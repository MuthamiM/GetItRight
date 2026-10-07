from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.surveys.schemas import (
    SurveyOut, SurveyCreate, SurveyResponseSubmission, SurveySubmissionReceipt
)
from backend.api.features.surveys.service import (
    list_surveys, get_survey_by_id, create_survey, submit_survey_response
)

router = APIRouter(prefix="/surveys", tags=["Surveys"])

@router.get("", response_model=List[SurveyOut])
def get_all_surveys(plan: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Fetch surveys optionally filtered by plan."""
    return list_surveys(db, plan)

@router.get("/templates")
def survey_templates_from_surveys():
    """Returns pre-built survey templates for the creation wizard (alias route)."""
    from backend.api.features.analytics.routes import survey_templates
    return survey_templates()

@router.get("/{survey_id}", response_model=SurveyOut)
def get_survey(survey_id: str, db: Session = Depends(get_db)):
    """Get single survey with full question and response breakdown."""
    return get_survey_by_id(db, survey_id)

@router.post("", response_model=SurveyOut)
def create_new_survey(data: SurveyCreate, db: Session = Depends(get_db)):
    """Author and publish a new multi-step qualitative survey."""
    return create_survey(db, data)

@router.post("/{survey_id}/respond", response_model=SurveySubmissionReceipt)
@router.post("/{survey_id}/submit", response_model=SurveySubmissionReceipt)
def answer_survey(survey_id: str, sub: SurveyResponseSubmission, db: Session = Depends(get_db)):
    """Submit responses to a survey with Merkle receipt generation."""
    return submit_survey_response(db, survey_id, sub)
