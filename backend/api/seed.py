"""
GetItRight — Idempotent Database Seed Script
Populates realistic mock data across all tables for dashboard consumption.
Safe to run multiple times — skips tables that already have rows.
"""
import json
import uuid
import hashlib
import random
from datetime import datetime, timezone, timedelta

from backend.api.core.database import SessionLocal, engine, Base
from backend.api.features.auth.models import UserModel
from backend.api.features.polls.models import PollModel, PollOptionModel, VoteTransactionModel
from backend.api.features.surveys.models import SurveyModel, SurveyQuestionModel, SurveyResponseModel
from backend.api.features.analytics.models import (
    StationModel, AnomalyModel, DisputeModel, CheckpointModel,
    ObserverModel, LedgerBlockModel, AuditLogModel, StatModel
)

# Ensure tables exist
Base.metadata.create_all(bind=engine)


def _hash(val: str) -> str:
    return "0x" + hashlib.sha256(val.encode("utf-8")).hexdigest()[:16]


def _ts_offset(days_ago: int, hour: int = 10) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    dt = dt.replace(hour=hour, minute=random.randint(0, 59))
    return dt.strftime("%Y-%m-%d %H:%M")


def seed_users(db):
    if db.query(UserModel).count() > 0:
        print("[SEED] Users table already has data — skipping.")
        return

    users = [
        {"Id": "USR-001", "FullName": "Grace Wanjiku", "Email": "grace@getitright.io", "Password": _hash("pass1"), "Role": "Customer", "Plan": "free", "PlanName": "Civic Starter", "Organization": "Umoja Community Initiative", "VoterQuota": 1000, "PollsQuota": 5, "TotalPollsCreated": 3, "TotalVotesReceived": 140},
        {"Id": "USR-002", "FullName": "Marcus Kiprop", "Email": "marcus@getitright.io", "Password": _hash("pass2"), "Role": "Customer", "Plan": "pro", "PlanName": "Civic Pro", "Organization": "Kericho Youth Forum", "VoterQuota": 10000, "PollsQuota": 25, "TotalPollsCreated": 5, "TotalVotesReceived": 620},
        {"Id": "USR-003", "FullName": "Faith Mwangi", "Email": "faith@getitright.io", "Password": _hash("pass3"), "Role": "Admin", "Plan": "org", "PlanName": "Organization", "Organization": "Civic Transparency Initiative", "VoterQuota": 100000, "PollsQuota": 500, "TotalPollsCreated": 12, "TotalVotesReceived": 4200},
        {"Id": "USR-004", "FullName": "Brian Otieno", "Email": "brian@getitright.io", "Password": _hash("pass4"), "Role": "Analyst", "Plan": "org", "PlanName": "Organization", "Organization": "Data Insights Kenya", "VoterQuota": 50000, "PollsQuota": 100, "TotalPollsCreated": 2, "TotalVotesReceived": 310},
        {"Id": "USR-005", "FullName": "Alice Njeri", "Email": "alice@getitright.io", "Password": _hash("pass5"), "Role": "Auditor", "Plan": "election", "PlanName": "Election Grade", "Organization": "Independent Electoral Board", "VoterQuota": 500000, "PollsQuota": 9999, "TotalPollsCreated": 0, "TotalVotesReceived": 0},
        {"Id": "USR-006", "FullName": "Diana Wekesa", "Email": "diana@getitright.io", "Password": _hash("pass6"), "Role": "Customer", "Plan": "free", "PlanName": "Civic Starter", "Organization": "Independent", "VoterQuota": 1000, "PollsQuota": 5, "TotalPollsCreated": 1, "TotalVotesReceived": 45},
        {"Id": "USR-007", "FullName": "Charles Mutua", "Email": "charles@getitright.io", "Password": _hash("pass7"), "Role": "Customer", "Plan": "pro", "PlanName": "Civic Pro", "Organization": "Mombasa Tech Hub", "VoterQuota": 10000, "PollsQuota": 25, "TotalPollsCreated": 4, "TotalVotesReceived": 890},
        {"Id": "USR-008", "FullName": "Sarah Akinyi", "Email": "sarah@getitright.io", "Password": _hash("pass8"), "Role": "Customer", "Plan": "free", "PlanName": "Civic Starter", "Organization": "Independent", "VoterQuota": 1000, "PollsQuota": 5, "TotalPollsCreated": 2, "TotalVotesReceived": 78},
        {"Id": "USR-009", "FullName": "Joseph Kamau", "Email": "joseph@getitright.io", "Password": _hash("pass9"), "Role": "Enterprise Publisher", "Plan": "org", "PlanName": "Organization", "Organization": "Kenya Corporate Council", "VoterQuota": 50000, "PollsQuota": 100, "TotalPollsCreated": 6, "TotalVotesReceived": 1500},
        {"Id": "USR-010", "FullName": "Lucy Chebet", "Email": "lucy@getitright.io", "Password": _hash("pass10"), "Role": "Customer", "Plan": "free", "PlanName": "Civic Starter", "Organization": "Independent", "VoterQuota": 1000, "PollsQuota": 5, "TotalPollsCreated": 1, "TotalVotesReceived": 32},
        {"Id": "USR-011", "FullName": "Peter Ochieng", "Email": "peter@getitright.io", "Password": _hash("pass11"), "Role": "Customer", "Plan": "pro", "PlanName": "Civic Pro", "Organization": "Kisumu Urban Council", "VoterQuota": 10000, "PollsQuota": 25, "TotalPollsCreated": 3, "TotalVotesReceived": 410},
        {"Id": "USR-012", "FullName": "Rose Wambui", "Email": "rose@getitright.io", "Password": _hash("pass12"), "Role": "Customer", "Plan": "free", "PlanName": "Civic Starter", "Organization": "Independent", "VoterQuota": 1000, "PollsQuota": 5, "TotalPollsCreated": 0, "TotalVotesReceived": 0},
        {"Id": "USR-013", "FullName": "James Maina", "Email": "james@getitright.io", "Password": _hash("pass13"), "Role": "Analyst", "Plan": "org", "PlanName": "Organization", "Organization": "National Statistics Bureau", "VoterQuota": 50000, "PollsQuota": 100, "TotalPollsCreated": 1, "TotalVotesReceived": 220},
        {"Id": "USR-014", "FullName": "Esther Njoki", "Email": "esther@getitright.io", "Password": _hash("pass14"), "Role": "Customer", "Plan": "pro", "PlanName": "Civic Pro", "Organization": "Nairobi Women's Network", "VoterQuota": 10000, "PollsQuota": 25, "TotalPollsCreated": 2, "TotalVotesReceived": 350},
        {"Id": "USR-015", "FullName": "Daniel Kiptoo", "Email": "daniel@getitright.io", "Password": _hash("pass15"), "Role": "Customer", "Plan": "free", "PlanName": "Civic Starter", "Organization": "Independent", "VoterQuota": 1000, "PollsQuota": 5, "TotalPollsCreated": 1, "TotalVotesReceived": 55},
    ]

    ips = ["102.217.156.42", "197.232.12.89", "105.160.10.14", "41.89.228.100", "102.68.44.210",
           "196.201.214.90", "41.72.100.30", "102.0.5.87", "105.29.168.2", "197.156.132.10",
           "102.134.88.12", "41.204.187.5", "105.48.70.22", "196.207.18.90", "102.89.45.67"]
    lats = [-1.2921, -0.5143, -1.1714, -1.2840, -4.0435, 0.0917, -0.0917, -1.3000, -0.3031, 0.3476,
            -1.2841, -1.1800, -1.2600, -1.3100, 0.5143]
    lons = [36.8219, 35.2698, 36.8356, 36.8925, 39.6682, 34.7680, 34.7680, 36.8500, 36.0800, 34.0513,
            36.8924, 36.9000, 36.7800, 36.8100, 35.2698]
    devices = ["Samsung Galaxy A54", "Dell XPS 15 / Win11", "Google Pixel 8", "iPhone 15 Pro",
               "Nokia G42 5G", "MacBook Air M3", "Tecno Spark 20", "Samsung Galaxy S24",
               "HP EliteBook 840", "Lenovo ThinkPad X1", "Google Pixel 7a",
               "Samsung Galaxy A34", "iPhone 14", "Huawei P60", "Infinix Hot 40"]

    for i, u in enumerate(users):
        user = UserModel(
            Id=u["Id"], FullName=u["FullName"], Email=u["Email"], Password=u["Password"],
            PhoneNumber=f"+254 7{random.randint(10,99)} {random.randint(100,999)} {random.randint(100,999)}",
            IpAddress=ips[i], Latitude=lats[i], Longitude=lons[i],
            DeviceDetails=devices[i], Role=u["Role"], Plan=u["Plan"], PlanName=u["PlanName"],
            Organization=u["Organization"],
            CreatedAt=_ts_offset(random.randint(30, 180)),
            Status="Active",
            TotalPollsCreated=u["TotalPollsCreated"], TotalVotesReceived=u["TotalVotesReceived"],
            VoterQuota=u["VoterQuota"], PollsQuota=u["PollsQuota"],
            ConsoleUrl="/console/console.html" if u["Role"] == "Customer" else "/console/admin.html",
            LastLogin=f"{random.randint(1,48)} hours ago"
        )
        db.add(user)

    db.commit()
    print(f"[SEED] Inserted {len(users)} users.")


