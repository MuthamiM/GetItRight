from typing import Optional, List
import re
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.surveys.models import SurveyModel
from backend.api.features.surveys.schemas import (
    SurveyOut, SurveyCreate, SurveyResponseSubmission, SurveySubmissionReceipt,
    SurveyStatusUpdate, SurveyAnalyticsOut, ReceiptVerificationOut, SurveyResponseStatusOut,
    SurveyResponseStatusQuery
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


def _survey_export_records(db: Session, survey_ids: list[str], owner_id: str | None = None):
    import json
    from backend.api.features.surveys.models import SurveyResponseModel

    surveys = db.query(SurveyModel).filter(SurveyModel.Id.in_(survey_ids)).all()
    if owner_id is not None:
        surveys = [survey for survey in surveys if survey.OwnerId == owner_id]
    responses = db.query(SurveyResponseModel).filter(
        SurveyResponseModel.SurveyId.in_([survey.Id for survey in surveys])
    ).order_by(SurveyResponseModel.Timestamp.desc()).all() if surveys else []
    response_map = {}
    for response in responses:
        response_map.setdefault(response.SurveyId, []).append({
            "timestamp": response.Timestamp,
            "respondent": response.VoterPseudonym,
            "answers": json.loads(response.AnswersJson or "[]"),
        })
    return surveys, response_map


def _build_export(surveys, response_map, export_format: str):
    if export_format == "csv":
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Survey ID", "Survey Title", "Track", "Respondent", "County", "Timestamp", "Question", "Answer", "Status"])
        for survey in surveys:
            responses = response_map.get(survey.Id, [])
            if not responses:
                writer.writerow([survey.Id, survey.Title, survey.Track or "General", "No responses recorded", "", "", "", "", ""])
            else:
                for resp in responses:
                    ts = resp.get("timestamp", "")
                    respondent = resp.get("voterName") or resp.get("respondent", "")
                    county = resp.get("county", "Nairobi County")
                    answers = resp.get("answers", [])
                    if not answers:
                        writer.writerow([survey.Id, survey.Title, survey.Track or "General", respondent, county, ts, "None", "", "Verified & Confirmed"])
                    else:
                        for ans in answers:
                            if isinstance(ans, dict):
                                q = ans.get("questionId") or ans.get("question") or "Question"
                                a = ans.get("answer", "")
                                writer.writerow([survey.Id, survey.Title, survey.Track or "General", respondent, county, ts, q, a, "Verified & Confirmed"])
                            else:
                                writer.writerow([survey.Id, survey.Title, survey.Track or "General", respondent, county, ts, "Answer", str(ans), "Verified & Confirmed"])
        return output.getvalue().encode("utf-8"), "text/csv", "icapsq-survey-responses.csv"

    if export_format == "json":
        import json
        data = []
        for survey in surveys:
            responses = response_map.get(survey.Id, [])
            data.append({
                "surveyId": survey.Id,
                "title": survey.Title,
                "track": survey.Track,
                "status": survey.Status,
                "responseCount": len(responses),
                "responses": responses
            })
        return json.dumps(data, indent=2).encode("utf-8"), "application/json", "icapsq-survey-responses.json"

    if not surveys:
        from backend.api.core.report_builder import build_empty_report
        extensions = {
            "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "icapsq-survey-report.xlsx"),
            "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "icapsq-survey-report.docx"),
            "pdf": ("application/pdf", "icapsq-survey-report.pdf"),
        }
        media_type, filename = extensions[export_format]
        content = build_empty_report("Survey response report", "No surveys are available to export for this account.", export_format)
        return content, media_type, filename

    from backend.api.core.report_builder import build_survey_docx, build_survey_xlsx, build_survey_pdf

    if surveys:
        first_survey = surveys[0]
        responses = response_map.get(first_survey.Id, [])
        if export_format == "xlsx":
            return build_survey_xlsx(first_survey, responses), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "icapsq-survey-report.xlsx"
        if export_format == "docx":
            return build_survey_docx(first_survey, responses), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "icapsq-survey-report.docx"
        return build_survey_pdf(first_survey, responses), "application/pdf", "icapsq-survey-report.pdf"

    raise ValueError(f"Unsupported survey export format: {export_format}")

@router.get("", response_model=List[SurveyOut])
def get_all_surveys(
    plan: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    include_all: Optional[bool] = Query(False),
    db: Session = Depends(get_db)
):
    """Fetch surveys optionally filtered by plan and status."""
    return list_surveys(db, plan=plan, status=status, include_all=include_all)

@router.get("/templates")
def survey_templates_from_surveys():
    """Returns pre-built survey templates for the creation wizard (alias route)."""
    from backend.api.features.analytics.routes import survey_templates
    return survey_templates()


@router.get("/exports/responses")
def export_all_survey_responses(
    export_format: str = Query("pdf", alias="format", pattern="^(pdf|docx|xlsx|csv|json)$"),
    owner_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    if current_user["role"] not in ["Admin", "Super Admin"]:
        owner_id = current_user["sub"]
    query = db.query(SurveyModel)
    if owner_id:
        query = query.filter(SurveyModel.OwnerId == owner_id)
    surveys = query.all()
    surveys, response_map = _survey_export_records(db, [survey.Id for survey in surveys], owner_id=owner_id)
    data, media_type, filename = _build_export(surveys, response_map, export_format)
    return StreamingResponse(BytesIO(data), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{survey_id}/export")
def export_survey_responses(
    survey_id: str,
    export_format: str = Query("pdf", alias="format", pattern="^(pdf|docx|xlsx|csv|json)$"),
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    survey = db.query(SurveyModel).filter(SurveyModel.Id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    if current_user["role"] not in ["Admin", "Super Admin"] and survey.OwnerId != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this survey")
    surveys, response_map = _survey_export_records(db, [survey_id])
    data, media_type, filename = _build_export(surveys, response_map, export_format)
    return StreamingResponse(BytesIO(data), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})

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
    is_admin = current_user.get("role") in ["Admin", "Super Admin"]
    if not is_admin and (survey.OwnerId or "").lower() != (current_user.get("sub") or "").lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this survey")
    responses = db.query(SurveyResponseModel).filter(
        SurveyResponseModel.SurveyId == survey_id
    ).order_by(SurveyResponseModel.Timestamp.desc()).all()
    return [{
        "id": response.Id,
        "surveyId": response.SurveyId,
        "userId": response.UserId,
        "respondent": response.VoterPseudonym,
        "answers": json.loads(response.AnswersJson or "[]") if isinstance(response.AnswersJson, str) else (response.AnswersJson or []),
        "receiptHash": response.ReceiptHash,
        "timestamp": response.Timestamp,
        "voterName": getattr(response, "VoterName", None),
        "voterIdNumber": getattr(response, "VoterIdNumber", None),
        "deviceName": getattr(response, "DeviceName", None),
        "deviceOS": getattr(response, "DeviceOS", None),
        "county": getattr(response, "County", None),
        # Keep precise coordinates available to internal validation only.
        "latitude": None,
        "longitude": None,
        "gpsCoordinates": None,
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


@router.post("/{survey_id}/response-status", response_model=SurveyResponseStatusOut)
def check_survey_user_status_by_identity(
    survey_id: str,
    identity: SurveyResponseStatusQuery,
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db),
):
    """Check completion using private JSON fields so voter IDs never enter URLs or access logs."""
    import json

    voter_id_number = (identity.voterIdNumber or "").strip()
    if voter_id_number and not re.fullmatch(r"\d{5,12}", voter_id_number):
        voter_id_number = None
    resp = get_survey_user_response(
        db,
        survey_id,
        user_id=current_user["sub"] if current_user else None,
        voter_key=identity.voterKey,
        voter_id_number=voter_id_number,
    )
    if not resp:
        return SurveyResponseStatusOut(hasResponded=False, surveyId=survey_id)
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
        voterPseudonym=resp.VoterPseudonym,
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
    if current_user:
        sub.userId = current_user["sub"]
    else:
        # Never turn a county into an account ID: that made every anonymous
        # respondent in one county collide on the same identity claim.
        sub.userId = None
    if not sub.voterPseudonym:
        import uuid
        sub.voterPseudonym = f"VISITOR-{uuid.uuid4().hex}"
    return submit_survey_response(db, survey_id, sub)
