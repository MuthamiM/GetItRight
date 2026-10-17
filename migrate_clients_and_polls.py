"""
Migrate and seed the GetItRight database:
1. Super Admin: Musa Mwange (password: 11858077)
2. Clients: HEZRON MASUMBA, MARTIN MULWA, FESTUS JONAH (password: 11858077, Role: Customer)
3. 5 Active Polls and 5 Active Surveys for EACH client (total 15 polls, 15 surveys)
4. Disable all other users, archive older polls & surveys, but retain them in DB
"""
import os
import sys
import json
import uuid
import hashlib
from datetime import datetime, timezone, timedelta

# Add repo to sys.path
sys.path.insert(0, "/home/cantroll/POLL")

from backend.api.core.database import SessionLocal
from backend.api.features.auth.models import UserModel
from backend.api.features.polls.models import PollModel, PollOptionModel
from backend.api.features.surveys.models import SurveyModel, SurveyQuestionModel
from backend.api.core.security import get_password_hash

def run_migration():
    db = SessionLocal()
    try:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        super_hash = get_password_hash("11858077")
        client_hash = get_password_hash("11858077")

        print("[1/5] Setting up Super Admin: Musa Mwange...")
        # Update or create admin user with admin@getitright.io and musamwange42@gmail.com
        admin_user = db.query(UserModel).filter(UserModel.Email == "admin@getitright.io").first()
        if not admin_user:
            admin_user = UserModel(
                Id="USR-ADMIN",
                FullName="Musa Mwange",
                Email="admin@getitright.io",
                Password=super_hash,
                Role="Admin",
                Plan="election",
                PlanName="Sovereign Election Guard",
                Organization="GetItRight National Commission",
                Status="Active",
                VoterQuota=10000000,
                PollsQuota=1000,
                ConsoleUrl="/console/admin.html",
                CreatedAt=now_str,
                LastLogin=now_str
            )
            db.add(admin_user)
        else:
            admin_user.FullName = "Musa Mwange"
            admin_user.Password = super_hash
            admin_user.Role = "Admin"
            admin_user.Plan = "election"
            admin_user.PlanName = "Sovereign Election Guard"
            admin_user.Organization = "GetItRight National Commission"
            admin_user.Status = "Active"
            admin_user.ConsoleUrl = "/console/admin.html"

        # Also update musamwange42@gmail.com if present
        musa_personal = db.query(UserModel).filter(UserModel.Email == "musamwange42@gmail.com").first()
        if musa_personal:
            musa_personal.FullName = "Musa Mwange"
            musa_personal.Password = super_hash
            musa_personal.Role = "Admin"
            musa_personal.Plan = "election"
            musa_personal.PlanName = "Sovereign Election Guard"
            musa_personal.Status = "Active"
            musa_personal.ConsoleUrl = "/console/admin.html"

        print("[2/5] Creating / updating 3 New Clients...")
        clients_data = [
            {
                "id": "USR-HEZRON-01",
                "name": "HEZRON MASUMBA",
                "email": "hezron.masumba@getitright.io",
                "org": "Masumba Civic Research & Strategy",
            },
            {
                "id": "USR-MARTIN-01",
                "name": "MARTIN MULWA",
                "email": "martin.mulwa@getitright.io",
                "org": "Mulwa Data & Economic Analytics",
            },
            {
                "id": "USR-FESTUS-01",
                "name": "FESTUS JONAH",
                "email": "festus.jonah@getitright.io",
                "org": "Jonah Polling & Infrastructure Review",
            }
        ]

        active_user_ids = {admin_user.Id}
        if musa_personal:
            active_user_ids.add(musa_personal.Id)

        for c in clients_data:
            existing = db.query(UserModel).filter(
                (UserModel.Id == c["id"]) | (UserModel.Email == c["email"])
            ).first()
            if existing:
                existing.FullName = c["name"]
                existing.Email = c["email"]
                existing.Password = client_hash
                existing.Role = "Customer"
                existing.Plan = "pro"
                existing.PlanName = "Civic Pro"
                existing.Organization = c["org"]
                existing.Status = "Active"
                existing.VoterQuota = 50000
                existing.PollsQuota = 50
                existing.ConsoleUrl = "/console/user.html"
                active_user_ids.add(existing.Id)
            else:
                new_u = UserModel(
                    Id=c["id"],
                    FullName=c["name"],
                    Email=c["email"],
                    Password=client_hash,
                    Role="Customer",
                    Plan="pro",
                    PlanName="Civic Pro",
                    Organization=c["org"],
                    Status="Active",
                    VoterQuota=50000,
                    PollsQuota=50,
                    ConsoleUrl="/console/user.html",
                    CreatedAt=now_str,
                    LastLogin=now_str
                )
                db.add(new_u)
                active_user_ids.add(c["id"])

        print("[3/5] Disabling all other users...")
        all_users = db.query(UserModel).all()
        disabled_count = 0
        for u in all_users:
            if u.Id not in active_user_ids:
                u.Status = "Disabled"
                disabled_count += 1
        print(f"      Disabled {disabled_count} previous users.")

        print("[4/5] Archiving previous polls and closing previous surveys...")
        old_polls = db.query(PollModel).all()
        for p in old_polls:
            p.Status = "archived"
        print(f"      Archived {len(old_polls)} previous polls.")

        old_surveys = db.query(SurveyModel).all()
        for s in old_surveys:
            s.Status = "closed"
        print(f"      Closed {len(old_surveys)} previous surveys.")

        print("[5/5] Seeding 5 Active Polls and 5 Active Surveys for each client...")
        # Define 5 polls for each client
        polls_by_client = {
            "USR-HEZRON-01": [
                {
                    "id": "PL-HEZRON-01",
                    "title": "Nairobi County Transport Infrastructure & Commuter Rail Expansion 2026/2027",
                    "desc": "Public opinion on priority mass-transit investments for the Nairobi Metropolitan Area.",
                    "category": "Urban Transport",
                    "options": [
                        "Bus Rapid Transit (BRT) Dedicated Corridors",
                        "Commuter Rail Modernization & New Stations",
                        "Smart Traffic Management & Intelligent Signals",
                        "Non-Motorized Transport (Walkways & Cycle Lanes)"
                    ]
                },
                {
                    "id": "PL-HEZRON-02",
                    "title": "Kenya National Healthcare Financing: Social Health Insurance Fund (SHIF) Transition",
                    "desc": "Assessment of citizen access, benefit packages, and out-of-pocket costs under SHIF.",
                    "category": "Healthcare & Social Welfare",
                    "options": [
                        "Highly Effective & Accessible",
                        "Needs Streamlined Facility Registration",
                        "High Out-of-Pocket Burden at Primary Level",
                        "Requires Fundamental Tariff Overhaul"
                    ]
                },
                {
                    "id": "PL-HEZRON-03",
                    "title": "Machakos County Agricultural Value Addition & Youth Agro-Processing Priorities",
                    "desc": "Targeted county investments in agro-processing hubs, storage, and market access.",
                    "category": "County Agriculture",
                    "options": [
                        "Cold Storage Hubs for Perishables",
                        "Targeted Seed & Fertilizer Voucher Programs",
                        "Direct Cooperative Export Market Linkages",
                        "Solar-Powered Drip Irrigation Infrastructure"
                    ]
                },
                {
                    "id": "PL-HEZRON-04",
                    "title": "Makueni County Green Energy & Solar Grid Decentralization Initiative",
                    "desc": "Decentralized clean power generation for water pumping and rural cottage industries.",
                    "category": "Energy & Sustainability",
                    "options": [
                        "Community Solar Mini-Grids",
                        "Solar-Powered High-Yield Boreholes",
                        "Subsidized Commercial Household Solar",
                        "Industrial Agro-Processing Micro-Grids"
                    ]
                },
                {
                    "id": "PL-HEZRON-05",
                    "title": "National Digital Identity & Data Privacy Confidence Level in Public Services",
                    "desc": "Public confidence in sovereign cryptographic voter receipts and digital identity safety.",
                    "category": "Digital Rights & Governance",
                    "options": [
                        "Complete Trust / Robust Privacy Standards",
                        "Moderate Trust / Needs Independent Audits",
                        "Low Trust / Data Protection Concerns",
                        "No Trust / Full Parliamentary Reform Required"
                    ]
                }
            ],
            "USR-MARTIN-01": [
                {
                    "id": "PL-MARTIN-01",
                    "title": "Kitui Central Constituency 2027 Parliamentary Leadership & Development Agenda",
                    "desc": "Voter priorities for the upcoming legislative term in Kitui Central Constituency.",
                    "category": "Parliamentary Elections",
                    "options": [
                        "Youth TVET Skills & Digital Work Hubs",
                        "Piped Clean Water Reticulation to All Wards",
                        "Modern Market Infrastructure for Traders",
                        "Revolving Micro-Enterprise Credit Grants"
                    ]
                },
                {
                    "id": "PL-MARTIN-02",
                    "title": "Kenya AI & Machine Learning Adoption in Financial Inclusion & SACCOs",
                    "desc": "Role of algorithmic scoring and conversational tech in cooperative financial institutions.",
                    "category": "FinTech & Co-operatives",
                    "options": [
                        "Automated Credit Risk & Micro-Loan Scoring",
                        "Real-time Fraud Detection & AML Monitoring",
                        "Conversational Banking in Local Dialects",
                        "Smart Dividend & Investment Allocation"
                    ]
                },
                {
                    "id": "PL-MARTIN-03",
                    "title": "National University Funding Model (NFM): Student Support & Sustainability Review",
                    "desc": "Public sentiment on student scholarship bands, household means testing, and university loans.",
                    "category": "Higher Education",
                    "options": [
                        "Retain Current Bands with Higher Direct Grants",
                        "Return to Differentiated Unit Cost System",
                        "Expand HELB Low-Interest Revolving Loans",
                        "Fully Subsidize Priority STEM & Medical Programs"
                    ]
                },
                {
                    "id": "PL-MARTIN-04",
                    "title": "Eastern Region Avocado & Macadamia Export Cooperative Quality Standards",
                    "desc": "Export competitiveness and fair pricing mechanisms for smallholder tree-crop growers.",
                    "category": "Agri-Export & Trade",
                    "options": [
                        "Mandatory Digital Traceability Barcodes",
                        "Direct Freight Logistics from Local Hubs",
                        "County Cooperative Controlled-Atmosphere Stores",
                        "Subsidized GlobalGAP Organic Certification"
                    ]
                },
                {
                    "id": "PL-MARTIN-05",
                    "title": "Kenya SME Taxation & Digital Service Tax (DST) Compliance Sentiment",
                    "desc": "Evaluating the compliance burden and incentive structure for small tech-enabled enterprises.",
                    "category": "Taxation & Economic Policy",
                    "options": [
                        "Simplified Single Flat Turnover Rate",
                        "Raise Mandatory VAT Registration Threshold",
                        "Zero-Rate Digital Productivity & Developer Software",
                        "3-Year Complete Tax Holiday for Startups"
                    ]
                }
            ],
            "USR-FESTUS-01": [
                {
                    "id": "PL-FESTUS-01",
                    "title": "Mombasa Port Logistics Modernization & SGR Cargo Tariff Competitiveness",
                    "desc": "Strategic interventions to position the Northern Corridor as the region's premier transit hub.",
                    "category": "Logistics & Maritime",
                    "options": [
                        "Eliminate Duplicative Last-Mile Port Charges",
                        "Automate 24/7 Green-Channel Customs Clearance",
                        "Open SGR Freight Booking to Multi-Modal Operators",
                        "Expand Inland Container Depots with Cold Chains"
                    ]
                },
                {
                    "id": "PL-FESTUS-02",
                    "title": "National Carbon Credit Revenue Sharing & Community Climate Action",
                    "desc": "Equitable revenue splits between institutional developers and indigenous forest communities.",
                    "category": "Climate Action & Carbon Markets",
                    "options": [
                        "Mandatory 40% Minimum Community Revenue Pass-through",
                        "Direct Household Clean Cooking Technology Grants",
                        "County-Level Ward Climate Adaptation Funds",
                        "Restoration Subsidies for Mangrove & Indigenous Forests"
                    ]
                },
                {
                    "id": "PL-FESTUS-03",
                    "title": "Kitui South Mineral Resources & Limestone Mining Royalties Framework",
                    "desc": "Ensuring transparent revenue allocation and environmental protections for host mining communities.",
                    "category": "Natural Resources & Mining",
                    "options": [
                        "Direct Community Ward Bursary & Scholarship Trust",
                        "Paved Heavy-Duty Mining Road Infrastructure",
                        "Strict Mandatory Environmental Reclamation Escrow",
                        "Enforceable 70% Local Employment Quota"
                    ]
                },
                {
                    "id": "PL-FESTUS-04",
                    "title": "Kenya Cybersecurity & Mobile Money Consumer Protection Readiness 2026",
                    "desc": "Safeguarding citizens against social engineering, SIM swaps, and predatory micro-loan harvesting.",
                    "category": "Cybersecurity & Consumer Protection",
                    "options": [
                        "Mandatory Real-Time Facial Biometric SIM Lock",
                        "Instant 24-Hour Automated Freeze on Suspect Transfers",
                        "Free Universal Public Cyber Fraud Literacy Drives",
                        "Mandatory Bank & Telco Consumer Insurance Pool"
                    ]
                },
                {
                    "id": "PL-FESTUS-05",
                    "title": "Renewable Geothermal & Wind Energy Power Purchase Tariff Optimization",
                    "desc": "Lowering industrial and commercial electricity tariffs to stimulate domestic manufacturing.",
                    "category": "Industrial Power & Utilities",
                    "options": [
                        "Targeted Sub-$0.08/kWh Industrial Power Band",
                        "Feed-in Tariff Framework for Commercial Rooftops",
                        "Expand Off-Peak Night-Shift Heavy Power Discounts",
                        "Accelerate Special Economic Zone (SEZ) Direct Hookups"
                    ]
                }
            ]
        }

        # Seed polls
        for owner_id, polls in polls_by_client.items():
            for poll_spec in polls:
                existing_p = db.query(PollModel).filter(PollModel.Id == poll_spec["id"]).first()
                initial_root = "0x" + hashlib.sha256(f"{poll_spec['id']}:{poll_spec['title']}".encode("utf-8")).hexdigest()[:16]
                if existing_p:
                    existing_p.Title = poll_spec["title"]
                    existing_p.Description = poll_spec["desc"]
                    existing_p.Category = poll_spec["category"]
                    existing_p.OwnerId = owner_id
                    existing_p.Plan = "pro"
                    existing_p.Status = "live"
                    existing_p.TotalVotes = 0
                    existing_p.MerkleRoot = initial_root
                    existing_p.CreatedAt = now_str
                    existing_p.EndDate = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                    # Clear existing options
                    db.query(PollOptionModel).filter(PollOptionModel.PollId == poll_spec["id"]).delete()
                else:
                    new_p = PollModel(
                        Id=poll_spec["id"],
                        Title=poll_spec["title"],
                        Description=poll_spec["desc"],
                        Category=poll_spec["category"],
                        Plan="pro",
                        OwnerId=owner_id,
                        CreatedAt=now_str,
                        Status="live",
                        TotalVotes=0,
                        MerkleRoot=initial_root,
                        IsEncryptedBallot=1,
                        EndDate=(datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                    )
                    db.add(new_p)

                # Add options
                for idx, opt_label in enumerate(poll_spec["options"]):
                    db.add(PollOptionModel(
                        PollId=poll_spec["id"],
                        Index=idx,
                        Label=opt_label,
                        Votes=0,
                        Percentage=0.0
                    ))

        # Define 5 surveys for each client
        surveys_by_client = {
            "USR-HEZRON-01": [
                {
                    "id": "SRV-HEZRON-01",
                    "title": "Metropolitan Transit Efficiency & Commuter Cost Assessment",
                    "desc": "Comprehensive census on daily fare expenditures, travel times, and passenger safety.",
                    "track": "Urban Mobility",
                    "questions": [
                        {
                            "text": "What is your average daily commuting fare expense in the Nairobi Metropolitan Area?",
                            "type": "choice",
                            "options": ["Below KES 100", "KES 100 - 250", "KES 250 - 500", "Above KES 500"]
                        },
                        {
                            "text": "How reliable do you find public transport scheduling during peak morning hours?",
                            "type": "choice",
                            "options": ["Highly Predictable", "Occasional Delays (15-30m)", "Severe Congestion (>1h)", "Unusable"]
                        },
                        {
                            "text": "What priority measure would most improve your daily commute experience?",
                            "type": "choice",
                            "options": ["Dedicated Bus Lanes", "Electronic Tap-and-Go Fare Cards", "More Commuter Trains", "Better Station Lighting & Security"]
                        }
                    ]
                },
                {
                    "id": "SRV-HEZRON-02",
                    "title": "Primary Healthcare Facility Quality & Essential Medicine Availability Study",
                    "desc": "Evaluating Level 2 and Level 3 public health dispensary service levels and stock availability.",
                    "track": "Public Health",
                    "questions": [
                        {
                            "text": "When visiting your nearest local dispensary, are prescribed essential medicines in stock?",
                            "type": "choice",
                            "options": ["Always In Stock", "Partially In Stock", "Rarely In Stock", "Always Purchased Privately"]
                        },
                        {
                            "text": "What is your typical waiting time to see a clinical officer or medical officer?",
                            "type": "choice",
                            "options": ["Under 30 Minutes", "30 Minutes to 1 Hour", "1 to 3 Hours", "Over 3 Hours"]
                        },
                        {
                            "text": "How do you rate the hygiene and diagnostic equipment readiness at your local clinic?",
                            "type": "choice",
                            "options": ["Excellent", "Good / Satisfactory", "Basic / Constrained", "Critically Inadequate"]
                        }
                    ]
                },
                {
                    "id": "SRV-HEZRON-03",
                    "title": "Smallholder Farmer Drought Resilience & Irrigation Readiness Survey",
                    "desc": "Assessing crop insurance adoption, borehole access, and post-harvest grain losses.",
                    "track": "Agriculture",
                    "questions": [
                        {
                            "text": "What is your primary source of agricultural water for crop cultivation?",
                            "type": "choice",
                            "options": ["Rain-fed Only", "Community Earth Dam / Pan", "Borehole / Shallow Well", "River Drip Irrigation"]
                        },
                        {
                            "text": "Have you enrolled in any index-based agricultural drought insurance program?",
                            "type": "choice",
                            "options": ["Yes, Actively Covered", "Previously, but Discontinued", "Interested but Uninformed", "Not Interested / High Cost"]
                        },
                        {
                            "text": "What percentage of your grain or horticulture harvest is lost to post-harvest pests or lack of storage?",
                            "type": "choice",
                            "options": ["Under 5%", "5% - 15%", "15% - 30%", "Over 30%"]
                        }
                    ]
                },
                {
                    "id": "SRV-HEZRON-04",
                    "title": "County Budget Public Participation & Fiscal Transparency Audit",
                    "desc": "Examining community involvement and accountability in Annual Development Plans (ADP).",
                    "track": "Governance",
                    "questions": [
                        {
                            "text": "Have you attended a public participation forum for your County Fiscal Strategy or Ward Budget?",
                            "type": "choice",
                            "options": ["Yes, Regularly", "Once or Twice", "Aware but Unable to Attend", "Never Informed of Dates"]
                        },
                        {
                            "text": "In your view, are community priorities reflected in final county project allocations?",
                            "type": "choice",
                            "options": ["Fully Reflected", "Partially Considered", "Largely Ignored", "Completely Disregarded"]
                        },
                        {
                            "text": "Which sector deserves the highest Ward Development Fund budget share in your area?",
                            "type": "choice",
                            "options": ["Water Harvesting & Pipes", "Feeder Road Grading", "Dispensary Upgrades", "Youth Poly-technics & Grants"]
                        }
                    ]
                },
                {
                    "id": "SRV-HEZRON-05",
                    "title": "E-Citizen Digital Public Services Satisfaction & Accessibility Index",
                    "desc": "Evaluating platform reliability, transaction processing speed, and user convenience.",
                    "track": "Public Tech",
                    "questions": [
                        {
                            "text": "How frequently do you access e-Citizen portal services (passports, NTSA, land, birth certificates)?",
                            "type": "choice",
                            "options": ["Monthly or More", "A Few Times a Year", "Once a Year", "Only Through Cyber Cafe"]
                        },
                        {
                            "text": "What is the biggest bottleneck you encounter when transacting online?",
                            "type": "choice",
                            "options": ["Payment Gateway Timeouts", "Delayed Document Processing", "Confusing Interface", "No Bottlenecks / Seamless"]
                        },
                        {
                            "text": "Do you feel your personal data submitted to government portals is securely safeguarded?",
                            "type": "choice",
                            "options": ["Very Confident", "Moderately Confident", "Somewhat Concerned", "Highly Distrustful"]
                        }
                    ]
                }
            ],
            "USR-MARTIN-01": [
                {
                    "id": "SRV-MARTIN-01",
                    "title": "Higher Education Financing & Student Living Cost Welfare Survey 2026",
                    "desc": "Assessing university student tuition burdens, accommodation costs, and loan disbursement timeliness.",
                    "track": "Education",
                    "questions": [
                        {
                            "text": "What is your funding band classification under the New Higher Education Funding Model?",
                            "type": "choice",
                            "options": ["Band 1 (Vulnerable)", "Band 2 (Extremely Needy)", "Band 3 (Needy)", "Band 4 / 5 (Less Needy)", "Self-Sponsored / Private"]
                        },
                        {
                            "text": "Are your semester upkeep funds disbursed in time for the commencement of academic terms?",
                            "type": "choice",
                            "options": ["Always On Time", "Minor 2-4 Week Delay", "Severe Delay (>1 Month)", "Never Received Upkeep"]
                        },
                        {
                            "text": "What is your average monthly accommodation and food expenditure during session?",
                            "type": "choice",
                            "options": ["Under KES 8,000", "KES 8,000 - 15,000", "KES 15,000 - 25,000", "Above KES 25,000"]
                        }
                    ]
                },
                {
                    "id": "SRV-MARTIN-02",
                    "title": "Micro and Small Enterprise (MSE) Capital Access & Credit Bureau Study",
                    "desc": "Examining interest rates, working capital availability, and digital credit scoring for traders.",
                    "track": "FinTech & SMEs",
                    "questions": [
                        {
                            "text": "Where does your business primarily source emergency short-term working capital?",
                            "type": "choice",
                            "options": ["Mobile Digital Lenders", "Commercial Bank / Microfinance", "Chama / SACCO Loans", "Family & Personal Savings"]
                        },
                        {
                            "text": "How do prevailing interest rates and processing fees affect your business growth?",
                            "type": "choice",
                            "options": ["Manageable & Competitive", "High but Bearable", "Extremely Restrictive", "Prohibitive / Hindering Growth"]
                        },
                        {
                            "text": "Has negative credit bureau (CRB) listing ever prevented you from accessing essential commercial credit?",
                            "type": "choice",
                            "options": ["Yes, Due to Late Mobile Loan", "Yes, Disputed Amount", "No, Clear Credit Record", "Never Applied for Bank Credit"]
                        }
                    ]
                },
                {
                    "id": "SRV-MARTIN-03",
                    "title": "Horticulture Cooperative Aggregation & Cold Chain Distribution Audit",
                    "desc": "Study on post-harvest cold storage, cooperative bargaining power, and export grade quality.",
                    "track": "Agribusiness",
                    "questions": [
                        {
                            "text": "Do you sell your horticultural produce through a cooperative or directly to middlemen brokers?",
                            "type": "choice",
                            "options": ["Registered Farmers Cooperative", "Direct to Farm-Gate Middlemen", "Direct to Local Open Market", "Contracted Supermarket / Exporter"]
                        },
                        {
                            "text": "How far is the nearest cold storage aggregation facility from your farm?",
                            "type": "choice",
                            "options": ["Within 5 Kilometers", "5 to 20 Kilometers", "Over 20 Kilometers", "No Cold Storage Available"]
                        },
                        {
                            "text": "What would most significantly raise your seasonal farm profit margins?",
                            "type": "choice",
                            "options": ["Direct Bulk Export Contracts", "Affordable Packhouse Cold Storage", "Subsidized Organic Fertilizers", "Transparent Real-Time Market Price App"]
                        }
                    ]
                },
                {
                    "id": "SRV-MARTIN-04",
                    "title": "Rural Internet Connectivity & Remote Digital Work Hubs Census",
                    "desc": "Evaluating fiber-to-the-ward progress, mobile data pricing, and youth freelancing opportunities.",
                    "track": "Digital Economy",
                    "questions": [
                        {
                            "text": "What type of internet connectivity is available at your primary residence / workstation?",
                            "type": "choice",
                            "options": ["High-Speed Fiber (FTTH)", "4G/5G Fixed Wireless", "Mobile Phone 3G/4G Only", "Satellite (e.g. Starlink)", "No Internet Connectivity"]
                        },
                        {
                            "text": "Is there an operational government or community public digital work hub within your ward?",
                            "type": "choice",
                            "options": ["Yes, Fully Equipped & Active", "Yes, but Lacks Power/Fast Net", "Under Construction", "None in My Ward"]
                        },
                        {
                            "text": "Have you earned income through online digital freelancing, coding, or remote services in the last year?",
                            "type": "choice",
                            "options": ["Yes, Primary Income Source", "Yes, Supplemental Side Income", "Attempted, but No Clients", "Never Tried / Need Training"]
                        }
                    ]
                },
                {
                    "id": "SRV-MARTIN-05",
                    "title": "Sub-County Civic Ward Projects Implementation & Oversight Survey",
                    "desc": "Tracking project completion timelines, contractor accountability, and community handover.",
                    "track": "Devolution",
                    "questions": [
                        {
                            "text": "What is the status of budgeted capital infrastructure projects in your ward over the past 2 years?",
                            "type": "choice",
                            "options": ["Completed & In Use", "In Progress On Schedule", "Stalled / Abandoned", "Never Commenced"]
                        },
                        {
                            "text": "Is a clear billboard showing project cost, contractor, and completion date posted on site?",
                            "type": "choice",
                            "options": ["Yes, Full Transparency", "Partial Info Only", "No Signage At All", "Not Sure"]
                        },
                        {
                            "text": "How would you rate the responsiveness of your County Assembly Representative (MCA)?",
                            "type": "choice",
                            "options": ["Highly Responsive & Accessible", "Moderately Accessible", "Rarely Seen in Ward", "Completely Absent"]
                        }
                    ]
                }
            ],
            "USR-FESTUS-01": [
                {
                    "id": "SRV-FESTUS-01",
                    "title": "Logistics Corridor & Cross-Border Trade Ease Survey 2026",
                    "desc": "Evaluating border post clearance speeds, non-tariff trade barriers, and transit corridor safety.",
                    "track": "Logistics & Trade",
                    "questions": [
                        {
                            "text": "How many hours does commercial cargo clearance typically take at One-Stop Border Posts (OSBP)?",
                            "type": "choice",
                            "options": ["Under 6 Hours", "6 to 24 Hours", "1 to 3 Days", "Over 3 Days"]
                        },
                        {
                            "text": "Which non-tariff barrier poses the greatest friction on major transit corridors?",
                            "type": "choice",
                            "options": ["Uncoordinated Weighbridge Checks", "Police Checkpoint Stoppages", "Multiple County Cess Levies", "Electronic Cargo Seal Failures"]
                        },
                        {
                            "text": "Has the Single Window System streamlined your customs documentation workflows?",
                            "type": "choice",
                            "options": ["Substantially Streamlined", "Marginally Improved", "No Significant Difference", "More Complicated"]
                        }
                    ]
                },
                {
                    "id": "SRV-FESTUS-02",
                    "title": "Community Forest Conservation & Carbon Offset Benefit-Sharing Study",
                    "desc": "Assessing grassroots engagement, alternative livelihoods, and forest ranger partnerships.",
                    "track": "Climate Action",
                    "questions": [
                        {
                            "text": "Is your community forest association (CFA) formally partnered with an accredited carbon project?",
                            "type": "choice",
                            "options": ["Yes, Fully Certified", "In Application Process", "Discussions Ongoing", "No Partnership"]
                        },
                        {
                            "text": "Have community members received direct dividend payments or civic benefits (schools, boreholes)?",
                            "type": "choice",
                            "options": ["Yes, Tangible Community Projects", "Direct Cash Dividends", "Promise Made but Not Delivered", "No Benefits Received"]
                        },
                        {
                            "text": "What sustainable alternative livelihood activity is most viable for forest boundary residents?",
                            "type": "choice",
                            "options": ["Apiculture (Modern Beekeeping)", "Eco-Tourism & Guided Trails", "Agroforestry Tree Nurseries", "Commercial Bamboo Farming"]
                        }
                    ]
                },
                {
                    "id": "SRV-FESTUS-03",
                    "title": "Mining Communities Social Impact Assessment & Land Rights Review",
                    "desc": "Investigating environmental compliance, dust mitigation, and land compensation equity.",
                    "track": "Natural Resources",
                    "questions": [
                        {
                            "text": "Has large-scale commercial extraction in your region caused documented environmental or water degradation?",
                            "type": "choice",
                            "options": ["Severe Water/Dust Impact", "Moderate Localized Impact", "Minor Controlled Impact", "No Negative Impact Detected"]
                        },
                        {
                            "text": "Were displaced land owners compensated at fair, independent market valuation rates?",
                            "type": "choice",
                            "options": ["Fair Market Compensation Paid", "Under-compensated / Disputed", "Unpaid / Pending Court Claims", "Not Applicable"]
                        },
                        {
                            "text": "Does the commercial mining operator fulfill its statutory Community Development Agreement (CDA)?",
                            "type": "choice",
                            "options": ["Full CDA Compliance", "Partial Project Funding", "Minimal / Token Compliance", "Non-Compliant"]
                        }
                    ]
                },
                {
                    "id": "SRV-FESTUS-04",
                    "title": "Consumer Banking Fraud Incident Reporting & Dispute Resolution Survey",
                    "desc": "Evaluating financial institution responsiveness to unauthorized mobile banking transactions.",
                    "track": "Consumer Protection",
                    "questions": [
                        {
                            "text": "Have you or an immediate family member experienced unauthorized mobile or card deductions in the past 24 months?",
                            "type": "choice",
                            "options": ["Yes, Successfully Recovered", "Yes, Funds Lost Permanently", "Attempted Fraud Blocked in Time", "Never Experienced Fraud"]
                        },
                        {
                            "text": "How promptly did your bank or mobile operator investigate and resolve the reported dispute?",
                            "type": "choice",
                            "options": ["Resolved Within 48 Hours", "1 to 2 Weeks", "Over a Month", "Ignored / Unsatisfactory Response"]
                        },
                        {
                            "text": "What additional security feature would make you feel safest when transacting on mobile money?",
                            "type": "choice",
                            "options": ["Mandatory Facial Biometrics", "Hardware Security Token", "Delay on New Recipient Transfers", "Instant Emergency Freeze Dial-Code"]
                        }
                    ]
                },
                {
                    "id": "SRV-FESTUS-05",
                    "title": "Clean Energy Transition & Household Clean Cooking Fuel Adoption Census",
                    "desc": "Tracking adoption of LPG, ethanol, induction stoves, and bio-gas in urban and peri-urban wards.",
                    "track": "Energy & Sustainability",
                    "questions": [
                        {
                            "text": "What is the primary cooking fuel utilized in your household on a daily basis?",
                            "type": "choice",
                            "options": ["LPG (Gas Cylinder)", "Clean Ethanol / Bio-Ethanol", "Electric Induction Cooker", "Charcoal / Fuelwood"]
                        },
                        {
                            "text": "What is the main obstacle preventing your household from adopting 100% clean cooking energy?",
                            "type": "choice",
                            "options": ["Initial Cylinder / Stove Cost", "Refill Cost Volatility", "Availability of Fuel Nearby", "Cultural Taste Preference for Charcoal"]
                        },
                        {
                            "text": "Would pay-as-you-go (smart meter) micro-LPG encourage you to transition fully away from solid fuels?",
                            "type": "choice",
                            "options": ["Definitely Yes", "Probably Yes", "Unlikely", "Already Using Clean Energy"]
                        }
                    ]
                }
            ]
        }

        # Seed surveys
        for owner_id, surveys in surveys_by_client.items():
            for s_spec in surveys:
                existing_s = db.query(SurveyModel).filter(SurveyModel.Id == s_spec["id"]).first()
                initial_root = "0x" + hashlib.sha256(f"{s_spec['id']}:{s_spec['title']}".encode("utf-8")).hexdigest()[:16]
                if existing_s:
                    existing_s.Title = s_spec["title"]
                    existing_s.Description = s_spec["desc"]
                    existing_s.Track = s_spec["track"]
                    existing_s.OwnerId = owner_id
                    existing_s.Plan = "pro"
                    existing_s.Status = "active"
                    existing_s.TotalResponses = 0
                    existing_s.TargetResponses = 5000
                    existing_s.CreatedAt = now_str
                    existing_s.EndDate = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                    existing_s.MerkleCohortRoot = initial_root
                    # Clear existing questions
                    db.query(SurveyQuestionModel).filter(SurveyQuestionModel.SurveyId == s_spec["id"]).delete()
                else:
                    new_s = SurveyModel(
                        Id=s_spec["id"],
                        Title=s_spec["title"],
                        Description=s_spec["desc"],
                        Track=s_spec["track"],
                        Plan="pro",
                        Status="active",
                        TargetResponses=5000,
                        TotalResponses=0,
                        CreatedAt=now_str,
                        OwnerId=owner_id,
                        MerkleCohortRoot=initial_root,
                        TargetAudience="Verified Kenyan Citizens & Sector Professionals",
                        OrganizationName="GetItRight Verified Client Network",
                        EndDate=(datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                    )
                    db.add(new_s)

                # Add questions
                for q_idx, q_spec in enumerate(s_spec["questions"], start=1):
                    db.add(SurveyQuestionModel(
                        SurveyId=s_spec["id"],
                        Index=q_idx,
                        QuestionText=q_spec["text"],
                        QuestionType=q_spec["type"],
                        OptionsJson=json.dumps(q_spec["options"]),
                        ResponsesJson="{}"
                    ))

        db.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        print(f"Super Admin: Musa Mwange (admin@getitright.io, musamwange42@gmail.com)")
        print(f"Clients created: Hezron Masumba, Martin Mulwa, Festus Jonah")
        print(f"15 new active polls and 15 new active surveys seeded.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
