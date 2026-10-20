from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.analytics.schemas import (
    TrackingTelemetryOut, StatsOut, StationOut, AnomalyOut, DisputeOut,
    CheckpointOut, ObserverOut, LedgerBlockOut, AuditLogOut,
    AdminDashboardStatsOut, CustomerDashboardStatsOut, SurveyTemplateOut,
    PlatformNotificationIn, PlatformNotificationOut
)
from backend.api.middleware.auth_middleware import get_current_user_token, require_admin, get_optional_current_user_token


def _plain_text(value: str, field: str, maximum: int) -> str:
    clean = (value or "").strip()
    if not clean or len(clean) > maximum or any(char in clean for char in "<>"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} must be plain text")
    return clean
from backend.api.features.analytics.service import (
    get_tracking_telemetry, get_stats, list_stations, get_station_by_code,
    list_anomalies, list_disputes, list_checkpoints, list_observers,
    list_ledger, list_audit, get_admin_dashboard_stats, get_customer_dashboard_stats
)

router = APIRouter(tags=["Analytics & Cryptographic Telemetry"])

@router.get("/admin/dashboard-stats", response_model=AdminDashboardStatsOut)
def admin_dashboard_stats(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Aggregated admin dashboard stats — all KPIs, charts, and recent voters from DB."""
    from backend.api.controllers.analytics_controller import AnalyticsController
    return AnalyticsController.get_admin_dashboard_stats(db)

@router.get("/customer/dashboard-stats/{user_id}", response_model=CustomerDashboardStatsOut)
def customer_dashboard_stats(user_id: str, current_user: dict = Depends(get_current_user_token), db: Session = Depends(get_db)):
    """User-scoped dashboard stats — polls, votes, quotas, charts from DB."""
    from fastapi import HTTPException, status
    if current_user["role"] != "Admin" and current_user["sub"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only view your own dashboard")
    return get_customer_dashboard_stats(db, user_id)

@router.get("/surveys/templates", response_model=List[SurveyTemplateOut])
def survey_templates():
    """Returns pre-built survey templates for the creation wizard."""
    from backend.api.features.analytics.schemas import SurveyTemplateQuestionOut
    templates = [
        SurveyTemplateOut(
            id="tmpl-nps", name="Customer Satisfaction (NPS)",
            description="Measure Net Promoter Score and customer happiness with targeted feedback questions.",
            category="Enterprise Feedback", icon="star",
            questions=[
                SurveyTemplateQuestionOut(questionText="How likely are you to recommend us to a friend or colleague? (0-10)", questionType="rating", options=[]),
                SurveyTemplateQuestionOut(questionText="What is the primary reason for your score?", questionType="text", options=[]),
                SurveyTemplateQuestionOut(questionText="Which aspect of our service impressed you the most?", questionType="choice", options=["Speed", "Quality", "Support", "Price", "Reliability"]),
                SurveyTemplateQuestionOut(questionText="Any additional feedback?", questionType="text", options=[])
            ]
        ),
        SurveyTemplateOut(
            id="tmpl-employee", name="Employee Engagement",
            description="Assess team morale, workplace satisfaction, and identify areas for improvement.",
            category="Enterprise Feedback", icon="users",
            questions=[
                SurveyTemplateQuestionOut(questionText="How satisfied are you with your current role?", questionType="choice", options=["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"]),
                SurveyTemplateQuestionOut(questionText="Do you feel your contributions are valued by the team?", questionType="choice", options=["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]),
                SurveyTemplateQuestionOut(questionText="What would you change about the workplace?", questionType="text", options=[]),
                SurveyTemplateQuestionOut(questionText="Rate your work-life balance (1-5)", questionType="rating", options=[])
            ]
        ),
        SurveyTemplateOut(
            id="tmpl-product", name="Product Feedback",
            description="Gather user insights on product features, usability, and improvement priorities.",
            category="Product Roadmap", icon="rocket",
            questions=[
                SurveyTemplateQuestionOut(questionText="How often do you use our product?", questionType="choice", options=["Daily", "Weekly", "Monthly", "Rarely"]),
                SurveyTemplateQuestionOut(questionText="Which feature do you use the most?", questionType="choice", options=["Dashboard", "Reports", "Collaboration", "Integrations", "Other"]),
                SurveyTemplateQuestionOut(questionText="Rate the overall usability (1-5)", questionType="rating", options=[]),
                SurveyTemplateQuestionOut(questionText="What feature should we build next?", questionType="text", options=[])
            ]
        ),
        SurveyTemplateOut(
            id="tmpl-civic", name="Civic Community Priorities",
            description="Identify community needs and priorities for public resource allocation.",
            category="Civic Priority", icon="building",
            questions=[
                SurveyTemplateQuestionOut(questionText="What is the most pressing issue in your community?", questionType="choice", options=["Healthcare", "Education", "Infrastructure", "Security", "Employment", "Water & Sanitation"]),
                SurveyTemplateQuestionOut(questionText="How would you rate local government responsiveness?", questionType="rating", options=[]),
                SurveyTemplateQuestionOut(questionText="Describe a specific improvement you'd like to see", questionType="text", options=[]),
                SurveyTemplateQuestionOut(questionText="Would you participate in a follow-up town hall?", questionType="choice", options=["Yes", "No", "Maybe"])
            ]
        ),
        SurveyTemplateOut(
            id="tmpl-event", name="Event Feedback",
            description="Post-event evaluation to measure attendee satisfaction and gather improvement suggestions.",
            category="General", icon="calendar",
            questions=[
                SurveyTemplateQuestionOut(questionText="How would you rate the overall event experience?", questionType="rating", options=[]),
                SurveyTemplateQuestionOut(questionText="Which session was most valuable?", questionType="choice", options=["Keynote", "Panel Discussion", "Workshop", "Networking", "Q&A"]),
                SurveyTemplateQuestionOut(questionText="Would you attend a future event?", questionType="choice", options=["Definitely", "Probably", "Unlikely", "No"]),
                SurveyTemplateQuestionOut(questionText="Suggestions for future events?", questionType="text", options=[])
            ]
        ),
        SurveyTemplateOut(
            id="tmpl-market", name="Market Research",
            description="Understand market demographics, preferences, and purchasing behavior.",
            category="Enterprise Feedback", icon="chart",
            questions=[
                SurveyTemplateQuestionOut(questionText="What is your age range?", questionType="choice", options=["18-24", "25-34", "35-44", "45-54", "55+"]),
                SurveyTemplateQuestionOut(questionText="How did you hear about us?", questionType="choice", options=["Social Media", "Search Engine", "Word of Mouth", "Advertisement", "Other"]),
                SurveyTemplateQuestionOut(questionText="What factors most influence your purchasing decisions?", questionType="choice", options=["Price", "Quality", "Brand", "Reviews", "Convenience"]),
                SurveyTemplateQuestionOut(questionText="Any other comments about your preferences?", questionType="text", options=[])
            ]
        )
    ]
    return templates

@router.get("/admin/tracking-telemetry", response_model=TrackingTelemetryOut)
def admin_tracking_telemetry(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Fetch live aggregate platform telemetry and real vote distribution across plans."""
    return get_tracking_telemetry(db)

@router.get("/stats", response_model=StatsOut)
def platform_stats(db: Session = Depends(get_db)):
    """Fetch real-time cluster metrics, ingestion velocity, latency, and reporting stations."""
    return get_stats(db)

@router.get("/stations", response_model=List[StationOut])
def stations_list(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Fetch all 250 physical polling stations with turnout percentages and cryptographic observer hashes."""
    return list_stations(db)

@router.get("/stations/{code}", response_model=StationOut)
def station_detail(code: str, _: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Fetch specific station telemetry and Form 34A hash."""
    return get_station_by_code(db, code)

@router.get("/anomalies", response_model=List[AnomalyOut])
def anomalies_list(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Fetch active anomaly detection flags."""
    return list_anomalies(db)

@router.get("/disputes", response_model=List[DisputeOut])
def disputes_list(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Fetch dual-observer dispute reconciliations."""
    return list_disputes(db)

@router.post("/disputes/{id}/resolve")
def resolve_dispute_endpoint(id: str, _: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Resolve dual observer variance and mark polling station as verified."""
    from backend.api.features.analytics.service import resolve_dispute
    return resolve_dispute(db, id)

@router.get("/checkpoints", response_model=List[CheckpointOut])
def checkpoints_list(db: Session = Depends(get_db)):
    """Fetch Bitcoin blockchain anchored state checkpoints."""
    return list_checkpoints(db)

@router.post("/checkpoints/publish", response_model=CheckpointOut)
def publish_checkpoint_endpoint(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Anchor current ledger state to Bitcoin blockchain."""
    from backend.api.features.analytics.service import publish_checkpoint
    return publish_checkpoint(db)

@router.get("/observers", response_model=List[ObserverOut])
def observers_list(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Fetch hardware observers and cryptographic public keys."""
    return list_observers(db)

@router.get("/ledger", response_model=List[LedgerBlockOut])
def ledger_blocks(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Fetch verifiable cryptographic ledger blocks."""
    return list_ledger(db)

@router.get("/audit", response_model=List[AuditLogOut])
def audit_logs(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Fetch cryptographic audit trail signatures."""
    return list_audit(db)

@router.get("/notifications", response_model=List[PlatformNotificationOut])
def get_platform_notifications(
    user_id: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db)
):
    """Fetch active platform notifications created by admin with per-client read tracking."""
    from backend.api.features.analytics.models import PlatformNotificationModel, UserNotificationReadModel
    target_user_id = (current_user.get("sub") if current_user else None) or user_id

    records = db.query(PlatformNotificationModel).filter(PlatformNotificationModel.IsActive == 1).order_by(PlatformNotificationModel.Id.desc()).limit(50).all()

    read_notif_ids = set()
    if target_user_id:
        read_records = db.query(UserNotificationReadModel.NotificationId).filter(
            UserNotificationReadModel.UserId == target_user_id
        ).all()
        read_notif_ids = {r[0] for r in read_records}

    return [
        PlatformNotificationOut(
            id=r.Id,
            title=r.Title,
            message=r.Message,
            type=r.Type or "info",
            audience=r.Audience or "all",
            createdBy=r.CreatedBy or "Admin",
            createdAt=r.CreatedAt,
            isActive=r.IsActive or 1,
            isRead=(r.Id in read_notif_ids)
        )
        for r in records
    ]

@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    user_id: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db)
):
    """Mark a notification as read specifically for a given client/user."""
    from datetime import datetime, timezone
    from backend.api.features.analytics.models import UserNotificationReadModel
    target_user_id = (current_user.get("sub") if current_user else None) or user_id
    if not target_user_id:
        return {"success": True, "message": "No user specified"}

    existing = db.query(UserNotificationReadModel).filter(
        UserNotificationReadModel.UserId == target_user_id,
        UserNotificationReadModel.NotificationId == notification_id
    ).first()
    if not existing:
        now_iso = datetime.now(timezone.utc).isoformat()
        db.add(UserNotificationReadModel(UserId=target_user_id, NotificationId=notification_id, ReadAt=now_iso))
        db.commit()
    return {"success": True, "notificationId": notification_id, "userId": target_user_id}

@router.post("/notifications/read-all")
def mark_all_notifications_read(
    user_id: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db)
):
    """Mark all active notifications as read for a given client/user."""
    from datetime import datetime, timezone
    from backend.api.features.analytics.models import PlatformNotificationModel, UserNotificationReadModel
    target_user_id = (current_user.get("sub") if current_user else None) or user_id
    if not target_user_id:
        return {"success": True, "message": "No user specified"}

    notifs = db.query(PlatformNotificationModel.Id).filter(PlatformNotificationModel.IsActive == 1).all()
    now_iso = datetime.now(timezone.utc).isoformat()
    for (nid,) in notifs:
        existing = db.query(UserNotificationReadModel).filter(
            UserNotificationReadModel.UserId == target_user_id,
            UserNotificationReadModel.NotificationId == nid
        ).first()
        if not existing:
            db.add(UserNotificationReadModel(UserId=target_user_id, NotificationId=nid, ReadAt=now_iso))
    db.commit()
    return {"success": True, "userId": target_user_id}

@router.post("/notifications", response_model=PlatformNotificationOut)
async def create_platform_notification(
    payload: PlatformNotificationIn,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin creates and broadcasts a platform notification to all connected clients."""
    from datetime import datetime, timezone
    from backend.api.features.analytics.models import PlatformNotificationModel
    from backend.api.servers.websocket_server import ws_server

    now_iso = datetime.now(timezone.utc).isoformat()
    record = PlatformNotificationModel(
        Title=_plain_text(payload.title or "Platform Notice", "Notification title", 120),
        Message=_plain_text(payload.message, "Notification message", 500),
        Type=payload.type or "info",
        Audience=payload.audience or "all",
        CreatedBy=current_user["name"],
        CreatedAt=now_iso,
        IsActive=1
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    out = PlatformNotificationOut(
        id=record.Id,
        title=record.Title,
        message=record.Message,
        type=record.Type,
        audience=record.Audience,
        createdBy=record.CreatedBy,
        createdAt=record.CreatedAt,
        isActive=record.IsActive,
        isRead=False
    )

    try:
        await ws_server.broadcast_notification(out.dict())
    except Exception:
        pass

    return out

@router.delete("/notifications/{notification_id}")
def delete_platform_notification(notification_id: int, _: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Delete / dismiss a platform notification."""
    from backend.api.features.analytics.models import PlatformNotificationModel
    record = db.query(PlatformNotificationModel).filter(PlatformNotificationModel.Id == notification_id).first()
    if not record:
        return {"success": False, "message": "Notification not found"}
    record.IsActive = 0
    db.commit()
    return {"success": True, "message": f"Notification {notification_id} dismissed."}


@router.get("/turnout/summary")
def get_turnout_summary(
    owner_id: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db),
):
    """
    Returns authentic, real-time turnout figures calculated directly from database records:
    - Poll transactions and tallies
    - Survey responses and quotas
    - Accredited physical polling station returns
    - County-level turnout distribution
    - 24-hour intake velocity curve
    """
    from collections import defaultdict
    from sqlalchemy import func
    from backend.api.features.polls.models import PollModel, VoteTransactionModel
    from backend.api.features.surveys.models import SurveyModel, SurveyResponseModel
    from backend.api.features.analytics.models import StationModel

    # Role checking: If client user, scope to their ownerId
    if current_user and current_user.get("role") not in ["Admin", "Super Admin"]:
        owner_id = current_user.get("sub")

    # 1. Physical Stations
    stations = db.query(StationModel).all()
    tot_st_reg = sum(st.RegisteredVoters or 0 for st in stations)
    tot_st_cast = sum(st.VotesCast or 0 for st in stations)
    station_turnout_rate = round((tot_st_cast / max(tot_st_reg, 1)) * 100, 1)

    station_items = [
        {
            "code": st.Code,
            "name": st.Name,
            "county": st.County,
            "registeredVoters": st.RegisteredVoters or 0,
            "votesCast": st.VotesCast or 0,
            "turnoutRate": round(((st.VotesCast or 0) / max(st.RegisteredVoters or 1, 1)) * 100, 1),
            "status": st.Status or "Active Reporting",
            "form34AHash": st.Form34AHash or "GEN-VALIDATED"
        }
        for st in stations
    ]

    # 2. Polls
    poll_query = db.query(PollModel)
    if owner_id:
        poll_query = poll_query.filter(PollModel.OwnerId == owner_id)
    polls = poll_query.all()

    plan_quotas = {"free": 1000, "starter": 2500, "pro": 5000, "enterprise": 20000, "electoral": 50000}
    poll_items = []
    tot_poll_votes = 0
    tot_poll_quota = 0

    for p in polls:
        tx_count = db.query(VoteTransactionModel).filter(VoteTransactionModel.PollId == p.Id).count()
        votes = max(p.TotalVotes or 0, tx_count)
        tot_poll_votes += votes
        quota = plan_quotas.get((p.Plan or "free").lower(), 2500)
        tot_poll_quota += quota
        rate = round((votes / max(quota, 1)) * 100, 1)

        # Leading county for this poll
        top_cty_row = db.query(VoteTransactionModel.County, func.count(VoteTransactionModel.Id))\
            .filter(VoteTransactionModel.PollId == p.Id, VoteTransactionModel.County != None)\
            .group_by(VoteTransactionModel.County)\
            .order_by(func.count(VoteTransactionModel.Id).desc()).first()
        top_cty = top_cty_row[0] if top_cty_row else "Nairobi County"

        status_str = "Quota Met" if votes >= quota else ("Surpassing Target" if rate >= 60 else "Active Ingestion")

        poll_items.append({
            "id": p.Id,
            "type": "poll",
            "title": p.Title,
            "category": p.Category or "Public Policy",
            "plan": p.Plan,
            "quota": quota,
            "cast": votes,
            "rate": rate,
            "status": status_str,
            "topCounty": top_cty
        })

    # 3. Surveys
    survey_query = db.query(SurveyModel)
    if owner_id:
        survey_query = survey_query.filter(SurveyModel.OwnerId == owner_id)
    surveys = survey_query.all()

    survey_items = []
    tot_survey_resp = 0
    tot_survey_quota = 0

    for s in surveys:
        resp_count = db.query(SurveyResponseModel).filter(SurveyResponseModel.SurveyId == s.Id).count()
        resp = max(s.TotalResponses or 0, resp_count)
        tot_survey_resp += resp
        quota = s.TargetResponses or 5000
        tot_survey_quota += quota
        rate = round((resp / max(quota, 1)) * 100, 1)

        # Leading county for this survey
        top_cty_row = db.query(SurveyResponseModel.County, func.count(SurveyResponseModel.Id))\
            .filter(SurveyResponseModel.SurveyId == s.Id, SurveyResponseModel.County != None)\
            .group_by(SurveyResponseModel.County)\
            .order_by(func.count(SurveyResponseModel.Id).desc()).first()
        top_cty = top_cty_row[0] if top_cty_row else "Nairobi County"

        status_str = "Quota Met" if resp >= quota else ("Surpassing Target" if rate >= 60 else "Active Ingestion")

        survey_items.append({
            "id": s.Id,
            "type": "survey",
            "title": s.Title,
            "category": s.Track or "Civic Research",
            "plan": s.Plan,
            "quota": quota,
            "cast": resp,
            "rate": rate,
            "status": status_str,
            "topCounty": top_cty
        })

    # 4. County Distribution from real votes and survey submissions
    county_counts = defaultdict(int)
    for r in db.query(VoteTransactionModel.County, func.count(VoteTransactionModel.Id)).group_by(VoteTransactionModel.County).all():
        if r[0]: county_counts[r[0]] += r[1]
    for r in db.query(SurveyResponseModel.County, func.count(SurveyResponseModel.Id)).group_by(SurveyResponseModel.County).all():
        if r[0]: county_counts[r[0]] += r[1]
    for st in stations:
        if st.County: county_counts[st.County] += (st.VotesCast or 0)

    total_regional_cast = sum(county_counts.values()) or 1
    top_counties = [
        {
            "county": cty,
            "submissions": cnt,
            "share": round((cnt / total_regional_cast) * 100, 1)
        }
        for cty, cnt in sorted(county_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    ]

    # 5. Real 24h Hourly Velocity
    hourly_counts = defaultdict(int)
    for vt in db.query(VoteTransactionModel.Timestamp).all():
        try:
            ts = vt[0]
            if len(ts) >= 13 and ts[10] in (" ", "T"):
                hour = int(ts[11:13])
                hourly_counts[hour] += 1
        except Exception:
            pass
    for sr in db.query(SurveyResponseModel.Timestamp).all():
        try:
            ts = sr[0]
            if len(ts) >= 13 and ts[10] in (" ", "T"):
                hour = int(ts[11:13])
                hourly_counts[hour] += 1
        except Exception:
            pass

    hourly_velocity = [
        {"hour": f"{h:02d}:00", "votes": hourly_counts[h]}
        for h in range(24)
    ]

    # Overall Turnout Rate: station turnout if available or combined quota turnout
    total_submissions = tot_poll_votes + tot_survey_resp
    total_quota = tot_poll_quota + tot_survey_quota
    overall_turnout_rate = station_turnout_rate if station_turnout_rate > 0 else round((total_submissions / max(total_quota, 1)) * 100, 1)

    return {
        "totals": {
            "overallTurnoutRate": overall_turnout_rate,
            "physicalStationTurnoutRate": station_turnout_rate,
            "totalPollVotes": tot_poll_votes,
            "totalSurveyResponses": tot_survey_resp,
            "totalSubmissions": total_submissions,
            "totalRegisteredQuota": total_quota,
            "activePollsCount": len(polls),
            "activeSurveysCount": len(surveys),
            "totalCampaignsCount": len(polls) + len(surveys),
            "stationVotesCast": tot_st_cast,
            "stationRegisteredVoters": tot_st_reg,
        },
        "campaigns": poll_items + survey_items,
        "stations": station_items,
        "topCounties": top_counties,
        "hourlyVelocity": hourly_velocity
    }


@router.get("/turnout/export")
def export_turnout_analytics(
    export_format: str = Query("xlsx", alias="format", pattern="^(xlsx|docx|pdf|csv|json)$"),
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """Generate and stream an official Turnout & Quota Analytics report in Excel, Word, CSV, or PDF format."""
    from fastapi.responses import StreamingResponse
    from io import BytesIO, StringIO
    import csv
    import json
    from backend.api.features.polls.models import PollModel, VoteTransactionModel
    from backend.api.features.surveys.models import SurveyModel, SurveyResponseModel
    from backend.api.core.report_builder import build_turnout_xlsx, build_turnout_docx

    is_admin = current_user.get("role") in ["Admin", "Super Admin"]
    owner_id = None if is_admin else current_user.get("sub")

    # Query polls & surveys
    poll_query = db.query(PollModel)
    survey_query = db.query(SurveyModel)
    if owner_id:
        poll_query = poll_query.filter(PollModel.OwnerId == owner_id)
        survey_query = survey_query.filter(SurveyModel.OwnerId == owner_id)
    polls = poll_query.all()
    surveys = survey_query.all()

    # Query poll votes
    poll_ids = [p.Id for p in polls]
    transactions = db.query(VoteTransactionModel).filter(
        VoteTransactionModel.PollId.in_(poll_ids)
    ).all() if poll_ids else []
    transactions_by_poll = {}
    for t in transactions:
        transactions_by_poll.setdefault(t.PollId, []).append(t)

    # Query survey responses
    survey_ids = [s.Id for s in surveys]
    responses = db.query(SurveyResponseModel).filter(
        SurveyResponseModel.SurveyId.in_(survey_ids)
    ).all() if survey_ids else []
    responses_by_survey = {}
    for r in responses:
        responses_by_survey.setdefault(r.SurveyId, []).append({
            "timestamp": r.Timestamp,
            "respondent": r.VoterPseudonym,
            "county": getattr(r, "County", "Nairobi County") or "Nairobi County",
            "answers": json.loads(r.AnswersJson or "[]") if isinstance(r.AnswersJson, str) else []
        })

    total_registered_baseline = max(1000, (len(polls) + len(surveys)) * 2500)

    if export_format == "xlsx":
        data = build_turnout_xlsx(polls, surveys, transactions_by_poll, responses_by_survey, total_registered_baseline)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "icapsq-turnout-and-quotas-report.xlsx"
    elif export_format == "docx":
        data = build_turnout_docx(polls, surveys, transactions_by_poll, responses_by_survey, total_registered_baseline)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = "icapsq-turnout-and-quotas-report.docx"
    elif export_format == "csv":
        out = StringIO()
        writer = csv.writer(out)
        writer.writerow(["Type", "Campaign ID", "Campaign Title", "Category / Track", "Target Quota", "Ballots / Responses Cast", "Turnout Rate (%)", "Status"])
        for p in polls:
            cnt = len(transactions_by_poll.get(p.Id, []))
            target = getattr(p, "QuotaTarget", 2500) or 2500
            rate = f"{(cnt / target * 100):.1f}%" if target > 0 else "0.0%"
            status = "Target Met" if cnt >= target else "Active Ingestion"
            writer.writerow(["POLL", p.Id, p.Title, p.Category or "General", target, cnt, rate, status])
        for s in surveys:
            cnt = len(responses_by_survey.get(s.Id, []))
            target = getattr(s, "TargetQuota", 2500) or 2500
            rate = f"{(cnt / target * 100):.1f}%" if target > 0 else "0.0%"
            status = "Target Met" if cnt >= target else "Active Ingestion"
            writer.writerow(["SURVEY", s.Id, s.Title, s.Track or "General", target, cnt, rate, status])
        data = out.getvalue().encode("utf-8")
        media_type = "text/csv"
        filename = "icapsq-turnout-and-quotas-report.csv"
    elif export_format == "json":
        items = []
        for p in polls:
            cnt = len(transactions_by_poll.get(p.Id, []))
            target = getattr(p, "QuotaTarget", 2500) or 2500
            items.append({
                "type": "POLL", "id": p.Id, "title": p.Title, "category": p.Category,
                "targetQuota": target, "votesCast": cnt,
                "turnoutRate": round(cnt / target * 100, 1) if target > 0 else 0
            })
        for s in surveys:
            cnt = len(responses_by_survey.get(s.Id, []))
            target = getattr(s, "TargetQuota", 2500) or 2500
            items.append({
                "type": "SURVEY", "id": s.Id, "title": s.Title, "category": s.Track,
                "targetQuota": target, "responsesCast": cnt,
                "turnoutRate": round(cnt / target * 100, 1) if target > 0 else 0
            })
        data = json.dumps(items, indent=2).encode("utf-8")
        media_type = "application/json"
        filename = "icapsq-turnout-and-quotas-report.json"
    else:
        # Fallback to xlsx if format is pdf or unrecognized
        data = build_turnout_xlsx(polls, surveys, transactions_by_poll, responses_by_survey, total_registered_baseline)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "icapsq-turnout-and-quotas-report.xlsx"

    return StreamingResponse(
        BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
