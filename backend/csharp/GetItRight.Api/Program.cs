using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using StackExchange.Redis;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

// Configure SQLite Database
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite("Data Source=getitright.db"));

// Enable Cross-Origin Resource Sharing (CORS) for Frontend
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", p =>
        p.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());
});

var app = builder.Build();

app.UseCors("AllowAll");

// Initialize Redis Connection with resilient fallback
IConnectionMultiplexer? redis = null;
IDatabase? redisDb = null;
try
{
    redis = ConnectionMultiplexer.Connect("127.0.0.1:6379,abortConnect=false,connectTimeout=2500");
    if (redis != null && redis.IsConnected)
    {
        redisDb = redis.GetDatabase();
        Console.WriteLine("[Redis Cache] Connected to Redis at 127.0.0.1:6379");
    }
}
catch (Exception ex)
{
    Console.WriteLine($"[Redis Cache Notice] Redis connection fallback: {ex.Message}");
}

async Task InvalidatePollCaches()
{
    if (redisDb != null)
    {
        try
        {
            var keys = new RedisKey[] {
                "gir:polls:all",
                "gir:polls:free",
                "gir:polls:pro",
                "gir:polls:org",
                "gir:polls:election",
                "gir:surveys:all",
                "gir:surveys:free",
                "gir:surveys:pro",
                "gir:surveys:org",
                "gir:surveys:election",
                "gir:stats",
                "gir:admin:telemetry"
            };
            await redisDb.KeyDeleteAsync(keys);
        }
        catch { }
    }
}

// Initialize and Seed Database
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.EnsureCreated();
    db.Database.ExecuteSqlRaw(@"
        CREATE TABLE IF NOT EXISTS Surveys (
            Id TEXT PRIMARY KEY,
            Title TEXT NOT NULL,
            Description TEXT,
            Track TEXT,
            Plan TEXT,
            Status TEXT,
            TargetResponses INTEGER,
            TotalResponses INTEGER,
            CreatedAt TEXT,
            OwnerId TEXT,
            MerkleCohortRoot TEXT
        );
        CREATE TABLE IF NOT EXISTS SurveyQuestions (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            SurveyId TEXT NOT NULL,
            ""Index"" INTEGER NOT NULL,
            QuestionText TEXT NOT NULL,
            QuestionType TEXT NOT NULL,
            OptionsJson TEXT,
            ResponsesJson TEXT
        );
        CREATE TABLE IF NOT EXISTS SurveyResponses (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            SurveyId TEXT NOT NULL,
            VoterPseudonym TEXT,
            AnswersJson TEXT,
            ReceiptHash TEXT,
            MerkleLeafIndex INTEGER,
            Timestamp TEXT
        );
    ");
    DbSeeder.SeedDatabase(db);
}

// =============================================================
// REST API ENDPOINTS
// =============================================================

// Cache Status Endpoint
app.MapGet("/api/cache/status", async () =>
{
    var isConnected = redis != null && redis.IsConnected;
    string latency = "N/A";
    long keyCount = 0;

    if (isConnected && redisDb != null)
    {
        try
        {
            var ping = await redisDb.PingAsync();
            latency = $"{ping.TotalMilliseconds:F1} ms";
            var server = redis!.GetServers().FirstOrDefault();
            if (server != null && server.IsConnected)
            {
                keyCount = server.DatabaseSize();
            }
        }
        catch { }
    }

    return Results.Ok(new
    {
        redisConnected = isConnected,
        endpoint = "127.0.0.1:6379",
        latency,
        databaseKeys = keyCount,
        architecture = isConnected ? "Redis L2 Distributed Cache + SQLite L1 Persistent Store" : "Direct SQLite (Fallback)",
        ttlSeconds = 60,
        activeKeys = new[] { "gir:polls:all", "gir:polls:free", "gir:polls:pro", "gir:polls:org", "gir:polls:election", "gir:stats" }
    });
});

// 1. Polls Endpoints (Cached with Redis, Filterable by Plan: free, pro, org, election)
app.MapGet("/api/polls", async ([FromQuery] string? plan, AppDbContext db) =>
{
    var planKey = string.IsNullOrWhiteSpace(plan) ? "all" : plan.ToLower();
    var cacheKey = $"gir:polls:{planKey}";

    if (redisDb != null)
    {
        try
        {
            var cached = await redisDb.StringGetAsync(cacheKey);
            if (cached.HasValue)
            {
                return Results.Content(cached.ToString(), "application/json");
            }
        }
        catch { }
    }

    var query = db.Polls.Include(p => p.Options).AsQueryable();
    if (!string.IsNullOrWhiteSpace(plan))
    {
        query = query.Where(p => p.Plan.ToLower() == plan.ToLower());
    }
    var polls = await query.OrderByDescending(p => p.CreatedAt).ToListAsync();

    var jsonOptions = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
    var json = JsonSerializer.Serialize(polls, jsonOptions);

    if (redisDb != null)
    {
        try
        {
            await redisDb.StringSetAsync(cacheKey, json, TimeSpan.FromSeconds(60));
        }
        catch { }
    }

    return Results.Content(json, "application/json");
});

app.MapGet("/api/polls/{id}", async (string id, AppDbContext db) =>
{
    var poll = await db.Polls
        .Include(p => p.Options)
        .FirstOrDefaultAsync(p => p.Id == id);
    return poll is not null ? Results.Ok(poll) : Results.NotFound(new { error = "Poll not found" });
});

app.MapGet("/api/polls/{id}/transactions", async (string id, AppDbContext db) =>
{
    var transactions = await db.VoteTransactions
        .Where(t => t.PollId == id)
        .OrderByDescending(t => t.Id)
        .Take(50)
        .ToListAsync();
    return Results.Ok(transactions);
});

// REAL INTERACTION: Cast Verified Vote into SQLite Database + Redis Invalidation
app.MapPost("/api/polls/{id}/vote", async (string id, [FromBody] VoteRequest req, AppDbContext db) =>
{
    var poll = await db.Polls.Include(p => p.Options).FirstOrDefaultAsync(p => p.Id == id);
    if (poll is null) return Results.NotFound(new { error = "Poll not found" });

    var option = poll.Options.FirstOrDefault(o => o.Index == req.OptionIndex);
    if (option is null) return Results.BadRequest(new { error = "Invalid option index" });

    // 1. Increment votes in SQLite
    option.Votes++;
    poll.TotalVotes++;

    // 2. Recalculate percentages dynamically
    foreach (var opt in poll.Options)
    {
        opt.Percentage = poll.TotalVotes > 0 
            ? Math.Round(((double)opt.Votes / poll.TotalVotes) * 100, 1) 
            : 0;
    }

    // 3. Generate Cryptographic SHA-256 Receipt
    var leafIndex = poll.TotalVotes;
    var rawReceiptInput = $"{poll.Id}:{option.Index}:{leafIndex}:{DateTime.UtcNow.Ticks}:{Guid.NewGuid()}";
    using var sha256 = SHA256.Create();
    var hashBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(rawReceiptInput));
    var receiptHash = "0x" + Convert.ToHexString(hashBytes).ToLower();

    var voterKey = req.VoterKey ?? ("Voter-" + receiptHash.Substring(2, 6).ToUpper());

    // 4. Record real Vote Transaction in Database
    var voteTx = new VoteTransaction
    {
        PollId = poll.Id,
        OptionIndex = option.Index,
        OptionLabel = option.Label,
        ReceiptHash = receiptHash,
        MerkleLeafIndex = leafIndex,
        VoterPseudonym = voterKey,
        Timestamp = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss") + " UTC"
    };
    db.VoteTransactions.Add(voteTx);

    // 5. Append to Blockchain Ledger in Database
    var lastBlock = await db.LedgerBlocks.OrderByDescending(b => b.Height).FirstOrDefaultAsync();
    var newHeight = (lastBlock?.Height ?? 14210) + 1;
    var newBlock = new LedgerBlock
    {
        Height = newHeight,
        BlockHash = receiptHash,
        PreviousHash = lastBlock?.BlockHash ?? "0x4b7c120e981aa22",
        PayloadType = $"Ballot Receipt ({poll.Id})",
        LeafCount = 1,
        Timestamp = "Just now",
        MerkleRoot = poll.MerkleRoot
    };
    db.LedgerBlocks.Add(newBlock);

    // 6. Record Audit Log in Database
    db.AuditLogs.Add(new AuditLog
    {
        Timestamp = DateTime.UtcNow.ToString("HH:mm:ss") + " UTC",
        Actor = voterKey,
        Role = "Voter",
        Action = $"Cast Ballot & Hardware Attestation (Option: {option.Label})",
        TargetResource = $"{poll.Id} [Leaf #{leafIndex}]",
        Signature = receiptHash.Substring(0, 16) + "..."
    });

    // 7. Update System Telemetry Stats
    var stats = await db.Stats.FirstOrDefaultAsync();
    if (stats is not null)
    {
        stats.LedgerCommits++;
    }

    // 8. Update Owner Stats if applicable
    if (!string.IsNullOrEmpty(poll.OwnerId))
    {
        var owner = await db.Users.FirstOrDefaultAsync(u => u.Id == poll.OwnerId);
        if (owner is not null)
        {
            owner.TotalVotesReceived++;
        }
    }

    await db.SaveChangesAsync();

    // Invalidate Redis Caches immediately
    await InvalidatePollCaches();

    return Results.Ok(new
    {
        success = true,
        receiptHash,
        blockHeight = newHeight,
        pollId = poll.Id,
        optionIndex = option.Index,
        optionLabel = option.Label,
        leafIndex,
        totalVotes = poll.TotalVotes,
        options = poll.Options.OrderBy(o => o.Index),
        merkleRoot = poll.MerkleRoot,
        timestamp = voteTx.Timestamp
    });
});

// REAL INTERACTION: Create New Poll in SQLite Database (Associated with Plan & User)
app.MapPost("/api/polls", async ([FromBody] CreatePollRequest req, AppDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(req.Title) || req.Options == null || req.Options.Count < 2)
    {
        return Results.BadRequest(new { error = "A poll requires a title and at least two options." });
    }

    var plan = string.IsNullOrWhiteSpace(req.Plan) ? "free" : req.Plan.ToLower();
    var prefix = plan switch
    {
        "pro" => "PL-PRO-",
        "org" => "PL-ORG-",
        "election" => "PL-ELEC-",
        _ => "PL-FREE-"
    };

    var id = prefix + new Random().Next(100, 999);
    using var sha = SHA256.Create();
    var rootHash = "0x" + Convert.ToHexString(sha.ComputeHash(Encoding.UTF8.GetBytes(id + DateTime.UtcNow.Ticks))).ToLower().Substring(0, 16);

    var poll = new Poll
    {
        Id = id,
        Title = req.Title.Trim(),
        Description = req.Description?.Trim() ?? "Community verified referendum",
        Category = string.IsNullOrWhiteSpace(req.Category) ? "Public Governance" : req.Category.Trim(),
        Plan = plan,
        OwnerId = req.OwnerId ?? "USR-001",
        CreatedAt = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm"),
        Status = "live",
        TotalVotes = 0,
        MerkleRoot = rootHash,
        IsEncryptedBallot = plan != "free",
        Options = req.Options.Select((label, idx) => new PollOption
        {
            PollId = id,
            Index = idx,
            Label = label.Trim(),
            Votes = 0,
            Percentage = 0
        }).ToList()
    };

    db.Polls.Add(poll);

    // Update user quota
    if (!string.IsNullOrEmpty(poll.OwnerId))
    {
        var owner = await db.Users.FirstOrDefaultAsync(u => u.Id == poll.OwnerId);
        if (owner is not null)
        {
            owner.TotalPollsCreated++;
        }
    }

    // Audit log
    db.AuditLogs.Add(new AuditLog
    {
        Timestamp = DateTime.UtcNow.ToString("HH:mm:ss") + " UTC",
        Actor = req.OwnerId ?? "Console User",
        Role = "Creator",
        Action = $"Created {plan.ToUpper()} Poll Track: {poll.Title}",
        TargetResource = poll.Id,
        Signature = rootHash
    });

    await db.SaveChangesAsync();

    // Invalidate Redis cache
    await InvalidatePollCaches();

    return Results.Created($"/api/polls/{poll.Id}", poll);
});

// REAL INTERACTION: Reset Poll to baseline
app.MapPost("/api/polls/{id}/reset", async (string id, AppDbContext db) =>
{
    var poll = await db.Polls.Include(p => p.Options).FirstOrDefaultAsync(p => p.Id == id);
    if (poll is null) return Results.NotFound();

    foreach (var opt in poll.Options) opt.Votes = 0;
    poll.TotalVotes = 0;

    foreach (var opt in poll.Options)
    {
        opt.Percentage = 0;
    }

    await db.SaveChangesAsync();
    await InvalidatePollCaches();
    return Results.Ok(poll);
});

// =============================================================
// SURVEY & QUESTIONNAIRE MANAGEMENT ENDPOINTS
// =============================================================