def seed_polls(db):
    kitui_east_exists = db.query(PollModel).filter(PollModel.Id == "PL-KITUI-EAST-2027").first()
    
    polls_data = []
    if not kitui_east_exists:
        polls_data.append({
            "Id": "PL-KITUI-EAST-2027",
            "Title": "Kitui East Constituency MP Aspirants Poll 2027",
            "Description": "Official 2027 opinion poll for Kitui East Constituency Member of Parliament (MP) aspirants.",
            "Category": "Constituency MP Election",
            "Plan": "election",
            "OwnerId": "USR-003",
            "Options": [
                "Zak Syengo (Zacchaeus Syengo) - Wiper",
                "Nelson Muling'a - Wiper",
                "Amb. Kiema Kilonzo - Wiper",
                "Wilson Muange Musyoka",
                "Hon. Nimrod Mbai - UDA (Incumbent)",
                "Henry Nyamai",
                "Other / Undecided"
            ]
        })

    if db.query(PollModel).count() == 0:
        polls_data.extend([
            {"Id": "PL-FREE-A1B2", "Title": "Best Public Transport Option for Nairobi", "Description": "Help us decide which transport mode the city should invest in next.", "Category": "Civic Priority", "Plan": "free", "OwnerId": "USR-001", "Options": ["BRT Buses", "Light Rail", "Expanded Matatu Routes", "Cycling Infrastructure"]},
            {"Id": "PL-FREE-C3D4", "Title": "Community Park Activities Preference", "Description": "What activities should we prioritize in the new community park?", "Category": "General", "Plan": "free", "OwnerId": "USR-006", "Options": ["Playground Equipment", "Sports Courts", "Walking Trails", "Community Garden"]},
            {"Id": "PL-FREE-E5F6", "Title": "Preferred School Calendar Model", "Description": "Which academic calendar model works best for families?", "Category": "General", "Plan": "free", "OwnerId": "USR-008", "Options": ["Traditional (3 Terms)", "Semester System", "Year-Round", "Flexible Hybrid"]},
            {"Id": "PL-PRO-G7H8", "Title": "Workplace Flexibility Survey", "Description": "How should our company approach remote work going forward?", "Category": "Enterprise Feedback", "Plan": "pro", "OwnerId": "USR-002", "Options": ["Fully Remote", "Hybrid (3 days office)", "Hybrid (2 days office)", "Fully On-Site", "Employee Choice"]},
            {"Id": "PL-PRO-I9J0", "Title": "Digital Payment Preference", "Description": "Which digital payment platform do you use most?", "Category": "Product Roadmap", "Plan": "pro", "OwnerId": "USR-007", "Options": ["M-Pesa", "Airtel Money", "Bank App", "PayPal", "Crypto Wallet"]},
            {"Id": "PL-PRO-K1L2", "Title": "Tech Conference Topic Priorities", "Description": "Vote for the topics you want covered at DevFest 2026.", "Category": "Product Roadmap", "Plan": "pro", "OwnerId": "USR-011", "Options": ["AI/ML", "Cybersecurity", "Cloud Native", "Mobile Development", "Blockchain"]},
            {"Id": "PL-ORG-M3N4", "Title": "County Budget Allocation Priorities", "Description": "How should the county allocate the development budget?", "Category": "Civic Priority", "Plan": "org", "OwnerId": "USR-003", "Options": ["Healthcare", "Education", "Infrastructure", "Agriculture", "Security"]},
            {"Id": "PL-ORG-O5P6", "Title": "Employee Benefits Package Selection", "Description": "Select the benefits package that matters most to you.", "Category": "Enterprise Feedback", "Plan": "org", "OwnerId": "USR-009", "Options": ["Extended Health Cover", "Education Allowance", "Remote Work Stipend", "Gym Membership", "Stock Options"]},
            {"Id": "PL-ORG-Q7R8", "Title": "Renewable Energy Investment Priority", "Description": "Which renewable energy source should receive priority funding?", "Category": "Civic Priority", "Plan": "org", "OwnerId": "USR-004", "Options": ["Solar Farms", "Wind Turbines", "Geothermal", "Hydroelectric"]},
            {"Id": "PL-FREE-S9T0", "Title": "Favorite Local Cuisine", "Description": "Vote for the cuisine that best represents our region.", "Category": "General", "Plan": "free", "OwnerId": "USR-010", "Options": ["Nyama Choma", "Ugali & Sukuma", "Pilau", "Chapati & Beans", "Fish & Chips"]},
            {"Id": "PL-PRO-U1V2", "Title": "Product Feature Prioritization Q4", "Description": "Which feature should our team ship first in Q4?", "Category": "Product Roadmap", "Plan": "pro", "OwnerId": "USR-014", "Options": ["Dark Mode", "Offline Support", "Multi-language", "API Integrations"]},
            {"Id": "PL-FREE-W3X4", "Title": "Weekend Market Location Vote", "Description": "Where should the new weekend market be located?", "Category": "General", "Plan": "free", "OwnerId": "USR-015", "Options": ["Central Park Area", "Riverside Drive", "Stadium Grounds", "University Field"]},
        ])

    # Distribute votes across months (last 6 months)
    month_weights = [0.08, 0.12, 0.14, 0.18, 0.25, 0.23]  # May→Oct weights

    for pd in polls_data:
        total_votes = random.randint(30, 450)
        new_poll = PollModel(
            Id=pd["Id"], Title=pd["Title"], Description=pd["Description"],
            Category=pd["Category"], Plan=pd["Plan"], OwnerId=pd["OwnerId"],
            CreatedAt=_ts_offset(random.randint(10, 160)),
            Status="live", TotalVotes=total_votes,
            MerkleRoot=_hash(f"{pd['Id']}:{pd['Title']}"),
            IsEncryptedBallot=1 if pd["Plan"] in ["pro", "org", "election"] else 0
        )
        db.add(new_poll)
        db.flush()

        # Distribute votes across options
        remaining = total_votes
        opts = pd["Options"]
        for idx, label in enumerate(opts):
            if idx == len(opts) - 1:
                opt_votes = remaining
            else:
                opt_votes = random.randint(0, remaining)
                remaining -= opt_votes

            pct = round((opt_votes / total_votes) * 100, 1) if total_votes > 0 else 0.0
            option = PollOptionModel(
                PollId=pd["Id"], Index=idx, Label=label, Votes=opt_votes, Percentage=pct
            )
            db.add(option)

        # Generate vote transactions spread over 6 months
        for v in range(min(total_votes, 25)):  # cap transactions for performance
            month_idx = random.choices(range(6), weights=month_weights, k=1)[0]
            days_ago = (5 - month_idx) * 30 + random.randint(0, 29)
            opt_idx = random.randint(0, len(opts) - 1)
            voter_key = f"Voter-{uuid.uuid4().hex[:6]}"
            ts = _ts_offset(days_ago, random.randint(6, 22))
            receipt = _hash(f"{pd['Id']}:{opt_idx}:{voter_key}:{ts}")

            tx = VoteTransactionModel(
                PollId=pd["Id"], OptionIndex=opt_idx, OptionLabel=opts[opt_idx],
                ReceiptHash=receipt, MerkleLeafIndex=v + 1,
                VoterPseudonym=voter_key, Timestamp=ts
            )
            db.add(tx)

    db.commit()
    print(f"[SEED] Inserted {len(polls_data)} polls with options and vote transactions.")


