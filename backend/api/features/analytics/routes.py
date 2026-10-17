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