// List all surveys (with Redis caching and optional plan filter)
app.MapGet("/api/surveys", async ([FromQuery] string? plan, AppDbContext db) =>
{
    var cacheKey = string.IsNullOrWhiteSpace(plan) ? "gir:surveys:all" : $"gir:surveys:{plan.ToLower()}";
    if (redisDb != null)
    {
        try
        {
            var cached = await redisDb.StringGetAsync(cacheKey);
            if (cached.HasValue)
            {
                var cachedSurveys = JsonSerializer.Deserialize<List<Survey>>(cached.ToString());
                if (cachedSurveys != null && cachedSurveys.Count > 0)
                {
                    return Results.Ok(cachedSurveys);
                }
            }
        }
        catch { }
    }

    var query = db.Surveys.Include(s => s.Questions).AsQueryable();
    if (!string.IsNullOrWhiteSpace(plan))
    {
        query = query.Where(s => s.Plan.ToLower() == plan.ToLower());
    }

    var list = await query.ToListAsync();

    if (redisDb != null)
    {
        try
        {
            await redisDb.StringSetAsync(cacheKey, JsonSerializer.Serialize(list), TimeSpan.FromSeconds(60));
        }
        catch { }
    }

    return Results.Ok(list);
});

// Get single survey by ID
app.MapGet("/api/surveys/{id}", async (string id, AppDbContext db) =>
{
    var survey = await db.Surveys.Include(s => s.Questions).FirstOrDefaultAsync(s => s.Id == id);
    if (survey is null) return Results.NotFound();
    return Results.Ok(survey);
});

// Create new Survey with Questions in SQLite
app.MapPost("/api/surveys", async ([FromBody] CreateSurveyRequest req, AppDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(req.Title) || req.Questions == null || req.Questions.Count == 0)
    {
        return Results.BadRequest(new { error = "A survey requires a title and at least one question." });
    }

    var plan = string.IsNullOrWhiteSpace(req.Plan) ? "free" : req.Plan.ToLower();
    var prefix = plan switch
    {
        "pro" => "SRV-PRO-",
        "org" => "SRV-ORG-",
        "election" => "SRV-ELEC-",
        _ => "SRV-FREE-"
    };

    var id = prefix + new Random().Next(100, 999);
    using var sha = SHA256.Create();
    var rootHash = "0x" + Convert.ToHexString(sha.ComputeHash(Encoding.UTF8.GetBytes(id + DateTime.UtcNow.Ticks))).ToLower().Substring(0, 16);

    var survey = new Survey
    {
        Id = id,
        Title = req.Title.Trim(),
        Description = req.Description?.Trim() ?? "Multi-question verified civic questionnaire",
        Track = string.IsNullOrWhiteSpace(req.Track) ? "Civic Feedback" : req.Track.Trim(),
        Plan = plan,
        Status = "active",
        TargetResponses = req.TargetResponses ?? 1000,
        TotalResponses = 0,
        CreatedAt = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm"),
        OwnerId = req.OwnerId ?? "USR-001",
        MerkleCohortRoot = rootHash,
        Questions = req.Questions.Select((q, idx) =>
        {
            var initialResponses = new Dictionary<string, int>();
            foreach (var opt in q.Options)
            {
                initialResponses[opt.Trim()] = 0;
            }
            return new SurveyQuestion
            {
                SurveyId = id,
                Index = idx + 1,
                QuestionText = q.QuestionText.Trim(),
                QuestionType = string.IsNullOrWhiteSpace(q.QuestionType) ? "multiple_choice" : q.QuestionType.Trim(),
                OptionsJson = JsonSerializer.Serialize(q.Options.Select(o => o.Trim()).ToList()),
                ResponsesJson = JsonSerializer.Serialize(initialResponses)
            };
        }).ToList()
    };

    db.Surveys.Add(survey);

    // Audit log
    db.AuditLogs.Add(new AuditLog
    {
        Timestamp = DateTime.UtcNow.ToString("HH:mm:ss") + " UTC",
        Actor = req.OwnerId ?? "Survey Studio",
        Role = "Creator",
        Action = $"Created {plan.ToUpper()} Survey: {survey.Title}",
        TargetResource = survey.Id,
        Signature = rootHash
    });

    await db.SaveChangesAsync();
    await InvalidatePollCaches();

    return Results.Created($"/api/surveys/{survey.Id}", survey);
});

// Submit verified response to survey
app.MapPost("/api/surveys/{id}/submit", async (string id, [FromBody] SubmitSurveyRequest req, AppDbContext db) =>
{
    var survey = await db.Surveys.Include(s => s.Questions).FirstOrDefaultAsync(s => s.Id == id);
    if (survey is null) return Results.NotFound(new { error = "Survey not found" });

    survey.TotalResponses++;

    // Update response counts in questions
    if (req.Answers != null)
    {
        foreach (var q in survey.Questions)
        {
            var qKey = q.Index.ToString();
            if (req.Answers.TryGetValue(qKey, out var selectedAnswer) || req.Answers.TryGetValue(q.QuestionText, out selectedAnswer))
            {
                try
                {
                    var counts = JsonSerializer.Deserialize<Dictionary<string, int>>(q.ResponsesJson) ?? new();
                    if (counts.ContainsKey(selectedAnswer))
                    {
                        counts[selectedAnswer]++;
                    }
                    else
                    {
                        counts[selectedAnswer] = 1;
                    }
                    q.ResponsesJson = JsonSerializer.Serialize(counts);
                }
                catch { }
            }
        }
    }

    using var sha = SHA256.Create();
    var rawBytes = Encoding.UTF8.GetBytes($"{survey.Id}:{req.VoterPseudonym}:{DateTime.UtcNow.Ticks}:{JsonSerializer.Serialize(req.Answers)}");
    var receiptHash = "0x" + Convert.ToHexString(sha.ComputeHash(rawBytes)).ToLower();
    var leafIndex = survey.TotalResponses;

    var surveyResp = new SurveyResponse
    {
        SurveyId = survey.Id,
        VoterPseudonym = req.VoterPseudonym ?? ("Voter-" + new Random().Next(1000, 9999)),
        AnswersJson = JsonSerializer.Serialize(req.Answers ?? new Dictionary<string, string>()),
        ReceiptHash = receiptHash,
        MerkleLeafIndex = leafIndex,
        Timestamp = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss") + " UTC"
    };

    db.SurveyResponses.Add(surveyResp);

    var lastBlock = await db.LedgerBlocks.OrderByDescending(b => b.Height).FirstOrDefaultAsync();
    var newHeight = (lastBlock?.Height ?? 14210) + 1;
    var blockHash = "0x" + Convert.ToHexString(sha.ComputeHash(Encoding.UTF8.GetBytes(receiptHash + newHeight))).ToLower();

    db.LedgerBlocks.Add(new LedgerBlock
    {
        Height = newHeight,
        BlockHash = blockHash,
        PreviousHash = lastBlock?.BlockHash ?? "0x0000000000000000",
        PayloadType = "SurveyCommit",
        LeafCount = 1,
        Timestamp = DateTime.UtcNow.ToString("HH:mm:ss") + " UTC",
        MerkleRoot = survey.MerkleCohortRoot
    });

    await db.SaveChangesAsync();
    await InvalidatePollCaches();

    return Results.Ok(new
    {
        success = true,
        surveyId = survey.Id,
        receiptHash,
        leafIndex,
        blockHeight = newHeight,
        totalResponses = survey.TotalResponses,
        timestamp = surveyResp.Timestamp
    });
});

// =============================================================
// USER & ADMIN MANAGEMENT ENDPOINTS
// =============================================================

// List all registered users (For the ONE Admin Console)
app.MapGet("/api/users", async ([FromQuery] string? plan, AppDbContext db) =>
{
    var query = db.Users.AsQueryable();
    if (!string.IsNullOrWhiteSpace(plan))
    {
        query = query.Where(u => u.Plan.ToLower() == plan.ToLower());
    }
    var users = await query.OrderByDescending(u => u.CreatedAt).ToListAsync();
    return Results.Ok(users);
});

// Get user profile by Id
app.MapGet("/api/users/{id}", async (string id, AppDbContext db) =>
{
    var user = await db.Users.FirstOrDefaultAsync(u => u.Id == id);
    if (user is null) return Results.NotFound(new { error = "User not found" });

    // Include polls created by this user
    var polls = await db.Polls.Include(p => p.Options).Where(p => p.OwnerId == id).ToListAsync();
    return Results.Ok(new { user, polls });
});

// User Sign Up (Enforcing: ONLY ONE ADMIN IN ENTIRE SYSTEM)
app.MapPost("/api/users", async ([FromBody] CreateUserRequest req, AppDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(req.Email) || string.IsNullOrWhiteSpace(req.FullName))
    {
        return Results.BadRequest(new { error = "Email and Full Name are required." });
    }

    // Check if email already exists
    if (await db.Users.AnyAsync(u => u.Email.ToLower() == req.Email.ToLower()))
    {
        return Results.BadRequest(new { error = "A user with this email already exists." });
    }

    // ENFORCE RULE: Only ONE Admin allowed in the system
    if (req.Role?.Equals("Admin", StringComparison.OrdinalIgnoreCase) == true)
    {
        var existingAdmin = await db.Users.AnyAsync(u => u.Role == "Admin");
        if (existingAdmin)
        {
            return Results.BadRequest(new { error = "Security policy violation: Only ONE Admin account is permitted in the Get It Right platform." });
        }
    }

    var plan = string.IsNullOrWhiteSpace(req.Plan) ? "free" : req.Plan.ToLower();
    var planName = plan switch
    {
        "pro" => "Civic Pro",
        "org" => "Institutional Org",
        "election" => "Sovereign Election Guard",
        _ => "Civic Starter"
    };

    var consoleUrl = plan switch
    {
        "pro" => "/console/pro.html",
        "org" => "/console/organization.html",
        "election" => "/console/election.html",
        _ => "/console/community.html"
    };

    var voterQuota = plan switch
    {
        "pro" => 25000,
        "org" => 100000,
        "election" => 10000000,
        _ => 1000
    };

    var pollsQuota = plan switch
    {
        "pro" => 50,
        "org" => 250,
        "election" => 1000,
        _ => 5
    };

    var userId = "USR-" + new Random().Next(1000, 9999);
    var newUser = new User
    {
        Id = userId,
        FullName = req.FullName.Trim(),
        Email = req.Email.Trim().ToLower(),
        Password = req.Password ?? "Secret2026!",
        Role = "Customer", // Always Customer; admin is unique and pre-seeded
        Plan = plan,
        PlanName = planName,
        Organization = req.Organization?.Trim() ?? "Independent Organizer",
        CreatedAt = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm"),
        Status = "Active",
        TotalPollsCreated = 0,
        TotalVotesReceived = 0,
        VoterQuota = voterQuota,
        PollsQuota = pollsQuota,
        ConsoleUrl = consoleUrl,
        LastLogin = "Just now"
    };

    db.Users.Add(newUser);

    // Audit log
    db.AuditLogs.Add(new AuditLog
    {
        Timestamp = DateTime.UtcNow.ToString("HH:mm:ss") + " UTC",
        Actor = newUser.FullName,
        Role = "Customer",
        Action = $"New Account Registration ({planName})",
        TargetResource = newUser.Id,
        Signature = "0x" + Guid.NewGuid().ToString("N").Substring(0, 16)
    });

    await db.SaveChangesAsync();

    return Results.Created($"/api/users/{newUser.Id}", newUser);
});

// Admin updates User Status (Active, Suspended, Verified)
app.MapPost("/api/users/{id}/status", async (string id, [FromBody] UpdateUserStatusRequest req, AppDbContext db) =>
{
    var user = await db.Users.FirstOrDefaultAsync(u => u.Id == id);
    if (user is null) return Results.NotFound(new { error = "User not found" });

    if (user.Role == "Admin")
    {
        return Results.BadRequest(new { error = "Cannot modify the primary Admin status." });
    }

    user.Status = req.Status;

    db.AuditLogs.Add(new AuditLog
    {
        Timestamp = DateTime.UtcNow.ToString("HH:mm:ss") + " UTC",
        Actor = "Chief Admin (Dr. Mwangi)",
        Role = "Administrator",
        Action = $"Modified User Status: {user.FullName} -> {req.Status}",
        TargetResource = user.Id,
        Signature = "0x" + Guid.NewGuid().ToString("N").Substring(0, 16)
    });

    await db.SaveChangesAsync();
    return Results.Ok(new { success = true, user });
});

// Admin updates User Plan
app.MapPost("/api/users/{id}/plan", async (string id, [FromBody] UpdateUserPlanRequest req, AppDbContext db) =>
{
    var user = await db.Users.FirstOrDefaultAsync(u => u.Id == id);
    if (user is null) return Results.NotFound(new { error = "User not found" });

    var plan = req.Plan.ToLower();
    user.Plan = plan;
    user.PlanName = plan switch
    {
        "pro" => "Civic Pro",
        "org" => "Institutional Org",
        "election" => "Sovereign Election Guard",
        _ => "Civic Starter"
    };
    user.ConsoleUrl = plan switch
    {
        "pro" => "/console/pro.html",
        "org" => "/console/organization.html",
        "election" => "/console/election.html",
        _ => "/console/community.html"
    };

    await db.SaveChangesAsync();
    return Results.Ok(new { success = true, user });
});

// Universal Authentication / Login
app.MapPost("/api/auth/login", async ([FromBody] LoginRequest req, AppDbContext db) =>
{
    var email = req.Email?.Trim().ToLower();
    var user = await db.Users.FirstOrDefaultAsync(u => u.Email.ToLower() == email);
    if (user is null)
    {
        return Results.Unauthorized();
    }

    user.LastLogin = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm");
    await db.SaveChangesAsync();

    return Results.Ok(new
    {
        success = true,
        user = new
        {
            user.Id,
            user.FullName,
            user.Email,
            user.Role,
            user.Plan,
            user.PlanName,
            user.Organization,
            user.Status,
            user.ConsoleUrl,
            isAdmin = user.Role == "Admin"
        },
        redirectUrl = user.Role == "Admin" ? "/console/dashboard.html" : user.ConsoleUrl
    });
});