def seed_surveys(db):
    if db.query(SurveyModel).count() > 0:
        print("[SEED] Surveys table already has data — skipping.")
        return

    surveys_data = [
        {
            "Id": "SRV-FREE-A1B2", "Title": "Community Services Satisfaction", "Description": "Rate your experience with local community services.", "Track": "General", "Plan": "free", "OwnerId": "USR-001", "TargetResponses": 200,
            "Questions": [
                {"Text": "How satisfied are you with public sanitation services?", "Type": "choice", "Options": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"]},
                {"Text": "Rate the quality of local water supply (1-5)", "Type": "rating", "Options": ["1", "2", "3", "4", "5"]},
                {"Text": "What improvement would you prioritize?", "Type": "text", "Options": []},
            ]
        },
        {
            "Id": "SRV-PRO-C3D4", "Title": "Employee Engagement Pulse Check", "Description": "Quick pulse survey on employee morale and engagement.", "Track": "Enterprise Feedback", "Plan": "pro", "OwnerId": "USR-002", "TargetResponses": 500,
            "Questions": [
                {"Text": "I feel valued at my workplace.", "Type": "choice", "Options": ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]},
                {"Text": "My manager supports my professional growth.", "Type": "choice", "Options": ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]},
                {"Text": "Rate your work-life balance (1-5)", "Type": "rating", "Options": ["1", "2", "3", "4", "5"]},
                {"Text": "What one thing would improve your work experience?", "Type": "text", "Options": []},
            ]
        },
        {
            "Id": "SRV-ORG-E5F6", "Title": "Product Roadmap Feedback Q4 2026", "Description": "Help us shape the product roadmap for Q4.", "Track": "Product Roadmap", "Plan": "org", "OwnerId": "USR-009", "TargetResponses": 300,
            "Questions": [
                {"Text": "Which feature matters most to your workflow?", "Type": "choice", "Options": ["Real-time Collaboration", "Advanced Analytics", "API Integrations", "Mobile App"]},
                {"Text": "How likely are you to recommend our product? (NPS)", "Type": "rating", "Options": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]},
                {"Text": "Rate ease of onboarding (1-5)", "Type": "rating", "Options": ["1", "2", "3", "4", "5"]},
                {"Text": "Describe a feature you wish existed.", "Type": "text", "Options": []},
            ]
        },
        {
            "Id": "SRV-FREE-G7H8", "Title": "Civic Priorities for Ward Development", "Description": "Rank the development priorities for your ward.", "Track": "Civic Priority", "Plan": "free", "OwnerId": "USR-008", "TargetResponses": 400,
            "Questions": [
                {"Text": "Which infrastructure project should be prioritized?", "Type": "choice", "Options": ["Road Repair", "Street Lighting", "Drainage Systems", "Public Toilets", "Market Stalls"]},
                {"Text": "Rate your satisfaction with current ward leadership (1-5)", "Type": "rating", "Options": ["1", "2", "3", "4", "5"]},
                {"Text": "What is the biggest challenge in your community?", "Type": "text", "Options": []},
                {"Text": "Would you attend a public participation forum?", "Type": "choice", "Options": ["Yes, Definitely", "Maybe", "No"]},
            ]
        },
        {
            "Id": "SRV-PRO-I9J0", "Title": "Customer NPS & Satisfaction Survey", "Description": "Measure Net Promoter Score and customer happiness.", "Track": "Enterprise Feedback", "Plan": "pro", "OwnerId": "USR-007", "TargetResponses": 250,
            "Questions": [
                {"Text": "How likely are you to recommend us to a friend? (0-10)", "Type": "rating", "Options": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]},
                {"Text": "What do you like most about our service?", "Type": "choice", "Options": ["Speed", "Reliability", "Customer Support", "Price", "Features"]},
                {"Text": "What could we do better?", "Type": "text", "Options": []},
            ]
        },
        {
            "Id": "SRV-ORG-K1L2", "Title": "Annual Company Culture Assessment", "Description": "Comprehensive assessment of organizational culture and values.", "Track": "Enterprise Feedback", "Plan": "org", "OwnerId": "USR-004", "TargetResponses": 600,
            "Questions": [
                {"Text": "Our company values are clearly communicated.", "Type": "choice", "Options": ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]},
                {"Text": "Rate overall job satisfaction (1-5)", "Type": "rating", "Options": ["1", "2", "3", "4", "5"]},
                {"Text": "I have opportunities for career advancement.", "Type": "choice", "Options": ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]},
                {"Text": "What aspect of company culture needs improvement?", "Type": "text", "Options": []},
                {"Text": "Rate leadership transparency (1-5)", "Type": "rating", "Options": ["1", "2", "3", "4", "5"]},
            ]
        },
        {
            "Id": "SRV-FREE-M3N4", "Title": "Event Feedback — DevFest Nairobi 2026", "Description": "Share your feedback on the recent DevFest event.", "Track": "General", "Plan": "free", "OwnerId": "USR-011", "TargetResponses": 150,
            "Questions": [
                {"Text": "Overall event rating (1-5)", "Type": "rating", "Options": ["1", "2", "3", "4", "5"]},
                {"Text": "Which session was most valuable?", "Type": "choice", "Options": ["Keynote", "Workshop A: AI/ML", "Workshop B: Cloud", "Panel Discussion", "Networking Session"]},
                {"Text": "Would you attend next year?", "Type": "choice", "Options": ["Definitely", "Probably", "Unlikely", "No"]},
                {"Text": "Any suggestions for improvement?", "Type": "text", "Options": []},
            ]
        },
        {
            "Id": "SRV-PRO-O5P6", "Title": "Market Research — Fintech Adoption", "Description": "Understanding digital financial services adoption patterns.", "Track": "Product Roadmap", "Plan": "pro", "OwnerId": "USR-014", "TargetResponses": 350,
            "Questions": [
                {"Text": "Which mobile money service do you use most?", "Type": "choice", "Options": ["M-Pesa", "Airtel Money", "T-Kash", "Bank App", "None"]},
                {"Text": "How often do you use mobile payments?", "Type": "choice", "Options": ["Daily", "Weekly", "Monthly", "Rarely", "Never"]},
                {"Text": "Rate your trust in digital payments (1-5)", "Type": "rating", "Options": ["1", "2", "3", "4", "5"]},
                {"Text": "What feature would increase your usage?", "Type": "text", "Options": []},
            ]
        },
    ]

    for sd in surveys_data:
        total_resp = random.randint(20, sd["TargetResponses"])
        survey = SurveyModel(
            Id=sd["Id"], Title=sd["Title"], Description=sd["Description"],
            Track=sd["Track"], Plan=sd["Plan"], Status="Active",
            TargetResponses=sd["TargetResponses"], TotalResponses=total_resp,
            CreatedAt=_ts_offset(random.randint(5, 120)),
            OwnerId=sd["OwnerId"],
            MerkleCohortRoot=_hash(f"{sd['Id']}:{sd['Title']}"),
            TargetAudience="General Public", OrganizationName="Verified Civic Publisher"
        )
        db.add(survey)
        db.flush()

        for qi, q in enumerate(sd["Questions"]):
            # Build response distribution
            responses = {}
            if q["Options"]:
                for opt in q["Options"]:
                    responses[opt] = random.randint(2, max(3, total_resp // len(q["Options"])))
            else:
                responses["(open text)"] = total_resp

            question = SurveyQuestionModel(
                SurveyId=sd["Id"], Index=qi, QuestionText=q["Text"],
                QuestionType=q["Type"],
                OptionsJson=json.dumps(q["Options"]),
                ResponsesJson=json.dumps(responses)
            )
            db.add(question)

        # Generate survey response records
        for r in range(min(total_resp, 20)):
            voter = f"Respondent-{uuid.uuid4().hex[:6]}"
            ts = _ts_offset(random.randint(1, 60), random.randint(7, 21))
            answers = []
            for qi, q in enumerate(sd["Questions"]):
                if q["Options"]:
                    answers.append({"questionId": qi, "answer": random.choice(q["Options"])})
                else:
                    answers.append({"questionId": qi, "answer": "Sample open text response."})

            resp = SurveyResponseModel(
                SurveyId=sd["Id"], VoterPseudonym=voter,
                AnswersJson=json.dumps(answers),
                ReceiptHash=_hash(f"{sd['Id']}:{voter}:{ts}"),
                MerkleLeafIndex=r + 1, Timestamp=ts
            )
            db.add(resp)

    db.commit()
    print(f"[SEED] Inserted {len(surveys_data)} surveys with questions and responses.")


def seed_analytics(db):
    # Stations
    if db.query(StationModel).count() == 0:
        stations = [
            StationModel(Code="ST-042", Name="St. Jude Primary Hall", County="Kiambu", Constituency="Kiambu Central", RegisteredVoters=750, VotesCast=721, TurnoutPercent=96.1, DualObservers="Alice Njeri / Brian Otieno", Status="verified", Form34AHash=_hash("ST-042-F34A"), ObsASignature=_hash("obsA-042"), ObsBSignature=_hash("obsB-042")),
            StationModel(Code="ST-108", Name="Umoja Community Center", County="Nairobi", Constituency="Nairobi East", RegisteredVoters=920, VotesCast=868, TurnoutPercent=94.3, DualObservers="Charles Mutua / Diana Wekesa", Status="frozen", Form34AHash=_hash("ST-108-F34A"), ObsASignature=_hash("obsA-108"), ObsBSignature=_hash("obsB-108")),
            StationModel(Code="ST-019", Name="Township Secondary School", County="Mombasa", Constituency="Mombasa Urban", RegisteredVoters=600, VotesCast=560, TurnoutPercent=93.3, DualObservers="Esther Njoki", Status="flagged", Form34AHash=_hash("ST-019-F34A"), ObsASignature=_hash("obsA-019"), ObsBSignature=_hash("obsB-019")),
            StationModel(Code="ST-230", Name="Highway Polytechnic", County="Nakuru", Constituency="Nakuru West", RegisteredVoters=840, VotesCast=720, TurnoutPercent=85.7, DualObservers="Joseph Kamau", Status="verified", Form34AHash=_hash("ST-230-F34A"), ObsASignature=_hash("obsA-230"), ObsBSignature=_hash("obsB-230")),
            StationModel(Code="ST-311", Name="Lakeview Academy", County="Kisumu", Constituency="Kisumu Central", RegisteredVoters=550, VotesCast=518, TurnoutPercent=94.2, DualObservers="Peter Ochieng", Status="verified", Form34AHash=_hash("ST-311-F34A"), ObsASignature=_hash("obsA-311"), ObsBSignature=_hash("obsB-311")),
        ]
        for s in stations:
            db.add(s)
        db.commit()
        print("[SEED] Inserted 5 stations.")

    # Observers
    if db.query(ObserverModel).count() == 0:
        observers = [
            ObserverModel(ObserverId="OBS-001", Name="Alice Njeri", StationCode="ST-042", HardwareModel="Google Pixel 8", KeystoreType="FIDO2 Hardware Key", PublicKeyFingerprint="04a29f8c...3e1b7", BatterySignal="92% / Strong", Status="Active"),
            ObserverModel(ObserverId="OBS-002", Name="Brian Otieno", StationCode="ST-042", HardwareModel="Samsung Galaxy A54", KeystoreType="App TOTP", PublicKeyFingerprint="04bc12e8...7a9f0", BatterySignal="78% / Good", Status="Active"),
            ObserverModel(ObserverId="OBS-003", Name="Charles Mutua", StationCode="ST-108", HardwareModel="Google Pixel 7a", KeystoreType="FIDO2 Hardware Key", PublicKeyFingerprint="04de7108...42ba6", BatterySignal="85% / Strong", Status="Active"),
            ObserverModel(ObserverId="OBS-004", Name="Diana Wekesa", StationCode="ST-108", HardwareModel="Nokia G42 5G", KeystoreType="SMS OTP", PublicKeyFingerprint="048f0129...c4890", BatterySignal="65% / Fair", Status="Active"),
            ObserverModel(ObserverId="OBS-005", Name="Esther Njoki", StationCode="ST-019", HardwareModel="iPhone 15 Pro", KeystoreType="FIDO2 Hardware Key", PublicKeyFingerprint="04f21c87...5e3d2", BatterySignal="90% / Strong", Status="Active"),
            ObserverModel(ObserverId="OBS-006", Name="Joseph Kamau", StationCode="ST-230", HardwareModel="Samsung Galaxy S24", KeystoreType="App TOTP", PublicKeyFingerprint="04ab34f1...8c7e9", BatterySignal="70% / Good", Status="Active"),
            ObserverModel(ObserverId="OBS-007", Name="Peter Ochieng", StationCode="ST-311", HardwareModel="Google Pixel 8", KeystoreType="FIDO2 Hardware Key", PublicKeyFingerprint="04cd89a3...2f1b4", BatterySignal="88% / Strong", Status="Active"),
        ]
        for o in observers:
            db.add(o)
        db.commit()
        print("[SEED] Inserted 7 observers.")

    # Anomalies
    if db.query(AnomalyModel).count() == 0:
        anomalies = [
            AnomalyModel(StationCode="ST-019", RuleName="Turnout Spike vs Regional Baseline", Severity="High", Description="Station turnout is 93.3% while surrounding 14 stations average 68.2% (+25.1% variance).", Timestamp=_ts_offset(0, 14)),
            AnomalyModel(StationCode="ST-108", RuleName="Dual-Observer Count Variance", Severity="High", Description="Observer A records 395 for Candidate B, Observer B records 415 (20 vote difference).", Timestamp=_ts_offset(0, 13)),
            AnomalyModel(StationCode="ST-088", RuleName="Last-Digit Benford Distribution Variance", Severity="Medium", Description="Sub-tally round numbers: 6 out of 8 candidates end with zero or five (p = 0.008).", Timestamp=_ts_offset(1, 9)),
        ]
        for a in anomalies:
            db.add(a)
        db.commit()
        print("[SEED] Inserted 3 anomalies.")

    # Disputes
    if db.query(DisputeModel).count() == 0:
        dispute = DisputeModel(
            Id="DISP-108", StationCode="ST-108", StationName="Umoja Community Center",
            ObserverA="Charles Mutua", ObserverB="Diana Wekesa",
            ObsATally=868, ObsBTally=888, Variance=20,
            Status="frozen", AuditorFinding="Pending manual recount verification"
        )
        db.add(dispute)
        db.commit()
        print("[SEED] Inserted 1 dispute.")

    # Checkpoints
    if db.query(CheckpointModel).count() == 0:
        checkpoints = [
            CheckpointModel(CheckpointId=140, MerkleRootHash=_hash("CP-140"), SubmissionsCount=13200, BitcoinBlockHeight=884108, BitcoinTxId="0x" + uuid.uuid4().hex, Status="Bitcoin Confirmed", PublishedAt=_ts_offset(3, 14)),
            CheckpointModel(CheckpointId=141, MerkleRootHash=_hash("CP-141"), SubmissionsCount=13950, BitcoinBlockHeight=884117, BitcoinTxId="0x" + uuid.uuid4().hex, Status="Bitcoin Confirmed", PublishedAt=_ts_offset(1, 8)),
            CheckpointModel(CheckpointId=142, MerkleRootHash=_hash("CP-142"), SubmissionsCount=14210, BitcoinBlockHeight=884120, BitcoinTxId="0x" + uuid.uuid4().hex, Status="Bitcoin Confirmed", PublishedAt=_ts_offset(0, 10)),
            CheckpointModel(CheckpointId=143, MerkleRootHash=_hash("CP-143"), SubmissionsCount=14580, BitcoinBlockHeight=884126, BitcoinTxId="0x" + uuid.uuid4().hex, Status="Pending Confirmation", PublishedAt=_ts_offset(0, 14)),
        ]
        for c in checkpoints:
            db.add(c)
        db.commit()
        print("[SEED] Inserted 4 checkpoints.")

    # Ledger Blocks
    if db.query(LedgerBlockModel).count() == 0:
        prev = _hash("genesis")
        for i in range(6):
            bh = _hash(f"block-{i}-{prev}")
            block = LedgerBlockModel(
                BlockHash=bh, PreviousHash=prev,
                PayloadType=random.choice(["StationResult", "VoteBatch", "AnomalyFlag", "DisputeFreeze"]),
                LeafCount=random.randint(50, 500),
                Timestamp=_ts_offset(5 - i, random.randint(8, 18)),
                MerkleRoot=_hash(f"merkle-{i}")
            )
            db.add(block)
            prev = bh
        db.commit()
        print("[SEED] Inserted 6 ledger blocks.")

    # Audit Logs
    if db.query(AuditLogModel).count() == 0:
        actions = [
            ("Faith Mwangi", "Admin", "STATION_FREEZE", "Station ST-108"),
            ("Diana Wekesa", "Observer", "SUBMIT_STATION_RESULT", "Station ST-108 / Entry #14207"),
            ("Charles Mutua", "Observer", "SUBMIT_STATION_RESULT", "Station ST-108 / Entry #14206"),
            ("System Engine", "Daemon", "CHECKPOINT_PUBLISH", "Merkle Root #142"),
            ("Alice Njeri", "Observer", "SUBMIT_STATION_RESULT", "Station ST-042 / Entry #14208"),
            ("Brian Otieno", "Observer", "SUBMIT_STATION_RESULT", "Station ST-042 / Entry #14209"),
            ("Faith Mwangi", "Admin", "USER_ROLE_UPDATE", "USR-007 role → Civic Pro"),
            ("System Engine", "Daemon", "ANOMALY_DETECTED", "ST-019 Turnout Spike"),
            ("Joseph Kamau", "Observer", "SUBMIT_STATION_RESULT", "Station ST-230 / Entry #14210"),
            ("System Engine", "Daemon", "CHECKPOINT_PUBLISH", "Merkle Root #143"),
        ]
        for actor, role, action, target in actions:
            log = AuditLogModel(
                Timestamp=_ts_offset(random.randint(0, 5), random.randint(6, 22)),
                Actor=actor, Role=role, Action=action, TargetResource=target,
                Signature=_hash(f"{actor}:{action}:{target}")
            )
            db.add(log)
        db.commit()
        print("[SEED] Inserted 10 audit logs.")

    # Stats
    if db.query(StatModel).count() == 0:
        stat = StatModel(
            StationsTotal=250, StationsReporting=242,
            LedgerCommits=14580, ActiveObservers=7,
            OpenAnomalies=3, IngestionMsgPerSec=1420,
            P99LatencyMs=2.4, ChainIntegrityPercent=100.0
        )
        db.add(stat)
        db.commit()
        print("[SEED] Inserted platform stats.")


def run_seed():
    print("=" * 60)
    print(" GetItRight — Database Seed Script")
    print("=" * 60)
    db = SessionLocal()
    try:
        seed_users(db)
        seed_polls(db)
        seed_surveys(db)
        seed_analytics(db)
        print("\n[SEED COMPLETE] All mock data populated successfully.")
    except Exception as e:
        db.rollback()
        print(f"\n[SEED ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
