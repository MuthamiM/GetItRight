from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.surveys.models import SurveyModel
from backend.api.features.surveys.schemas import (
    SurveyOut, SurveyCreate, SurveyResponseSubmission, SurveySubmissionReceipt,
    SurveyStatusUpdate, SurveyAnalyticsOut, ReceiptVerificationOut, SurveyResponseStatusOut
)
from backend.api.features.surveys.service import (
    list_surveys, get_survey_by_id, create_survey, submit_survey_response,
    update_survey_status, get_survey_analytics, verify_survey_receipt, get_survey_user_response
)
from backend.api.middleware.auth_middleware import (
    get_current_user_token,
    get_optional_current_user_token,
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

@router.get("/{survey_id}/responses")
def get_survey_responses(
    survey_id: str,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """Return survey interactions to the owner or an administrator."""
    from backend.api.features.surveys.models import SurveyResponseModel
    import json

    survey = db.query(SurveyModel).filter(SurveyModel.Id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    if current_user["role"] != "Admin" and survey.OwnerId != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this survey")
    responses = db.query(SurveyResponseModel).filter(
        SurveyResponseModel.SurveyId == survey_id
    ).order_by(SurveyResponseModel.Timestamp.desc()).all()
    return [{
        "id": response.Id,
        "surveyId": response.SurveyId,
        "userId": response.UserId,
        "respondent": response.VoterPseudonym,
        "answers": json.loads(response.AnswersJson or "[]"),
        "receiptHash": response.ReceiptHash,
        "timestamp": response.Timestamp,
    } for response in responses]

@router.get("/{survey_id}", response_model=SurveyOut)
def get_survey(survey_id: str, db: Session = Depends(get_db)):
    """Get single survey with full question and response breakdown."""
    return get_survey_by_id(db, survey_id)

@router.patch("/{survey_id}/status", response_model=SurveyOut)
def change_survey_status(
    survey_id: str,
    data: SurveyStatusUpdate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """Update survey operational status (Active, Paused, Closed)."""
    survey = get_survey_by_id(db, survey_id)
    if current_user["role"] != "Admin" and survey.ownerId != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this survey")
    return update_survey_status(db, survey_id, data.status)

@router.get("/{survey_id}/analytics", response_model=SurveyAnalyticsOut)
def fetch_survey_analytics(
    survey_id: str,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """Fetch detailed question breakdown, completion rates, and Merkle root."""
    survey = get_survey_by_id(db, survey_id)
    if current_user["role"] != "Admin" and survey.ownerId != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this survey")
    return get_survey_analytics(db, survey_id)

@router.get("/{survey_id}/verify-receipt/{receipt_hash}", response_model=ReceiptVerificationOut)
def verify_receipt_endpoint(survey_id: str, receipt_hash: str, db: Session = Depends(get_db)):
    """Cryptographically verify survey respondent ballot receipt against Merkle tree."""
    return verify_survey_receipt(db, survey_id, receipt_hash)

@router.post("", response_model=SurveyOut)
def create_new_survey(
    data: SurveyCreate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """Author and publish a new multi-step qualitative survey."""
    data.ownerId = current_user["sub"]
    data.plan = current_user["plan"]
    return create_survey(db, data)

@router.get("/{survey_id}/response-status", response_model=SurveyResponseStatusOut)
@router.get("/{survey_id}/status-check", response_model=SurveyResponseStatusOut)
def check_survey_user_status(
    survey_id: str,
    userId: Optional[str] = Query(None),
    voterKey: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db)
):
    """Check if the user/voter has already taken this survey and return previous action receipt."""
    import json
    resp = get_survey_user_response(db, survey_id, user_id=current_user["sub"] if current_user else None, voter_key=voterKey)
    if resp:
        try:
            answers = json.loads(resp.AnswersJson)
        except Exception:
            answers = []
        return SurveyResponseStatusOut(
            hasResponded=True,
            surveyId=survey_id,
            receiptHash=resp.ReceiptHash,
            merkleLeafIndex=resp.MerkleLeafIndex,
            timestamp=resp.Timestamp,
            answers=answers,
            userId=resp.UserId,
            voterPseudonym=resp.VoterPseudonym
        )
    return SurveyResponseStatusOut(
        hasResponded=False,
        surveyId=survey_id
    )

@router.post("/{survey_id}/respond", response_model=SurveySubmissionReceipt)
@router.post("/{survey_id}/submit", response_model=SurveySubmissionReceipt)
def answer_survey(
    survey_id: str,
    sub: SurveyResponseSubmission,
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db),
):
    """Submit responses to a survey with Merkle receipt generation."""
    sub.userId = current_user["sub"] if current_user else None
    if not sub.userId and not (sub.voterPseudonym and sub.voterPseudonym.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A respondent key or authenticated session is required")
    return submit_survey_response(db, survey_id, sub)