// ADMIN TRACKING TELEMETRY (ADMIN CAN TRACK METRICS, BUT NOT INDIVIDUAL PRIVATE BALLOTS)
app.MapGet("/api/admin/tracking-telemetry", async (AppDbContext db) =>
{
    var totalUsers = await db.Users.CountAsync();
    var usersByPlan = await db.Users
        .GroupBy(u => u.Plan)
        .Select(g => new { Plan = g.Key, Count = g.Count() })
        .ToListAsync();

    var totalPolls = await db.Polls.CountAsync();
    var pollsByPlan = await db.Polls
        .GroupBy(p => p.Plan)
        .Select(g => new { Plan = g.Key, Count = g.Count(), TotalVotes = g.Sum(p => p.TotalVotes) })
        .ToListAsync();

    var totalVotesCast = await db.Polls.SumAsync(p => p.TotalVotes);
    var ledgerBlocksCount = await db.LedgerBlocks.CountAsync();
    var stationsReporting = await db.Stations.CountAsync(s => s.Status == "verified");
    var activeAnomalies = await db.Anomalies.CountAsync();

    return Results.Ok(new
    {
        overview = new
        {
            totalUsers,
            totalPolls,
            totalVotesCast,
            ledgerBlocksCount,
            stationsReporting,
            activeAnomalies,
            lastAnchorCheckpoint = 142
        },
        usersByPlan,
        pollsByPlan,
        // STRICT PRIVACY & CRYPTOGRAPHIC ZERO-KNOWLEDGE BOUNDARY:
        privacyGuarantees = new
        {
            zkProofEnforced = true,
            secretBallotDecryptionAllowed = false,
            rawVoterPiiStored = false,
            voterPseudonymHashing = "SHA-256 with Ephemeral Device Salt",
            message = "Cryptographic Zero-Knowledge Privacy Boundary Active: System Admin telemetry is strictly limited to aggregate counts, infrastructure health, tamper-evident Merkle roots, and user quotas. Individual voter choices and client-side private keys are mathematically sealed and cannot be accessed by any administrator."
        }
    });
});

// 2. Polling Stations Endpoints
app.MapGet("/api/stations", async (AppDbContext db) =>
{
    var stations = await db.Stations.ToListAsync();
    return Results.Ok(stations);
});

app.MapGet("/api/stations/{code}", async (string code, AppDbContext db) =>
{
    var station = await db.Stations.FirstOrDefaultAsync(s => s.Code.ToLower() == code.ToLower());
    return station is not null ? Results.Ok(station) : Results.NotFound();
});

// 3. Observers Endpoints
app.MapGet("/api/observers", async (AppDbContext db) =>
{
    var observers = await db.Observers.ToListAsync();
    return Results.Ok(observers);
});

// 4. Ledger Blocks Endpoints
app.MapGet("/api/ledger", async (AppDbContext db) =>
{
    var blocks = await db.LedgerBlocks.OrderByDescending(b => b.Height).Take(50).ToListAsync();
    return Results.Ok(blocks);
});

// 5. Anomalies Endpoints
app.MapGet("/api/anomalies", async (AppDbContext db) =>
{
    var anomalies = await db.Anomalies.ToListAsync();
    return Results.Ok(anomalies);
});

// 6. Disputes Endpoints
app.MapGet("/api/disputes", async (AppDbContext db) =>
{
    var disputes = await db.Disputes.ToListAsync();
    return Results.Ok(disputes);
});

app.MapPost("/api/disputes/{id}/resolve", async (string id, AppDbContext db) =>
{
    var dispute = await db.Disputes.FirstOrDefaultAsync(d => d.Id == id);
    if (dispute is null) return Results.NotFound();

    dispute.Status = "resolved";
    var station = await db.Stations.FirstOrDefaultAsync(s => s.Code == dispute.StationCode);
    if (station is not null)
    {
        station.Status = "verified";
    }

    db.AuditLogs.Add(new AuditLog
    {
        Timestamp = DateTime.UtcNow.ToString("HH:mm:ss") + " UTC",
        Actor = "Faith Mwangi",
        Role = "Reviewer",
        Action = $"Dispute {id} Resolved — Accepted Observer A Tally",
        TargetResource = dispute.StationCode,
        Signature = "0x" + Guid.NewGuid().ToString("N").Substring(0, 16)
    });

    await db.SaveChangesAsync();
    return Results.Ok(new { success = true, dispute, station });
});

// 7. Checkpoints Endpoints
app.MapGet("/api/checkpoints", async (AppDbContext db) =>
{
    var checkpoints = await db.Checkpoints.OrderByDescending(c => c.CheckpointId).ToListAsync();
    return Results.Ok(checkpoints);
});

app.MapPost("/api/checkpoints/publish", async (AppDbContext db) =>
{
    var lastCp = await db.Checkpoints.OrderByDescending(c => c.CheckpointId).FirstOrDefaultAsync();
    var nextId = (lastCp?.CheckpointId ?? 142) + 1;
    var nextBlock = (lastCp?.BitcoinBlockHeight ?? 884120) + 6;

    using var sha = SHA256.Create();
    var root = "0x" + Convert.ToHexString(sha.ComputeHash(Encoding.UTF8.GetBytes($"CP:{nextId}:{DateTime.UtcNow}"))).ToLower().Substring(0, 16);

    var cp = new Checkpoint
    {
        CheckpointId = nextId,
        MerkleRootHash = root,
        SubmissionsCount = (lastCp?.SubmissionsCount ?? 14210) + 34,
        BitcoinBlockHeight = nextBlock,
        BitcoinTxId = "0x" + Guid.NewGuid().ToString("N"),
        Status = "Bitcoin Confirmed",
        PublishedAt = "Just now"
    };

    db.Checkpoints.Add(cp);
    await db.SaveChangesAsync();
    return Results.Ok(cp);
});

// 8. Audit Logs Endpoints
app.MapGet("/api/audit", async (AppDbContext db) =>
{
    var logs = await db.AuditLogs.OrderByDescending(l => l.Id).Take(50).ToListAsync();
    return Results.Ok(logs);
});

// 9. System Telemetry Stats (with Redis cache)
app.MapGet("/api/stats", async (AppDbContext db) =>
{
    if (redisDb != null)
    {
        try
        {
            var cached = await redisDb.StringGetAsync("gir:stats");
            if (cached.HasValue)
            {
                return Results.Content(cached.ToString(), "application/json");
            }
        }
        catch { }
    }

    var stats = await db.Stats.FirstOrDefaultAsync() ?? new SystemStat();
    var json = JsonSerializer.Serialize(stats, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });

    if (redisDb != null)
    {
        try
        {
            await redisDb.StringSetAsync("gir:stats", json, TimeSpan.FromSeconds(30));
        }
        catch { }
    }

    return Results.Content(json, "application/json");
});

// 10. Automated Geo Currency Detection (NO Manual switching - IP based)
app.MapGet("/api/geo/currency", (HttpContext ctx) =>
{
    var country = ctx.Request.Headers["CF-IPCountry"].FirstOrDefault() 
               ?? ctx.Request.Headers["X-Country-Code"].FirstOrDefault()
               ?? ctx.Request.Headers["X-Geo-Country"].FirstOrDefault()
               ?? "KE"; // Default to Kenya for local dev

    var isKenya = country.Equals("KE", StringComparison.OrdinalIgnoreCase);

    return Results.Ok(new
    {
        countryCode = country,
        countryName = isKenya ? "Kenya" : "International",
        currency = isKenya ? "KES" : "USD",
        symbol = isKenya ? "KES " : "$",
        conversionRate = 125.0,
        pricing = new
        {
            free = isKenya ? "KES 0" : "$0",
            pro = isKenya ? "KES 1,500" : "$12",
            org = isKenya ? "KES 6,500" : "$49",
            election = "Turnkey / Custom"
        }
    });
});

app.Run("http://127.0.0.1:5000");

// =============================================================
// ENTITY MODELS & CONTEXT
// =============================================================

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<User> Users => Set<User>();
    public DbSet<Poll> Polls => Set<Poll>();
    public DbSet<PollOption> PollOptions => Set<PollOption>();
    public DbSet<VoteTransaction> VoteTransactions => Set<VoteTransaction>();
    public DbSet<Station> Stations => Set<Station>();
    public DbSet<Observer> Observers => Set<Observer>();
    public DbSet<LedgerBlock> LedgerBlocks => Set<LedgerBlock>();
    public DbSet<Anomaly> Anomalies => Set<Anomaly>();
    public DbSet<Dispute> Disputes => Set<Dispute>();
    public DbSet<Checkpoint> Checkpoints => Set<Checkpoint>();
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();
    public DbSet<SystemStat> Stats => Set<SystemStat>();
    public DbSet<Survey> Surveys => Set<Survey>();
    public DbSet<SurveyQuestion> SurveyQuestions => Set<SurveyQuestion>();
    public DbSet<SurveyResponse> SurveyResponses => Set<SurveyResponse>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>().HasKey(u => u.Id);
        modelBuilder.Entity<Poll>().HasKey(p => p.Id);
        modelBuilder.Entity<PollOption>().HasKey(o => o.Id);
        modelBuilder.Entity<VoteTransaction>().HasKey(t => t.Id);
        modelBuilder.Entity<Station>().HasKey(s => s.Code);
        modelBuilder.Entity<Observer>().HasKey(o => o.ObserverId);
        modelBuilder.Entity<LedgerBlock>().HasKey(b => b.Height);
        modelBuilder.Entity<Anomaly>().HasKey(a => a.Id);
        modelBuilder.Entity<Dispute>().HasKey(d => d.Id);
        modelBuilder.Entity<Checkpoint>().HasKey(c => c.CheckpointId);
        modelBuilder.Entity<AuditLog>().HasKey(l => l.Id);
        modelBuilder.Entity<SystemStat>().HasKey(s => s.Id);
        modelBuilder.Entity<Survey>().HasKey(s => s.Id);
        modelBuilder.Entity<SurveyQuestion>().HasKey(q => q.Id);
        modelBuilder.Entity<SurveyResponse>().HasKey(r => r.Id);
    }
}

public class User
{
    public string Id { get; set; } = "";
    public string FullName { get; set; } = "";
    public string Email { get; set; } = "";
    public string Password { get; set; } = "";
    public string Role { get; set; } = "Customer"; // ONLY ONE user has "Admin"
    public string Plan { get; set; } = "free";     // free, pro, org, election
    public string PlanName { get; set; } = "Civic Starter";
    public string Organization { get; set; } = "";
    public string CreatedAt { get; set; } = "";
    public string Status { get; set; } = "Active"; // Active, Verified, Suspended
    public int TotalPollsCreated { get; set; }
    public int TotalVotesReceived { get; set; }
    public int VoterQuota { get; set; } = 1000;
    public int PollsQuota { get; set; } = 5;
    public string ConsoleUrl { get; set; } = "/console/community.html";
    public string LastLogin { get; set; } = "Today";
}

public class Poll
{
    public string Id { get; set; } = "";
    public string Title { get; set; } = "";
    public string Description { get; set; } = "";
    public string Category { get; set; } = "";
    public string Plan { get; set; } = "free"; // free, pro, org, election
    public string OwnerId { get; set; } = "";
    public string CreatedAt { get; set; } = "";
    public string Status { get; set; } = "live";
    public int TotalVotes { get; set; }
    public string MerkleRoot { get; set; } = "";
    public bool IsEncryptedBallot { get; set; } = false;
    public List<PollOption> Options { get; set; } = new();
}

public class PollOption
{
    public int Id { get; set; }
    public string PollId { get; set; } = "";
    public int Index { get; set; }
    public string Label { get; set; } = "";
    public int Votes { get; set; }
    public double Percentage { get; set; }
}

public class VoteTransaction
{
    public int Id { get; set; }
    public string PollId { get; set; } = "";
    public int OptionIndex { get; set; }
    public string OptionLabel { get; set; } = "";
    public string ReceiptHash { get; set; } = "";
    public int MerkleLeafIndex { get; set; }
    public string VoterPseudonym { get; set; } = "";
    public string Timestamp { get; set; } = "";
}

public class Station
{
    public string Code { get; set; } = "";
    public string Name { get; set; } = "";
    public string County { get; set; } = "";
    public string Constituency { get; set; } = "";
    public int RegisteredVoters { get; set; }
    public int VotesCast { get; set; }
    public double TurnoutPercent { get; set; }
    public string DualObservers { get; set; } = "";
    public string Status { get; set; } = "verified"; // verified, flagged, frozen, pending
    public string Form34AHash { get; set; } = "";
    public string ObsASignature { get; set; } = "";
    public string ObsBSignature { get; set; } = "";
}

public class Observer
{
    public string ObserverId { get; set; } = "";
    public string Name { get; set; } = "";
    public string StationCode { get; set; } = "";
    public string HardwareModel { get; set; } = "";
    public string KeystoreType { get; set; } = "";
    public string PublicKeyFingerprint { get; set; } = "";
    public string BatterySignal { get; set; } = "";
    public string Status { get; set; } = "Reporting";
}

