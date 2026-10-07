from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.analytics.schemas import (
    TrackingTelemetryOut, StatsOut, StationOut, AnomalyOut, DisputeOut,
    CheckpointOut, ObserverOut, LedgerBlockOut, AuditLogOut,
    AdminDashboardStatsOut, CustomerDashboardStatsOut, SurveyTemplateOut
)
from backend.api.features.analytics.service import (
    get_tracking_telemetry, get_stats, list_stations, get_station_by_code,
    list_anomalies, list_disputes, list_checkpoints, list_observers,
    list_ledger, list_audit, get_admin_dashboard_stats, get_customer_dashboard_stats
)

router = APIRouter(tags=["Analytics & Cryptographic Telemetry"])

@router.get("/admin/dashboard-stats", response_model=AdminDashboardStatsOut)
def admin_dashboard_stats(db: Session = Depends(get_db)):
    """Aggregated admin dashboard stats — all KPIs, charts, and recent voters from DB."""
    return get_admin_dashboard_stats(db)

@router.get("/customer/dashboard-stats/{user_id}", response_model=CustomerDashboardStatsOut)
def customer_dashboard_stats(user_id: str, db: Session = Depends(get_db)):
    """User-scoped dashboard stats — polls, votes, quotas, charts from DB."""
    return get_customer_dashboard_stats(db, user_id)

@router.get("/surveys/templates", response_model=List[SurveyTemplateOut])
def survey_templates():
    """Returns pre-built survey templates for the creation wizard."""
    from backend.api.features.analytics.schemas import SurveyTemplateQuestionOut
    templates = [
        SurveyTemplateOut(
            id="tmpl-nps", name="Customer Satisfaction (NPS)",
            description="Measure Net Promoter Score and customer happiness with targeted feedback questions.",
            category="Enterprise Feedback", icon="⭐",
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
            category="Enterprise Feedback", icon="👥",
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
            category="Product Roadmap", icon="🚀",
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
            category="Civic Priority", icon="🏛️",
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
            category="General", icon="🎪",
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
            category="Enterprise Feedback", icon="📊",
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
def admin_tracking_telemetry(db: Session = Depends(get_db)):
    """Fetch live aggregate platform telemetry and real vote distribution across plans."""
    return get_tracking_telemetry(db)

@router.get("/stats", response_model=StatsOut)
def platform_stats(db: Session = Depends(get_db)):
    """Fetch real-time cluster metrics, ingestion velocity, latency, and reporting stations."""
    return get_stats(db)

@router.get("/stations", response_model=List[StationOut])
def stations_list(db: Session = Depends(get_db)):
    """Fetch all 250 physical polling stations with turnout percentages and cryptographic observer hashes."""
    return list_stations(db)

@router.get("/stations/{code}", response_model=StationOut)
def station_detail(code: str, db: Session = Depends(get_db)):
    """Fetch specific station telemetry and Form 34A hash."""
    return get_station_by_code(db, code)

@router.get("/anomalies", response_model=List[AnomalyOut])
def anomalies_list(db: Session = Depends(get_db)):
    """Fetch active anomaly detection flags."""
    return list_anomalies(db)

@router.get("/disputes", response_model=List[DisputeOut])
def disputes_list(db: Session = Depends(get_db)):
    """Fetch dual-observer dispute reconciliations."""
    return list_disputes(db)

@router.post("/disputes/{id}/resolve")
def resolve_dispute_endpoint(id: str, db: Session = Depends(get_db)):
    """Resolve dual observer variance and mark polling station as verified."""
    from backend.api.features.analytics.service import resolve_dispute
    return resolve_dispute(db, id)

@router.get("/checkpoints", response_model=List[CheckpointOut])
def checkpoints_list(db: Session = Depends(get_db)):
    """Fetch Bitcoin blockchain anchored state checkpoints."""
    return list_checkpoints(db)

@router.post("/checkpoints/publish", response_model=CheckpointOut)
def publish_checkpoint_endpoint(db: Session = Depends(get_db)):
    """Anchor current ledger state to Bitcoin blockchain."""
    from backend.api.features.analytics.service import publish_checkpoint
    return publish_checkpoint(db)

@router.get("/observers", response_model=List[ObserverOut])
def observers_list(db: Session = Depends(get_db)):
    """Fetch hardware observers and cryptographic public keys."""
    return list_observers(db)

@router.get("/ledger", response_model=List[LedgerBlockOut])
def ledger_blocks(db: Session = Depends(get_db)):
    """Fetch verifiable cryptographic ledger blocks."""
    return list_ledger(db)

@router.get("/audit", response_model=List[AuditLogOut])
def audit_logs(db: Session = Depends(get_db)):
    """Fetch cryptographic audit trail signatures."""
    return list_audit(db)