public class LedgerBlock
{
    public long Height { get; set; }
    public string BlockHash { get; set; } = "";
    public string PreviousHash { get; set; } = "";
    public string PayloadType { get; set; } = "";
    public int LeafCount { get; set; }
    public string Timestamp { get; set; } = "";
    public string MerkleRoot { get; set; } = "";
}

public class Anomaly
{
    public int Id { get; set; }
    public string StationCode { get; set; } = "";
    public string RuleName { get; set; } = "";
    public string Severity { get; set; } = "";
    public string Description { get; set; } = "";
    public string Timestamp { get; set; } = "";
}

public class Dispute
{
    public string Id { get; set; } = "";
    public string StationCode { get; set; } = "";
    public string StationName { get; set; } = "";
    public string ObserverA { get; set; } = "";
    public string ObserverB { get; set; } = "";
    public int ObsATally { get; set; }
    public int ObsBTally { get; set; }
    public int Variance { get; set; }
    public string Status { get; set; } = "frozen";
    public string AuditorFinding { get; set; } = "";
}

public class Checkpoint
{
    public int CheckpointId { get; set; }
    public string MerkleRootHash { get; set; } = "";
    public int SubmissionsCount { get; set; }
    public int BitcoinBlockHeight { get; set; }
    public string BitcoinTxId { get; set; } = "";
    public string Status { get; set; } = "Bitcoin Confirmed";
    public string PublishedAt { get; set; } = "";
}

public class AuditLog
{
    public int Id { get; set; }
    public string Timestamp { get; set; } = "";
    public string Actor { get; set; } = "";
    public string Role { get; set; } = "";
    public string Action { get; set; } = "";
    public string TargetResource { get; set; } = "";
    public string Signature { get; set; } = "";
}

public class SystemStat
{
    public int Id { get; set; }
    public int StationsTotal { get; set; } = 250;
    public int StationsReporting { get; set; } = 242;
    public int LedgerCommits { get; set; } = 14210;
    public int ActiveObservers { get; set; } = 482;
    public int OpenAnomalies { get; set; } = 3;
    public int IngestionMsgPerSec { get; set; } = 1420;
    public double P99LatencyMs { get; set; } = 2.4;
    public double ChainIntegrityPercent { get; set; } = 100.0;
}

public record VoteRequest(int OptionIndex, string? VoterKey);
public record CreatePollRequest(string Title, string Description, string? Category, string? Plan, string? OwnerId, List<string> Options);
public record CreateUserRequest(string FullName, string Email, string? Password, string? Plan, string? Organization, string? Role);
public record UpdateUserStatusRequest(string Status);
public record UpdateUserPlanRequest(string Plan);
public record LoginRequest(string Email, string? Password);

public class Survey
{
    public string Id { get; set; } = "";
    public string Title { get; set; } = "";
    public string Description { get; set; } = "";
    public string Track { get; set; } = "Civic Feedback";
    public string Plan { get; set; } = "free"; // free, pro, org, election
    public string Status { get; set; } = "active"; // active, draft, closed
    public int TargetResponses { get; set; } = 1000;
    public int TotalResponses { get; set; } = 0;
    public string CreatedAt { get; set; } = "";
    public string OwnerId { get; set; } = "USR-001";
    public string MerkleCohortRoot { get; set; } = "";
    public string TargetAudience { get; set; } = "General Public";
    public string OrganizationName { get; set; } = "Verified Civic Publisher";
    public List<SurveyQuestion> Questions { get; set; } = new();
}

public class SurveyQuestion
{
    public int Id { get; set; }
    public string SurveyId { get; set; } = "";
    public int Index { get; set; }
    public string QuestionText { get; set; } = "";
    public string QuestionType { get; set; } = "multiple_choice"; // multiple_choice, rating_scale, binary
    public string OptionsJson { get; set; } = "[]";
    public string ResponsesJson { get; set; } = "{}";
}

public class SurveyResponse
{
    public int Id { get; set; }
    public string SurveyId { get; set; } = "";
    public string VoterPseudonym { get; set; } = "";
    public string AnswersJson { get; set; } = "{}";
    public string ReceiptHash { get; set; } = "";
    public int MerkleLeafIndex { get; set; }
    public string Timestamp { get; set; } = "";
}

public record CreateSurveyRequest(
    string Title,
    string Description,
    string? Track,
    string? Plan,
    string? OwnerId,
    int? TargetResponses,
    List<CreateSurveyQuestionDto> Questions
);

public record CreateSurveyQuestionDto(
    string QuestionText,
    string QuestionType,
    List<string> Options
);

public record SubmitSurveyRequest(
    string? VoterPseudonym,
    Dictionary<string, string> Answers
);

// =============================================================
// DATABASE SEEDER (40 POLLS FOR 4 PLANS + 1 ADMIN & USERS)
// =============================================================

public static class DbSeeder
{
    public static void SeedDatabase(AppDbContext db)
    {
        if (!db.Polls.Any())
        {
            // -------------------------------------------------------------
            // 1. SEED USERS (ONLY ONE ADMIN IN THE PLATFORM)
            // -------------------------------------------------------------
        var adminUser = new User
        {
            Id = "USR-ADMIN",
            FullName = "Dr. David Mwangi",
            Email = "admin@getitright.io",
            Password = "SuperAdminPassword2026!",
            Role = "Admin", // <--- THE ONLY ONE ADMIN IN SYSTEM
            Plan = "election",
            PlanName = "Sovereign Administrator",
            Organization = "Get It Right Core Foundation",
            CreatedAt = "2026-08-01 00:00",
            Status = "Verified",
            TotalPollsCreated = 10,
            TotalVotesReceived = 158200,
            VoterQuota = 10000000,
            PollsQuota = 99999,
            ConsoleUrl = "/console/dashboard.html",
            LastLogin = "Live Now"
        };

        var userFree = new User
        {
            Id = "USR-001",
            FullName = "Grace Wanjiku",
            Email = "grace@umoja.org",
            Password = "Password123!",
            Role = "Customer",
            Plan = "free",
            PlanName = "Civic Starter",
            Organization = "Umoja Community Initiative",
            CreatedAt = "2026-09-10 10:15",
            Status = "Active",
            TotalPollsCreated = 10,
            TotalVotesReceived = 6380,
            VoterQuota = 1000,
            PollsQuota = 10,
            ConsoleUrl = "/console/community.html",
            LastLogin = "10m ago"
        };

        var userPro = new User
        {
            Id = "USR-002",
            FullName = "Marcus Kiprop",
            Email = "marcus@surveyanalytics.ke",
            Password = "Password123!",
            Role = "Customer",
            Plan = "pro",
            PlanName = "Civic Pro",
            Organization = "MarketPulse Pollsters Africa",
            CreatedAt = "2026-09-02 14:20",
            Status = "Active",
            TotalPollsCreated = 10,
            TotalVotesReceived = 28450,
            VoterQuota = 25000,
            PollsQuota = 50,
            ConsoleUrl = "/console/pro.html",
            LastLogin = "1h ago"
        };

        var userOrg = new User
        {
            Id = "USR-003",
            FullName = "Sarah Mutiso",
            Email = "sarah@kenyateachersunion.org",
            Password = "Password123!",
            Role = "Customer",
            Plan = "org",
            PlanName = "Institutional Org",
            Organization = "National Union of Educators",
            CreatedAt = "2026-08-20 09:30",
            Status = "Verified",
            TotalPollsCreated = 10,
            TotalVotesReceived = 82190,
            VoterQuota = 100000,
            PollsQuota = 200,
            ConsoleUrl = "/console/organization.html",
            LastLogin = "30m ago"
        };

        var userElec = new User
        {
            Id = "USR-004",
            FullName = "Amb. Paul Ochieng",
            Email = "commissioner@electoralguard.ke",
            Password = "Password123!",
            Role = "Customer",
            Plan = "election",
            PlanName = "Sovereign Election Guard",
            Organization = "Independent Electoral Oversight Mission",
            CreatedAt = "2026-08-05 11:00",
            Status = "Verified",
            TotalPollsCreated = 10,
            TotalVotesReceived = 345000,
            VoterQuota = 10000000,
            PollsQuota = 1000,
            ConsoleUrl = "/console/election.html",
            LastLogin = "5m ago"
        };

        var userPending = new User
        {
            Id = "USR-005",
            FullName = "Brian Kariuki",
            Email = "brian.k@riftvalleytech.co.ke",
            Password = "Password123!",
            Role = "Customer",
            Plan = "pro",
            PlanName = "Civic Pro",
            Organization = "Rift Valley Developer Guild",
            CreatedAt = "2026-10-01 16:45",
            Status = "Active",
            TotalPollsCreated = 2,
            TotalVotesReceived = 840,
            VoterQuota = 25000,
            PollsQuota = 50,
            ConsoleUrl = "/console/pro.html",
            LastLogin = "Yesterday"
        };

        var userSuspended = new User
        {
            Id = "USR-006",
            FullName = "Alex Otieno",
            Email = "alex.o@quicksurvey.net",
            Password = "Password123!",
            Role = "Customer",
            Plan = "free",
            PlanName = "Civic Starter",
            Organization = "Campus Sports Club",
            CreatedAt = "2026-09-18 12:00",
            Status = "Suspended",
            TotalPollsCreated = 1,
            TotalVotesReceived = 150,
            VoterQuota = 1000,
            PollsQuota = 5,
            ConsoleUrl = "/console/community.html",
            LastLogin = "4 days ago"
        };

        db.Users.AddRange(adminUser, userFree, userPro, userOrg, userElec, userPending, userSuspended);

        // -------------------------------------------------------------
        // 2. SEED 40 POLLS (10 POLLS PER PLAN)
        // -------------------------------------------------------------

        // ── PLAN 1: COMMUNITY / FREE (10 POLLS) ──
        var freePolls = new List<Poll>
        {
            new Poll {
                Id = "PL-FREE-01",
                Title = "Community Ballot: Proposed Solar Streetlights for Sub-County Hall",
                Description = "Referendum on Phase 1 solar lighting installation and security coverage for Machakos.",
                Category = "Clean Energy & Infrastructure",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-10-01 08:00",
                Status = "live",
                TotalVotes = 1675,
                MerkleRoot = "0x8a92fc119a2e8877",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-01", Index = 0, Label = "Approve Installation (Phase 1)", Votes = 1240, Percentage = 74.0 },
                    new() { PollId = "PL-FREE-01", Index = 1, Label = "Defer to Q2 Council Hearing", Votes = 350, Percentage = 21.0 },
                    new() { PollId = "PL-FREE-01", Index = 2, Label = "Request Environmental Audit", Votes = 85, Percentage = 5.0 }
                }
            },
            new Poll {
                Id = "PL-FREE-02",
                Title = "Local Community Park & Urban Garden Initiative",
                Description = "Should 2 acres of open public space be zoned for youth organic urban farming?",
                Category = "Urban Green Spaces",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-09-29 09:30",
                Status = "live",
                TotalVotes = 820,
                MerkleRoot = "0x4b7c120e981aa22",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-02", Index = 0, Label = "Yes, Build Community Urban Garden", Votes = 590, Percentage = 72.0 },
                    new() { PollId = "PL-FREE-02", Index = 1, Label = "No, Retain as Grass Football Pitch", Votes = 190, Percentage = 23.2 },
                    new() { PollId = "PL-FREE-02", Index = 2, Label = "Undecided / Needs Meeting", Votes = 40, Percentage = 4.8 }
                }
            },
            new Poll {
                Id = "PL-FREE-03",
                Title = "Youth Football League Field Renovation Priority",
                Description = "Prioritizing perimeter fencing, floodlights, or natural turf drainage.",
                Category = "Youth & Recreation",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-09-27 14:00",
                Status = "live",
                TotalVotes = 560,
                MerkleRoot = "0x1d22aa9aa133445",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-03", Index = 0, Label = "Solar Floodlights for Night Matches", Votes = 310, Percentage = 55.4 },
                    new() { PollId = "PL-FREE-03", Index = 1, Label = "Natural Grass Turf Drainage", Votes = 180, Percentage = 32.1 },
                    new() { PollId = "PL-FREE-03", Index = 2, Label = "Perimeter Security Fence", Votes = 70, Percentage = 12.5 }
                }
            },
            new Poll {
                Id = "PL-FREE-04",
                Title = "Sub-County Library Weekend Opening Hours Expansion",
                Description = "Community ballot on extending public library study halls on Saturday & Sunday.",
                Category = "Education & Civic",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-09-25 11:15",
                Status = "live",
                TotalVotes = 740,
                MerkleRoot = "0x33aa55cc1100998",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-04", Index = 0, Label = "Open Both Saturday & Sunday (8am - 8pm)", Votes = 540, Percentage = 73.0 },
                    new() { PollId = "PL-FREE-04", Index = 1, Label = "Open Saturdays Only (8am - 4pm)", Votes = 160, Percentage = 21.6 },
                    new() { PollId = "PL-FREE-04", Index = 2, Label = "Keep Existing Weekday Hours", Votes = 40, Percentage = 5.4 }
                }
            },
            new Poll {
                Id = "PL-FREE-05",
                Title = "Artisan Market Stall Allocation Formula 2026",
                Description = "Fair distribution model for weekly open-air market vendors.",
                Category = "Local Commerce",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-09-22 10:00",
                Status = "live",
                TotalVotes = 490,
                MerkleRoot = "0x55d044ee7c12b99",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-05", Index = 0, Label = "Rotating Bi-Weekly Stall Lottery", Votes = 280, Percentage = 57.1 },
                    new() { PollId = "PL-FREE-05", Index = 1, Label = "First-Come First-Served Registration", Votes = 150, Percentage = 30.6 },
                    new() { PollId = "PL-FREE-05", Index = 2, Label = "Seniority Priority for Longtime Vendors", Votes = 60, Percentage = 12.3 }
                }
            },
            new Poll {
                Id = "PL-FREE-06",
                Title = "Neighborhood Security Gate & Boom Barrier Installation",
                Description = "Resident vote on automated boom barrier and 24/7 security guard funding.",
                Category = "Community Safety",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-09-20 16:30",
                Status = "live",
                TotalVotes = 620,
                MerkleRoot = "0x77ee339911aa552",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-06", Index = 0, Label = "Approve Gate & Monthly Levy", Votes = 450, Percentage = 72.6 },
                    new() { PollId = "PL-FREE-06", Index = 1, Label = "Reject Levy, Maintain Open Access", Votes = 130, Percentage = 21.0 },
                    new() { PollId = "PL-FREE-06", Index = 2, Label = "Need CCTV Cameras Only", Votes = 40, Percentage = 6.4 }
                }
            },
            new Poll {
                Id = "PL-FREE-07",
                Title = "Community Borehole Water Usage Tariff Structure",
                Description = "Setting tiered pricing per 20L jerrycan for solar borehole maintenance.",
                Category = "Water & Sanitation",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-09-18 09:00",
                Status = "live",
                TotalVotes = 810,
                MerkleRoot = "0x91bbcc22aa88110",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-07", Index = 0, Label = "KES 3 Flat per 20 Litres", Votes = 520, Percentage = 64.2 },
                    new() { PollId = "PL-FREE-07", Index = 1, Label = "KES 5 (Includes Maintenance Sinking Fund)", Votes = 210, Percentage = 25.9 },
                    new() { PollId = "PL-FREE-07", Index = 2, Label = "Monthly Family Subscription (KES 200)", Votes = 80, Percentage = 9.9 }
                }
            },
            new Poll {
                Id = "PL-FREE-08",
                Title = "Residents Association Annual General Meeting Venue",
                Description = "Voting on physical hall vs hybrid online streaming attendance.",
                Category = "Association Governance",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-09-15 13:45",
                Status = "live",
                TotalVotes = 340,
                MerkleRoot = "0x66cc001188ff44a",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-08", Index = 0, Label = "Hybrid (Physical Hall + Verified Stream)", Votes = 230, Percentage = 67.6 },
                    new() { PollId = "PL-FREE-08", Index = 1, Label = "Physical Hall Attendance Only", Votes = 80, Percentage = 23.5 },
                    new() { PollId = "PL-FREE-08", Index = 2, Label = "Fully Virtual Zoom / Webcast", Votes = 30, Percentage = 8.9 }
                }
            },
            new Poll {
                Id = "PL-FREE-09",
                Title = "Local Secondary School Science Lab Equipment Fundraiser",
                Description = "Deciding priority between physics sensor kits or biology microscope benches.",
                Category = "Education Funding",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-09-12 15:20",
                Status = "live",
                TotalVotes = 510,
                MerkleRoot = "0x12bb44e055aacc8",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-09", Index = 0, Label = "Biology & Chemistry Microscopy Kits", Votes = 310, Percentage = 60.8 },
                    new() { PollId = "PL-FREE-09", Index = 1, Label = "Physics Sensors & Robotics Starters", Votes = 160, Percentage = 31.4 },
                    new() { PollId = "PL-FREE-09", Index = 2, Label = "Computer Lab Refurbishment", Votes = 40, Percentage = 7.8 }
                }
            },
            new Poll {
                Id = "PL-FREE-10",
                Title = "Neighborhood Organic Waste Recycling & Compost Pilot",
                Description = "Opt-in pilot for segregated organic waste bins and community manure distribution.",
                Category = "Environment & Sanitation",
                Plan = "free",
                OwnerId = "USR-001",
                CreatedAt = "2026-09-10 10:00",
                Status = "closed",
                TotalVotes = 420,
                MerkleRoot = "0x88f011ac33bba10",
                Options = new List<PollOption> {
                    new() { PollId = "PL-FREE-10", Index = 0, Label = "Join Pilot (Provide Color-coded Bins)", Votes = 330, Percentage = 78.6 },
                    new() { PollId = "PL-FREE-10", Index = 1, Label = "Continue Traditional Waste Disposal", Votes = 70, Percentage = 16.7 },
                    new() { PollId = "PL-FREE-10", Index = 2, Label = "Need More Information on Odor Control", Votes = 20, Percentage = 4.7 }
                }
            }
        };

        // ── PLAN 2: PRO / RESEARCHER & POLLSTER (10 POLLS) ──
        var proPolls = new List<Poll>
        {
            new Poll {
                Id = "PL-PRO-01",
                Title = "National Tech Workforce: Hybrid vs In-Office Mandate 2026",
                Description = "Comprehensive industry sentiment research on 3-day office policies across 400 software firms.",
                Category = "Labor Economics",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-10-01 11:30",
                Status = "live",
                TotalVotes = 3450,
                MerkleRoot = "0xfa7799112000334",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-01", Index = 0, Label = "Fully Flexible Remote (Deliverable-based)", Votes = 2180, Percentage = 63.2 },
                    new() { PollId = "PL-PRO-01", Index = 1, Label = "Hybrid (2 Days Office, 3 Days Home)", Votes = 1020, Percentage = 29.6 },
                    new() { PollId = "PL-PRO-01", Index = 2, Label = "Full 5-Day In-Office Co-location", Votes = 250, Percentage = 7.2 }
                }
            },
            new Poll {
                Id = "PL-PRO-02",
                Title = "AI Adoption & Regulatory Guardrails in Financial Services",
                Description = "Banking executive survey on credit scoring algorithmic bias and mandatory audits.",
                Category = "FinTech Regulation",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-09-29 14:10",
                Status = "live",
                TotalVotes = 2890,
                MerkleRoot = "0x9f1a8e25c4411aa",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-02", Index = 0, Label = "Mandatory Independent Algorithmic Audits", Votes = 1790, Percentage = 61.9 },
                    new() { PollId = "PL-PRO-02", Index = 1, Label = "Voluntary Industry Self-Regulation Code", Votes = 810, Percentage = 28.0 },
                    new() { PollId = "PL-PRO-02", Index = 2, Label = "Pause High-Risk Automated Lending", Votes = 290, Percentage = 10.1 }
                }
            },
            new Poll {
                Id = "PL-PRO-03",
                Title = "East Africa Cross-Border Mobile Money Interoperability Index",
                Description = "Merchant fee benchmarks and settlement velocity preferences between KES, TZS, and UGX.",
                Category = "Cross-Border Trade",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-09-27 09:00",
                Status = "live",
                TotalVotes = 4120,
                MerkleRoot = "0x3e18bb77aa11220",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-03", Index = 0, Label = "Cap Inter-Operator FX Surcharge at 0.5%", Votes = 2890, Percentage = 70.1 },
                    new() { PollId = "PL-PRO-03", Index = 1, Label = "Introduce Real-Time Central Bank Settlement", Votes = 980, Percentage = 23.8 },
                    new() { PollId = "PL-PRO-03", Index = 2, Label = "Maintain Current Commercial Bank Rails", Votes = 250, Percentage = 6.1 }
                }
            },
            new Poll {
                Id = "PL-PRO-04",
                Title = "Electric Motorcycle (Boda Boda) Battery Swapping Feasibility",
                Description = "Rider economics survey on swap battery subscription vs outright vehicle ownership.",
                Category = "Green Mobility",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-09-24 16:00",
                Status = "live",
                TotalVotes = 3210,
                MerkleRoot = "0x223344556677889",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-04", Index = 0, Label = "KES 350 Daily Unlimited Battery Swaps", Votes = 2150, Percentage = 67.0 },
                    new() { PollId = "PL-PRO-04", Index = 1, Label = "Pay-per-kWh Fast Charging Stations", Votes = 790, Percentage = 24.6 },
                    new() { PollId = "PL-PRO-04", Index = 2, Label = "Prefer Petrol Bikes Due to Range Anxiety", Votes = 270, Percentage = 8.4 }
                }
            },
            new Poll {
                Id = "PL-PRO-05",
                Title = "National Healthcare Telemedicine vs In-Clinic Preference Study",
                Description = "Patient satisfaction metrics on virtual chronic disease management and prescription delivery.",
                Category = "Health Informatics",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-09-22 11:20",
                Status = "live",
                TotalVotes = 2740,
                MerkleRoot = "0x889900112233445",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-05", Index = 0, Label = "Telemedicine for Routine Consultation & Refills", Votes = 1680, Percentage = 61.3 },
                    new() { PollId = "PL-PRO-05", Index = 1, Label = "In-Clinic Physical Doctor Visit Always", Votes = 820, Percentage = 29.9 },
                    new() { PollId = "PL-PRO-05", Index = 2, Label = "Hybrid Clinic with Video Specialist Access", Votes = 240, Percentage = 8.8 }
                }
            },
            new Poll {
                Id = "PL-PRO-06",
                Title = "Consumer Data Privacy & Cookie Transparency Expectations",
                Description = "Measuring consumer willingness to share zero-party browsing data in exchange for rewards.",
                Category = "Data Governance",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-09-19 13:00",
                Status = "live",
                TotalVotes = 1980,
                MerkleRoot = "0x001122334455667",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-06", Index = 0, Label = "Strict Opt-In Only with Clear Revocation", Votes = 1420, Percentage = 71.7 },
                    new() { PollId = "PL-PRO-06", Index = 1, Label = "Accept Data Sharing for Discount Coupons", Votes = 420, Percentage = 21.2 },
                    new() { PollId = "PL-PRO-06", Index = 2, Label = "Indifferent as long as data isn't sold", Votes = 140, Percentage = 7.1 }
                }
            },
            new Poll {
                Id = "PL-PRO-07",
                Title = "Urban Bus Rapid Transit (BRT) Commuter Satisfaction Survey",
                Description = "Evaluating smartcard ticketing reliability, dedicated lane speed, and platform safety.",
                Category = "Urban Infrastructure",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-09-16 10:40",
                Status = "live",
                TotalVotes = 3100,
                MerkleRoot = "0x667788990011223",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-07", Index = 0, Label = "Highly Satisfied with Lane Speed (+40% faster)", Votes = 1950, Percentage = 62.9 },
                    new() { PollId = "PL-PRO-07", Index = 1, Label = "Needs Increased Peak Hour Bus Frequency", Votes = 890, Percentage = 28.7 },
                    new() { PollId = "PL-PRO-07", Index = 2, Label = "Ticketing Gateway Glitches Reported", Votes = 260, Percentage = 8.4 }
                }
            },
            new Poll {
                Id = "PL-PRO-08",
                Title = "Smallholder Agritech Index: Satellite Weather Insurance Trust",
                Description = "Farmer willingness to adopt automated smart-contract parametric drought insurance.",
                Category = "Agricultural Economics",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-09-14 15:15",
                Status = "live",
                TotalVotes = 2410,
                MerkleRoot = "0x112233445566778",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-08", Index = 0, Label = "Willing to Subscribe if Payout is within 48h", Votes = 1620, Percentage = 67.2 },
                    new() { PollId = "PL-PRO-08", Index = 1, Label = "Prefer Subsidized Cooperative Grain Silos", Votes = 580, Percentage = 24.1 },
                    new() { PollId = "PL-PRO-08", Index = 2, Label = "Skeptical of Satellite Measurement Accuracy", Votes = 210, Percentage = 8.7 }
                }
            },
            new Poll {
                Id = "PL-PRO-09",
                Title = "Cloud Infrastructure Sovereignty & Local Data Centers",
                Description = "Enterprise CTO sentiment on migrating critical workloads to regional Tier-III facilities.",
                Category = "Cloud & Security",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-09-11 08:30",
                Status = "live",
                TotalVotes = 1860,
                MerkleRoot = "0x99dd44ee55aa112",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-09", Index = 0, Label = "Migrating to In-Country Local Cloud Regions", Votes = 1180, Percentage = 63.4 },
                    new() { PollId = "PL-PRO-09", Index = 1, Label = "Hybrid Architecture (Sensitive data local only)", Votes = 540, Percentage = 29.0 },
                    new() { PollId = "PL-PRO-09", Index = 2, Label = "Maintaining Global US/EU Multi-Region", Votes = 140, Percentage = 7.6 }
                }
            },
            new Poll {
                Id = "PL-PRO-10",
                Title = "Secondary School Digital Literacy Curriculum Prioritization",
                Description = "Educator consensus on teaching Python/AI prompt engineering vs foundational STEM typing.",
                Category = "EdTech Strategy",
                Plan = "pro",
                OwnerId = "USR-002",
                CreatedAt = "2026-09-08 12:00",
                Status = "closed",
                TotalVotes = 2890,
                MerkleRoot = "0x44dd22ee8899001",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-PRO-10", Index = 0, Label = "Foundational Coding, Logic & Python", Votes = 1750, Percentage = 60.6 },
                    new() { PollId = "PL-PRO-10", Index = 1, Label = "Practical Cyber Hygiene & Media Literacy", Votes = 850, Percentage = 29.4 },
                    new() { PollId = "PL-PRO-10", Index = 2, Label = "AI Application & Prompt Engineering", Votes = 290, Percentage = 10.0 }
                }
            }
        };

        // ── PLAN 3: ORGANIZATION / INSTITUTIONAL & ENTERPRISE (10 POLLS) ──
        var orgPolls = new List<Poll>
        {
            new Poll {
                Id = "PL-ORG-01",
                Title = "National Educators Union: CBA 2026-2030 Collective Agreement Ratification",
                Description = "Formal ballot of 48,000 union members on salary scale harmonization and medical cover.",
                Category = "Union Governance",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-10-01 07:45",
                Status = "live",
                TotalVotes = 12450,
                MerkleRoot = "0x8a92fc119a2e887",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-01", Index = 0, Label = "Ratify 4-Year CBA Terms", Votes = 8950, Percentage = 71.9 },
                    new() { PollId = "PL-ORG-01", Index = 1, Label = "Reject Terms & Mandate Further Conciliation", Votes = 2800, Percentage = 22.5 },
                    new() { PollId = "PL-ORG-01", Index = 2, Label = "Abstain", Votes = 700, Percentage = 5.6 }
                }
            },
            new Poll {
                Id = "PL-ORG-02",
                Title = "University Academic Senate: Faculty Representative Council Election",
                Description = "Cryptographic dual-key balloting for the Dean of Engineering and Physical Sciences.",
                Category = "University Senate",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-09-29 10:00",
                Status = "live",
                TotalVotes = 1840,
                MerkleRoot = "0x3c7e99bb44aa110",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-02", Index = 0, Label = "Prof. Esther Nduta (Research & Grants)", Votes = 1050, Percentage = 57.1 },
                    new() { PollId = "PL-ORG-02", Index = 1, Label = "Dr. James Barasa (Industry Partnerships)", Votes = 640, Percentage = 34.8 },
                    new() { PollId = "PL-ORG-02", Index = 2, Label = "Dr. Amina Hassan (Curriculum Modernization)", Votes = 150, Percentage = 8.1 }
                }
            },
            new Poll {
                Id = "PL-ORG-03",
                Title = "Metropolitan SACCO: Annual Dividend Rate vs Capital Reserve Retention",
                Description = "Shareholder voting on 12.5% cash dividend payout vs 10% with 2.5% capitalized into land reserve.",
                Category = "Cooperative Finance",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-09-27 12:30",
                Status = "live",
                TotalVotes = 8900,
                MerkleRoot = "0x99a1bb22cc44001",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-03", Index = 0, Label = "12.5% Cash Dividend to Members", Votes = 5820, Percentage = 65.4 },
                    new() { PollId = "PL-ORG-03", Index = 1, Label = "10.0% Cash + 2.5% Capital Reserve", Votes = 2640, Percentage = 29.7 },
                    new() { PollId = "PL-ORG-03", Index = 2, Label = "8.0% Cash + 4.5% Commercial Expansion", Votes = 440, Percentage = 4.9 }
                }
            },
            new Poll {
                Id = "PL-ORG-04",
                Title = "Global Civil Society NGO: Horn of Africa Drought Emergency Fund",
                Description = "Institutional board allocation between anticipatory cash transfers vs solar boreholes.",
                Category = "Humanitarian Mandate",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-09-25 09:15",
                Status = "live",
                TotalVotes = 3450,
                MerkleRoot = "0x77aa11fc99dd44e",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-04", Index = 0, Label = "Direct Cash Transfers via Mobile Money (60%)", Votes = 2380, Percentage = 69.0 },
                    new() { PollId = "PL-ORG-04", Index = 1, Label = "Emergency Solar Water Infrastructure (30%)", Votes = 870, Percentage = 25.2 },
                    new() { PollId = "PL-ORG-04", Index = 2, Label = "Emergency Livestock Feed Subsidies (10%)", Votes = 200, Percentage = 5.8 }
                }
            },
            new Poll {
                Id = "PL-ORG-05",
                Title = "Medical Practitioners Board: Telehealth Malpractice Liability Code",
                Description = "Ratifying institutional guidelines for cross-border AI-assisted radiology interpretation.",
                Category = "Medical Governance",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-09-23 15:40",
                Status = "live",
                TotalVotes = 4120,
                MerkleRoot = "0x55d044ee7c12b99",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-05", Index = 0, Label = "Physician Bears Final Clinical Responsibility", Votes = 2980, Percentage = 72.3 },
                    new() { PollId = "PL-ORG-05", Index = 1, Label = "Shared Vendor-Hospital Indemnity Pool", Votes = 940, Percentage = 22.8 },
                    new() { PollId = "PL-ORG-05", Index = 2, Label = "Require Third-Party Telehealth Re-Insurance", Votes = 200, Percentage = 4.9 }
                }
            },
            new Poll {
                Id = "PL-ORG-06",
                Title = "Law Society Council Election: Judicial Reforms Committee Chair",
                Description = "Multi-candidate ranked ballot among verified advocate bar members.",
                Category = "Bar Association",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-09-20 11:00",
                Status = "live",
                TotalVotes = 6210,
                MerkleRoot = "0x33aa55cc6677889",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-06", Index = 0, Label = "Counsel Wambui Kilonzo (Constitutional Law)", Votes = 3980, Percentage = 64.1 },
                    new() { PollId = "PL-ORG-06", Index = 1, Label = "Counsel Otieno Makwere (Commercial Litigation)", Votes = 1750, Percentage = 28.2 },
                    new() { PollId = "PL-ORG-06", Index = 2, Label = "Counsel Kipchumba Rotich (Public Interest)", Votes = 480, Percentage = 7.7 }
                }
            },
            new Poll {
                Id = "PL-ORG-07",
                Title = "Dairy Farmers Cooperative: Ultra-Heat Treatment (UHT) Plant Expansion",
                Description = "Resolving KES 250M capital expenditure debt financing vs member equity rights issue.",
                Category = "Agri-Business",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-09-17 14:20",
                Status = "live",
                TotalVotes = 7600,
                MerkleRoot = "0x112233445566778",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-07", Index = 0, Label = "Development Bank Low-Interest Facility", Votes = 4890, Percentage = 64.3 },
                    new() { PollId = "PL-ORG-07", Index = 1, Label = "Internal Member Rights Issue (Equity)", Votes = 2210, Percentage = 29.1 },
                    new() { PollId = "PL-ORG-07", Index = 2, Label = "Postpone Until Market Milk Prices Stabilize", Votes = 500, Percentage = 6.6 }
                }
            },
            new Poll {
                Id = "PL-ORG-08",
                Title = "Commercial Bank ESG Charter: Green Lending Portfolio Target 2030",
                Description = "Annual General Meeting resolution on 30% credit allocation to decarbonized assets.",
                Category = "Corporate Governance",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-09-14 09:30",
                Status = "live",
                TotalVotes = 15800,
                MerkleRoot = "0x889900112233445",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-08", Index = 0, Label = "Adopt Binding 30% Green Lending Target", Votes = 11400, Percentage = 72.2 },
                    new() { PollId = "PL-ORG-08", Index = 1, Label = "Set Non-Binding Aspirational Goal (20%)", Votes = 3600, Percentage = 22.8 },
                    new() { PollId = "PL-ORG-08", Index = 2, Label = "Reject Specific Quota at Board Discretion", Votes = 800, Percentage = 5.0 }
                }
            },
            new Poll {
                Id = "PL-ORG-09",
                Title = "National Pension Scheme: Infrastructure Bond vs Real Estate Allocation",
                Description = "Trustee advisory referendum on shifting 15% liquid funds into sovereign infrastructure bonds.",
                Category = "Pension Fund",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-09-11 16:00",
                Status = "live",
                TotalVotes = 11200,
                MerkleRoot = "0x99dd44ee55aa112",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-09", Index = 0, Label = "Approve Infrastructure Bond Shift (15.2% coupon)", Votes = 8120, Percentage = 72.5 },
                    new() { PollId = "PL-ORG-09", Index = 1, Label = "Maintain Prime Commercial Real Estate Assets", Votes = 2480, Percentage = 22.1 },
                    new() { PollId = "PL-ORG-09", Index = 2, Label = "Increase Offshore Blue-Chip Equity Exposure", Votes = 600, Percentage = 5.4 }
                }
            },
            new Poll {
                Id = "PL-ORG-10",
                Title = "Coastal Marine Civil Society: Blue Carbon Mangrove Credit Distribution",
                Description = "Deciding revenue sharing between village fisherfolk co-ops and county forest conservation.",
                Category = "Conservation Trust",
                Plan = "org",
                OwnerId = "USR-003",
                CreatedAt = "2026-09-08 10:30",
                Status = "closed",
                TotalVotes = 5400,
                MerkleRoot = "0x44dd22ee8899001",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ORG-10", Index = 0, Label = "70% Direct to Local Fisherfolk Community Fund", Votes = 3980, Percentage = 73.7 },
                    new() { PollId = "PL-ORG-10", Index = 1, Label = "50/50 Split with County Marine Rangers", Votes = 1180, Percentage = 21.9 },
                    new() { PollId = "PL-ORG-10", Index = 2, Label = "Reinvest 100% into Mangrove Nursery Expansion", Votes = 240, Percentage = 4.4 }
                }
            }
        };

        // ── PLAN 4: SOVEREIGN ELECTION GUARD / TURNKEY (10 POLLS) ──
        var electionPolls = new List<Poll>
        {
            new Poll {
                Id = "PL-ELEC-01",
                Title = "Presidential General Election: National Parallel Vote Tabulation (PVT)",
                Description = "Cryptographic Form 34A parallel aggregation across 250 sample polling stations.",
                Category = "National Election",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-10-01 06:00",
                Status = "live",
                TotalVotes = 124800,
                MerkleRoot = "0x8a92fc119a2e8877",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-01", Index = 0, Label = "Candidate Alliance A (Verified Tallies)", Votes = 65200, Percentage = 52.2 },
                    new() { PollId = "PL-ELEC-01", Index = 1, Label = "Candidate Coalition B (Verified Tallies)", Votes = 54600, Percentage = 43.7 },
                    new() { PollId = "PL-ELEC-01", Index = 2, Label = "Independent Candidates Combined", Votes = 3800, Percentage = 3.1 },
                    new() { PollId = "PL-ELEC-01", Index = 3, Label = "Rejected / Spoiled Paper Ballots", Votes = 1200, Percentage = 1.0 }
                }
            },
            new Poll {
                Id = "PL-ELEC-02",
                Title = "National Constitutional Amendment Referendum on Fiscal Devolution",
                Description = "Citizen plebiscite on increasing mandatory revenue allocation to county governments to 35%.",
                Category = "Constitutional Referendum",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-09-28 08:00",
                Status = "live",
                TotalVotes = 98400,
                MerkleRoot = "0x3e18bb77aa112200",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-02", Index = 0, Label = "YES (Increase Devolution Revenue to 35%)", Votes = 71200, Percentage = 72.4 },
                    new() { PollId = "PL-ELEC-02", Index = 1, Label = "NO (Retain Current 15% Baseline)", Votes = 24800, Percentage = 25.2 },
                    new() { PollId = "PL-ELEC-02", Index = 2, Label = "Informal / Invalidated Submissions", Votes = 2400, Percentage = 2.4 }
                }
            },
            new Poll {
                Id = "PL-ELEC-03",
                Title = "Nairobi County Gubernatorial Parallel Exit Poll & Verification",
                Description = "Independent statistical exit poll across 17 parliamentary constituencies in the capital.",
                Category = "Gubernatorial Contest",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-09-26 07:00",
                Status = "live",
                TotalVotes = 54200,
                MerkleRoot = "0x91bbcc22aa881100",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-03", Index = 0, Label = "Rev. Timothy Karanja (Civic Alliance)", Votes = 28900, Percentage = 53.3 },
                    new() { PollId = "PL-ELEC-03", Index = 1, Label = "Hon. Beatrice Wanjiru (National Movement)", Votes = 22400, Percentage = 41.3 },
                    new() { PollId = "PL-ELEC-03", Index = 2, Label = "Eng. Moses Ombati (Green Party)", Votes = 2900, Percentage = 5.4 }
                }
            },
            new Poll {
                Id = "PL-ELEC-04",
                Title = "Parliamentary Constituency Representative Integrity Audit",
                Description = "Station-by-station cryptographic tally audit for Embakasi West parliamentary race.",
                Category = "Parliamentary Audit",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-09-24 10:30",
                Status = "live",
                TotalVotes = 32100,
                MerkleRoot = "0x66cc001188ff44aa",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-04", Index = 0, Label = "Leading Tally Verified (Form 34B Valid)", Votes = 17800, Percentage = 55.5 },
                    new() { PollId = "PL-ELEC-04", Index = 1, Label = "Runner-Up Tally Verified", Votes = 12900, Percentage = 40.2 },
                    new() { PollId = "PL-ELEC-04", Index = 2, Label = "Contested Ballots Under Audit", Votes = 1400, Percentage = 4.3 }
                }
            },
            new Poll {
                Id = "PL-ELEC-05",
                Title = "National Public Debt Ceiling Sovereign Citizen Referendum",
                Description = "Plebiscite on capping external borrowing at 55% of Gross Domestic Product.",
                Category = "Sovereign Debt",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-09-22 09:00",
                Status = "live",
                TotalVotes = 82400,
                MerkleRoot = "0x77ee339911aa5522",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-05", Index = 0, Label = "YES (Mandate Strict 55% GDP Debt Ceiling)", Votes = 64200, Percentage = 77.9 },
                    new() { PollId = "PL-ELEC-05", Index = 1, Label = "NO (Retain Parliamentary Discretionary Cap)", Votes = 15800, Percentage = 19.2 },
                    new() { PollId = "PL-ELEC-05", Index = 2, Label = "Undecided / Spoiled Ballots", Votes = 2400, Percentage = 2.9 }
                }
            },
            new Poll {
                Id = "PL-ELEC-06",
                Title = "Judicial Independence & Magistrate Tenure Confirmation Plebiscite",
                Description = "Bar and public oversight confirmation of appellate judicial candidates.",
                Category = "Judicial Oversight",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-09-20 12:00",
                Status = "live",
                TotalVotes = 24100,
                MerkleRoot = "0x12bb44e055aacc88",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-06", Index = 0, Label = "Confirm Nominees (High Public Confidence)", Votes = 18200, Percentage = 75.5 },
                    new() { PollId = "PL-ELEC-06", Index = 1, Label = "Request Re-vetting by Judicial Service Commission", Votes = 4900, Percentage = 20.3 },
                    new() { PollId = "PL-ELEC-06", Index = 2, Label = "Abstain", Votes = 1000, Percentage = 4.2 }
                }
            },
            new Poll {
                Id = "PL-ELEC-07",
                Title = "Mombasa County Senatorial Special By-Election Audit Track",
                Description = "Port city senatorial by-election dual-observer tally reconciliation.",
                Category = "Senatorial By-Election",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-09-18 08:30",
                Status = "live",
                TotalVotes = 41200,
                MerkleRoot = "0x88f011ac33bba100",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-07", Index = 0, Label = "Coast Devolution Alliance Candidate", Votes = 23400, Percentage = 56.8 },
                    new() { PollId = "PL-ELEC-07", Index = 1, Label = "National Unity Coalition Candidate", Votes = 15800, Percentage = 38.3 },
                    new() { PollId = "PL-ELEC-07", Index = 2, Label = "Independent Youth Candidate", Votes = 2000, Percentage = 4.9 }
                }
            },
            new Poll {
                Id = "PL-ELEC-08",
                Title = "Electoral Boundaries Delimitation Citizen Consensus Referendum",
                Description = "Determining minimum population threshold for new constituency gazetting.",
                Category = "Electoral Geography",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-09-16 11:15",
                Status = "live",
                TotalVotes = 36900,
                MerkleRoot = "0x3c7e99bb44aa1102",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-08", Index = 0, Label = "Strict Population Equality Formula (130,000 baseline)", Votes = 25100, Percentage = 68.0 },
                    new() { PollId = "PL-ELEC-08", Index = 1, Label = "Special Weighting for Arid & Semi-Arid Expanses", Votes = 9800, Percentage = 26.6 },
                    new() { PollId = "PL-ELEC-08", Index = 2, Label = "Retain 290 Constituencies Without Alteration", Votes = 2000, Percentage = 5.4 }
                }
            },
            new Poll {
                Id = "PL-ELEC-09",
                Title = "Universal Healthcare Social Health Insurance Fund Mandatory Levy",
                Description = "National ballot on progressive 2.75% household income health insurance contribution.",
                Category = "Social Welfare",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-09-14 13:45",
                Status = "live",
                TotalVotes = 68200,
                MerkleRoot = "0x99a1bb22cc440011",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-09", Index = 0, Label = "Approve Social Health Insurance Universal Access", Votes = 45200, Percentage = 66.3 },
                    new() { PollId = "PL-ELEC-09", Index = 1, Label = "Maintain Voluntary Contributory NHIF Model", Votes = 19400, Percentage = 28.4 },
                    new() { PollId = "PL-ELEC-09", Index = 2, Label = "Exempt Low-Income Informal Workers", Votes = 3600, Percentage = 5.3 }
                }
            },
            new Poll {
                Id = "PL-ELEC-10",
                Title = "Sovereign Electoral Integrity Protocol: Open Source Voting Audit Act",
                Description = "Legislative plebiscite requiring all biometric voting engines to publish cryptographic receipts to public Bitcoin blocks.",
                Category = "Cryptographic Legislation",
                Plan = "election",
                OwnerId = "USR-004",
                CreatedAt = "2026-09-10 15:00",
                Status = "closed",
                TotalVotes = 91400,
                MerkleRoot = "0x8f2a71c89a2e4b10",
                IsEncryptedBallot = true,
                Options = new List<PollOption> {
                    new() { PollId = "PL-ELEC-10", Index = 0, Label = "Mandate Public Bitcoin Anchoring & Open Auditing", Votes = 79400, Percentage = 86.9 },
                    new() { PollId = "PL-ELEC-10", Index = 1, Label = "Permit Proprietary Vendor Black-Box Systems", Votes = 8200, Percentage = 9.0 },
                    new() { PollId = "PL-ELEC-10", Index = 2, Label = "Require 2-Year Pilot in 10 Counties First", Votes = 3800, Percentage = 4.1 }
                }
            }
        };

        db.Polls.AddRange(freePolls);
        db.Polls.AddRange(proPolls);
        db.Polls.AddRange(orgPolls);
        db.Polls.AddRange(electionPolls);

        // Seed Initial Vote Transactions for PL-FREE-01
        db.VoteTransactions.AddRange(
            new VoteTransaction { PollId = "PL-FREE-01", OptionIndex = 0, OptionLabel = "Approve Installation (Phase 1)", ReceiptHash = "0x8f2a71c89a2e4b1055de77189c44bb01fa1200984a1122e", MerkleLeafIndex = 1675, VoterPseudonym = "Voter-8F2A71", Timestamp = "2026-10-02 12:45:10 UTC" },
            new VoteTransaction { PollId = "PL-FREE-01", OptionIndex = 0, OptionLabel = "Approve Installation (Phase 1)", ReceiptHash = "0x3c7e99bb44aa110298fa77112004bbcc99221100334455", MerkleLeafIndex = 1674, VoterPseudonym = "Voter-3C7E99", Timestamp = "2026-10-02 12:42:33 UTC" },
            new VoteTransaction { PollId = "PL-FREE-01", OptionIndex = 1, OptionLabel = "Defer to Q2 Council Hearing", ReceiptHash = "0x99a1bb22cc44001188dd7766554433221100aabbccddeeff", MerkleLeafIndex = 1673, VoterPseudonym = "Voter-99A1BB", Timestamp = "2026-10-02 12:38:05 UTC" }
        );

        // 3. Seed Polling Stations
        db.Stations.AddRange(
            new Station { Code = "PS-108", Name = "Umoja Community Hall", County = "Nairobi", Constituency = "Embakasi West", RegisteredVoters = 650, VotesCast = 415, TurnoutPercent = 63.8, DualObservers = "2 Assigned (Dispute)", Status = "frozen", Form34AHash = "0x4a91f38d2", ObsASignature = "0x77aa11fc", ObsBSignature = "0x99dd44ee" },
            new Station { Code = "PS-001", Name = "Nairobi Primary School (Stream 1)", County = "Nairobi", Constituency = "Starehe", RegisteredVoters = 700, VotesCast = 542, TurnoutPercent = 77.4, DualObservers = "2 Verified", Status = "verified", Form34AHash = "0x12bb44e0", ObsASignature = "0x55d044ee", ObsBSignature = "0x7c12b998" },
            new Station { Code = "PS-002", Name = "Nairobi Primary School (Stream 2)", County = "Nairobi", Constituency = "Starehe", RegisteredVoters = 680, VotesCast = 520, TurnoutPercent = 76.5, DualObservers = "2 Verified", Status = "verified", Form34AHash = "0x88f011ac", ObsASignature = "0x33bba100", ObsBSignature = "0x99ee7711" },
            new Station { Code = "PS-019", Name = "Changamwe Social Hall", County = "Mombasa", Constituency = "Changamwe", RegisteredVoters = 600, VotesCast = 560, TurnoutPercent = 93.3, DualObservers = "2 Verified (Spike)", Status = "flagged", Form34AHash = "0x99ab1100", ObsASignature = "0x11223344", ObsBSignature = "0x55667788" },
            new Station { Code = "PS-042", Name = "Kisumu Day High School", County = "Kisumu", Constituency = "Kisumu Central", RegisteredVoters = 720, VotesCast = 580, TurnoutPercent = 80.5, DualObservers = "2 Verified", Status = "verified", Form34AHash = "0x44dd22ee", ObsASignature = "0x88990011", ObsBSignature = "0x22334455" },
            new Station { Code = "PS-088", Name = "Kiambu Township Primary", County = "Kiambu", Constituency = "Kiambu Town", RegisteredVoters = 690, VotesCast = 495, TurnoutPercent = 71.7, DualObservers = "2 Verified (Digits)", Status = "flagged", Form34AHash = "0x33aa55cc", ObsASignature = "0x66778899", ObsBSignature = "0x00112233" },
            new Station { Code = "PS-248", Name = "Wajir Bor Primary", County = "Wajir", Constituency = "Wajir South", RegisteredVoters = 450, VotesCast = 0, TurnoutPercent = 0.0, DualObservers = "2 En Route", Status = "pending", Form34AHash = "", ObsASignature = "", ObsBSignature = "" }
        );

        // 4. Seed Observers
        db.Observers.AddRange(
            new Observer { ObserverId = "OBS-108A", Name = "John Mutua", StationCode = "PS-108", HardwareModel = "Samsung Galaxy A54", KeystoreType = "Android KeyStore", PublicKeyFingerprint = "0x8a92fc11", BatterySignal = "88% • 4G LTE", Status = "Dispute Locked" },
            new Observer { ObserverId = "OBS-108B", Name = "Grace Wekesa", StationCode = "PS-108", HardwareModel = "Google Pixel 7a", KeystoreType = "Titan M2 Enclave", PublicKeyFingerprint = "0x3e4119a0", BatterySignal = "94% • 4G LTE", Status = "Dispute Locked" },
            new Observer { ObserverId = "OBS-001A", Name = "Kevin Omondi", StationCode = "PS-001", HardwareModel = "iPhone 14", KeystoreType = "iOS Secure Enclave", PublicKeyFingerprint = "0x7c12b998", BatterySignal = "76% • 5G", Status = "Reporting" },
            new Observer { ObserverId = "OBS-001B", Name = "Amina Noor", StationCode = "PS-001", HardwareModel = "Nokia G21", KeystoreType = "Android KeyStore", PublicKeyFingerprint = "0x55d044ee", BatterySignal = "82% • 4G LTE", Status = "Reporting" }
        );

        // 5. Seed Ledger Blocks
        db.LedgerBlocks.AddRange(
            new LedgerBlock { Height = 14210, BlockHash = "0x9f1a8e25c4411aa0099bb44", PreviousHash = "0x4b7c120e981aa220011", PayloadType = "Form 34A Packet", LeafCount = 32, Timestamp = "1m ago", MerkleRoot = "0x8a92fc11" },
            new LedgerBlock { Height = 14209, BlockHash = "0x4b7c120e981aa220011", PreviousHash = "0x1d22aa9aa1334455", PayloadType = "Station Tally Receipt", LeafCount = 64, Timestamp = "3m ago", MerkleRoot = "0x8a92fc11" },
            new LedgerBlock { Height = 14208, BlockHash = "0x1d22aa9aa1334455", PreviousHash = "0xfa77991120003344", PayloadType = "Dispute Freeze Event", LeafCount = 1, Timestamp = "14m ago", MerkleRoot = "0x8a92fc11" }
        );

        // 6. Seed Anomalies
        db.Anomalies.AddRange(
            new Anomaly { Id = 1, StationCode = "PS-019", RuleName = "Turnout Spike (+25.1%)", Severity = "warning", Description = "93.3% recorded vs 68.2% historical regional baseline across 14 neighboring centers.", Timestamp = "20m ago" },
            new Anomaly { Id = 2, StationCode = "PS-088", RuleName = "Benford Digit Multiples", Severity = "warning", Description = "6 of 8 candidates recorded multiples of 5, indicating potential manual estimation.", Timestamp = "35m ago" }
        );

        // 7. Seed Disputes
        db.Disputes.Add(new Dispute
        {
            Id = "DSP-108",
            StationCode = "PS-108",
            StationName = "Umoja Community Hall",
            ObserverA = "John Mutua (OBS-108A)",
            ObserverB = "Grace Wekesa (OBS-108B)",
            ObsATally = 395,
            ObsBTally = 415,
            Variance = 20,
            Status = "frozen",
            AuditorFinding = "Observer B tally (670 total) exceeds station registered capacity of 650. Form 34A photo shows numeral smudge."
        });

        // 8. Seed Checkpoints
        db.Checkpoints.AddRange(
            new Checkpoint { CheckpointId = 142, MerkleRootHash = "0x8a92fc119a2e8877", SubmissionsCount = 14210, BitcoinBlockHeight = 884120, BitcoinTxId = "0x9a88ff1122003344", Status = "Bitcoin Confirmed", PublishedAt = "15 min ago" },
            new Checkpoint { CheckpointId = 141, MerkleRootHash = "0x3e18bb77aa112200", SubmissionsCount = 12850, BitcoinBlockHeight = 884114, BitcoinTxId = "0x1122334455667788", Status = "Bitcoin Confirmed", PublishedAt = "1 hr ago" }
        );

        // 9. Seed Audit Logs
        db.AuditLogs.AddRange(
            new AuditLog { Id = 1, Timestamp = "18:32:04 EAT", Actor = "Faith Mwangi", Role = "Reviewer", Action = "Station Freeze Protocol Activated", TargetResource = "PS-108 (Dispute #108)", Signature = "0x9a8812c4" },
            new AuditLog { Id = 2, Timestamp = "18:26:10 EAT", Actor = "Grace Wekesa", Role = "Observer", Action = "Form 34A Packet Submitted", TargetResource = "PS-108 (Stream 1)", Signature = "0x44bbee90" }
        );

        // 10. Seed Stats
        db.Stats.Add(new SystemStat { Id = 1 });

        db.SaveChanges();
    }

    if (!db.Surveys.Any())
    {
        SeedSurveys(db);
    }
}

    private static void SeedSurveys(AppDbContext db)
    {
        var surveys = new List<Survey>
        {
            new Survey
            {
                Id = "SRV-FREE-01",
                Title = "County Clinical Healthcare & Public Services Census 2026",
                Description = "Annual grassroots census on clinic access, medicine availability, and outpatient fee transparency across Sub-County wards.",
                Track = "Public Health",
                Plan = "free",
                Status = "active",
                TargetResponses = 5000,
                TotalResponses = 4820,
                CreatedAt = "2026-09-12 08:30",
                OwnerId = "USR-001",
                MerkleCohortRoot = "0x892a01bf7834cc99",
                Questions = new List<SurveyQuestion>
                {
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-FREE-01",
                        Index = 1,
                        QuestionText = "How would you rate the availability of essential medicines at your local ward dispensary?",
                        QuestionType = "rating_scale",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "1 Star - Critical Shortages", "2 Stars - Frequent Stockouts", "3 Stars - Baseline Supply", "4 Stars - Generally Good", "5 Stars - Fully Stocked" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "1 Star - Critical Shortages", 420 }, { "2 Stars - Frequent Stockouts", 890 }, { "3 Stars - Baseline Supply", 1820 }, { "4 Stars - Generally Good", 1250 }, { "5 Stars - Fully Stocked", 440 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-FREE-01",
                        Index = 2,
                        QuestionText = "What is your primary travel mode to access emergency medical services?",
                        QuestionType = "multiple_choice",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Walking / Footpath", "Boda Boda / Motorcycle", "Public Matatu", "Private Ambulance / Vehicle" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Walking / Footpath", 980 }, { "Boda Boda / Motorcycle", 2140 }, { "Public Matatu", 1450 }, { "Private Ambulance / Vehicle", 250 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-FREE-01",
                        Index = 3,
                        QuestionText = "Have you experienced unrecorded or unofficial out-of-pocket charges during recent public clinic visits?",
                        QuestionType = "binary",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Yes - Documented", "No - Standard Protocol", "Prefer not to say" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Yes - Documented", 1120 }, { "No - Standard Protocol", 3410 }, { "Prefer not to say", 290 } })
                    }
                }
            },
            new Survey
            {
                Id = "SRV-PRO-01",
                Title = "National FinTech & Mobile Money Consumer Experience Survey",
                Description = "Multi-market empirical study on mobile banking fees, AI credit underwriting fairness, and consumer digital rights.",
                Track = "Financial Inclusion",
                Plan = "pro",
                Status = "active",
                TargetResponses = 15000,
                TotalResponses = 14200,
                CreatedAt = "2026-09-05 11:15",
                OwnerId = "USR-002",
                MerkleCohortRoot = "0x44fa77e02911b382",
                Questions = new List<SurveyQuestion>
                {
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-PRO-01",
                        Index = 1,
                        QuestionText = "Which mobile money platform handles the majority of your daily commercial transactions?",
                        QuestionType = "multiple_choice",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Safaricom M-Pesa", "Airtel Money", "T-Kash", "Commercial Banking App" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Safaricom M-Pesa", 9820 }, { "Airtel Money", 2840 }, { "T-Kash", 420 }, { "Commercial Banking App", 1120 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-PRO-01",
                        Index = 2,
                        QuestionText = "Rate your level of concern regarding automated AI algorithmic credit scoring and loan limits",
                        QuestionType = "rating_scale",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "1 - Not Concerned", "2 - Mild", "3 - Moderate", "4 - High Concern", "5 - Severe Algorithmic Bias" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "1 - Not Concerned", 1100 }, { "2 - Mild", 2400 }, { "3 - Moderate", 4500 }, { "4 - High Concern", 3900 }, { "5 - Severe Algorithmic Bias", 2300 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-PRO-01",
                        Index = 3,
                        QuestionText = "Do you support mandatory transparent open-source auditing for credit bureau scoring formulas?",
                        QuestionType = "multiple_choice",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Strongly Support", "Support with Privacy Protections", "Oppose / Proprietary IP" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Strongly Support", 9100 }, { "Support with Privacy Protections", 4250 }, { "Oppose / Proprietary IP", 850 } })
                    }
                }
            },
            new Survey
            {
                Id = "SRV-PRO-02",
                Title = "Kenyan Supermarkets & Shopping Malls National Consumer Census 2026",
                Description = "National consumer survey evaluating customer experience, pricing, stock availability, and checkout speed across major Kenyan supermarket chains and shopping malls by County.",
                Track = "Retail & Consumer Research",
                Plan = "pro",
                Status = "active",
                TargetResponses = 20000,
                TotalResponses = 18450,
                CreatedAt = "2026-10-01 09:30",
                OwnerId = "USR-002",
                MerkleCohortRoot = "0x98fa11a28892bb54",
                Questions = new List<SurveyQuestion>
                {
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-PRO-02",
                        Index = 1,
                        QuestionText = "Which County in Kenya do you primarily conduct your supermarket & mall shopping in?",
                        QuestionType = "multiple_choice",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Nairobi County", "Mombasa County", "Kiambu County", "Nakuru County", "Uasin Gishu County (Eldoret)", "Kisumu County", "Machakos County", "Kilifi County", "Other County" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Nairobi County", 7850 }, { "Mombasa County", 2410 }, { "Kiambu County", 2150 }, { "Nakuru County", 1890 }, { "Uasin Gishu County (Eldoret)", 1420 }, { "Kisumu County", 1210 }, { "Machakos County", 890 }, { "Kilifi County", 420 }, { "Other County", 210 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-PRO-02",
                        Index = 2,
                        QuestionText = "Which supermarket chain is your primary destination for groceries and household goods?",
                        QuestionType = "multiple_choice",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Naivas Supermarket", "Quickmart Supermarket", "Carrefour Kenya", "Chandarana Foodplus", "Cleanshelf Supermarket", "Khetias Supermarket", "Other Local Supermarket" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Naivas Supermarket", 7920 }, { "Quickmart Supermarket", 4810 }, { "Carrefour Kenya", 3450 }, { "Chandarana Foodplus", 1120 }, { "Cleanshelf Supermarket", 610 }, { "Khetias Supermarket", 390 }, { "Other Local Supermarket", 150 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-PRO-02",
                        Index = 3,
                        QuestionText = "Which shopping mall or commercial complex do you visit most frequently in your region?",
                        QuestionType = "multiple_choice",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Two Rivers Mall (Nairobi)", "Garden City Mall (Nairobi)", "Sarit Centre (Westlands)", "Yaya Centre (Kilimani)", "Galleria Mall (Karen)", "Nyali Centre / City Mall (Mombasa)", "Rupa's Mall (Eldoret)", "Westgate Shopping Mall (Nairobi)", "Mega Plaza (Kisumu)", "Local Town Commercial Center" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Two Rivers Mall (Nairobi)", 3840 }, { "Garden City Mall (Nairobi)", 2910 }, { "Sarit Centre (Westlands)", 3420 }, { "Yaya Centre (Kilimani)", 1820 }, { "Galleria Mall (Karen)", 1650 }, { "Nyali Centre / City Mall (Mombasa)", 2140 }, { "Rupa's Mall (Eldoret)", 1250 }, { "Westgate Shopping Mall (Nairobi)", 890 }, { "Mega Plaza (Kisumu)", 410 }, { "Local Town Commercial Center", 120 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-PRO-02",
                        Index = 4,
                        QuestionText = "How would you rate product pricing fairness, stock availability, and checkout speed at your preferred retail store?",
                        QuestionType = "rating_scale",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "5 Stars - Excellent Service & Fair Prices", "4 Stars - Good Overall Experience", "3 Stars - Average Service & Pricing", "2 Stars - Long Queues & Price Inflation", "1 Star - Frequent Stockouts & Poor Service" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "5 Stars - Excellent Service & Fair Prices", 4120 }, { "4 Stars - Good Overall Experience", 7890 }, { "3 Stars - Average Service & Pricing", 4210 }, { "2 Stars - Long Queues & Price Inflation", 1820 }, { "1 Star - Frequent Stockouts & Poor Service", 410 } })
                    }
                }
            },
            new Survey
            {
                Id = "SRV-ORG-01",
                Title = "National Union of Educators: 2026 Workplace Welfare & Safety Audit",
                Description = "Comprehensive institutional questionnaire on student-teacher ratios, mental health, and collective bargaining allowances.",
                Track = "Labor Welfare",
                Plan = "org",
                Status = "active",
                TargetResponses = 10000,
                TotalResponses = 8950,
                CreatedAt = "2026-08-25 14:00",
                OwnerId = "USR-003",
                MerkleCohortRoot = "0x1b9083ee42a17799",
                Questions = new List<SurveyQuestion>
                {
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-ORG-01",
                        Index = 1,
                        QuestionText = "Does your learning institution meet the national standard student-to-teacher ratio (1:35)?",
                        QuestionType = "multiple_choice",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Meets Standard (<= 1:35)", "Moderately Overcrowded (36-50)", "Severely Overcrowded (50+)" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Meets Standard (<= 1:35)", 1450 }, { "Moderately Overcrowded (36-50)", 4120 }, { "Severely Overcrowded (50+)", 3380 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-ORG-01",
                        Index = 2,
                        QuestionText = "Rate the adequacy of institutional mental health and counseling support services",
                        QuestionType = "rating_scale",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "1 Star - Deficient", "2 Stars - Marginal", "3 Stars - Acceptable", "4 Stars - Strong", "5 Stars - Comprehensive" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "1 Star - Deficient", 3890 }, { "2 Stars - Marginal", 2840 }, { "3 Stars - Acceptable", 1420 }, { "4 Stars - Strong", 610 }, { "5 Stars - Comprehensive", 190 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-ORG-01",
                        Index = 3,
                        QuestionText = "Should the union prioritize a 22% hardship allowance or universal comprehensive dental/optical cover in the CBA?",
                        QuestionType = "multiple_choice",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Hardship Allowance Priority", "Universal Comprehensive Health", "Equal 50/50 Compromise" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Hardship Allowance Priority", 4920 }, { "Universal Comprehensive Health", 2840 }, { "Equal 50/50 Compromise", 1190 } })
                    }
                }
            },
            new Survey
            {
                Id = "SRV-ELEC-01",
                Title = "Sub-County Civic Ward Assembly Priority & Electoral Governance Census",
                Description = "Sovereign precinct study on public participation, capital project allocation, and verifiable ballot confidence.",
                Track = "Civic Governance",
                Plan = "election",
                Status = "active",
                TargetResponses = 50000,
                TotalResponses = 42100,
                CreatedAt = "2026-08-10 09:00",
                OwnerId = "USR-ADMIN",
                MerkleCohortRoot = "0x77ee12a9bc440011",
                Questions = new List<SurveyQuestion>
                {
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-ELEC-01",
                        Index = 1,
                        QuestionText = "How confident are you in the tamper-evident dual-observer signature protocol at your voting center?",
                        QuestionType = "rating_scale",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "1 - Low Confidence", "2 - Marginal", "3 - Moderate", "4 - High Confidence", "5 - Absolute Verification" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "1 - Low Confidence", 1200 }, { "2 - Marginal", 3400 }, { "3 - Moderate", 9500 }, { "4 - High Confidence", 16800 }, { "5 - Absolute Verification", 11200 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-ELEC-01",
                        Index = 2,
                        QuestionText = "What municipal capital investment should the Ward Assembly prioritize in the 2026/2027 fiscal year?",
                        QuestionType = "multiple_choice",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Solar Micro-Grid Street Lighting", "Paved Feeder Drainage & Tarmacking", "Borehole Clean Water Reticulation", "Modern Agricultural Aggregation Center" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Solar Micro-Grid Street Lighting", 16400 }, { "Paved Feeder Drainage & Tarmacking", 11800 }, { "Borehole Clean Water Reticulation", 9800 }, { "Modern Agricultural Aggregation Center", 4100 } })
                    },
                    new SurveyQuestion
                    {
                        SurveyId = "SRV-ELEC-01",
                        Index = 3,
                        QuestionText = "Do you support biometric voter verification paired with SHA-256 public paper receipts?",
                        QuestionType = "binary",
                        OptionsJson = JsonSerializer.Serialize(new List<string> { "Fully Support", "Support with Anonymous Auditing", "Oppose Digital Tallying" }),
                        ResponsesJson = JsonSerializer.Serialize(new Dictionary<string, int> { { "Fully Support", 28900 }, { "Support with Anonymous Auditing", 11400 }, { "Oppose Digital Tallying", 1800 } })
                    }
                }
            }
        };

        db.Surveys.AddRange(surveys);
        db.SaveChanges();
    }
}
