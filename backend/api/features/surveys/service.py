import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, List
# pyrefly: ignore [missing-import]
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status
from backend.api.features.surveys.models import SurveyModel, SurveyQuestionModel, SurveyResponseModel
from backend.api.features.auth.models import UserModel
from backend.api.features.surveys.schemas import (
    SurveyOut, QuestionOut, SurveyCreate, SurveyResponseSubmission, SurveySubmissionReceipt,
    SurveyAnalyticsOut, QuestionAnalytics, ReceiptVerificationOut
)
from backend.api.core.voter_verification import validate_voter_details
from backend.api.core.ballot_claims import reserve_ballot_identities


def _plain_text(value: str, field: str, maximum: int) -> str:
    clean = (value or "").strip()
    if not clean or len(clean) > maximum or any(char in clean for char in "<>"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field} must be plain text and no longer than {maximum} characters",
        )
    return clean

def map_survey_to_out(s: SurveyModel) -> SurveyOut:
    questions_sorted = sorted(s.questions, key=lambda q: q.Index)
    q_outs = []
    for q in questions_sorted:
        options = []
        try:
            options = json.loads(q.OptionsJson) if q.OptionsJson else []
        except Exception:
            options = []

        responses = {}
        try:
            responses = json.loads(q.ResponsesJson) if q.ResponsesJson else {}
        except Exception:
            responses = {}

        q_outs.append(QuestionOut(
            id=q.Id,
            surveyId=q.SurveyId,
            index=q.Index,
            questionText=q.QuestionText,
            questionType=q.QuestionType,
            options=options,
            responsesCount=responses
        ))

    return SurveyOut(
        id=s.Id,
        title=s.Title,
        description=s.Description,
        track=s.Track,
        plan=s.Plan,
        status=s.Status,
        targetResponses=s.TargetResponses,
        totalResponses=s.TotalResponses,
        createdAt=s.CreatedAt,
        ownerId=s.OwnerId,
        merkleCohortRoot=s.MerkleCohortRoot,
        targetAudience=s.TargetAudience or "General Public",
        organizationName=s.OrganizationName or "Verified Civic Publisher",
        endDate=getattr(s, 'EndDate', None),
        questions=q_outs
    )

def list_surveys(db: Session, plan: Optional[str] = None, status: Optional[str] = None, include_all: bool = False) -> List[SurveyOut]:
    query = db.query(SurveyModel)
    if not include_all:
        if status:
            query = query.filter(SurveyModel.Status.ilike(status))
        else:
            query = query.filter(SurveyModel.Status.in_(["active", "Active"]))
    elif status and status.lower() != "all":
        query = query.filter(SurveyModel.Status.ilike(status))
    if plan:
        query = query.filter(SurveyModel.Plan == plan.lower())
    surveys = query.all()
    surveys_sorted = sorted(surveys, key=lambda s: (1 if str(s.Status).lower() in ["active", "live"] else 0, s.CreatedAt or ""), reverse=True)
    return [map_survey_to_out(s) for s in surveys_sorted]

def get_survey_by_id(db: Session, survey_id: str) -> SurveyOut:
    survey = db.query(SurveyModel).filter(SurveyModel.Id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Survey {survey_id} not found")
    return map_survey_to_out(survey)

def create_survey(db: Session, data: SurveyCreate) -> SurveyOut:
    if not data.questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey must have at least one question")
    title = _plain_text(data.title, "Survey title", 200)
    if len(title) < 3:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Survey title must be at least 3 characters")
    description = _plain_text(data.description, "Survey description", 2_000) if data.description else ""
    track = _plain_text(data.track, "Survey track", 100) if data.track else "General"
    if len(data.questions) > 50:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A survey may contain at most 50 questions")

    owner_id = (data.ownerId or "").strip()
    owner = db.query(UserModel).filter(UserModel.Id == owner_id).first()
    if not owner or owner.Status != "Active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active survey owner required")
    plan_key = (owner.Plan or data.plan or "pro").lower()
    new_id = f"SRV-{plan_key.upper()[:4]}-{uuid.uuid4().hex[:4].upper()}"
    root = "0x" + hashlib.sha256(f"{new_id}:{data.title}".encode("utf-8")).hexdigest()[:16]

    now = datetime.now(timezone.utc)
    if data.endDate:
        end_date_str = data.endDate
    elif data.durationHours:
        from datetime import timedelta
        end_date_str = (now + timedelta(hours=data.durationHours)).strftime("%Y-%m-%d %H:%M:%S")
    else:
        from datetime import timedelta
        end_date_str = (now + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

    new_survey = SurveyModel(
        Id=new_id,
        Title=title,
        Description=description,
        Track=track,
        Plan=plan_key,
        Status="Active",
        TargetResponses=data.targetResponses or 500,
        TotalResponses=0,
        CreatedAt=now.strftime("%Y-%m-%d %H:%M"),
        OwnerId=owner_id,
        MerkleCohortRoot=root,
        TargetAudience=_plain_text(data.targetAudience, "Target audience", 100) if data.targetAudience else "General Public",
        OrganizationName=_plain_text(data.organizationName, "Organization name", 200) if data.organizationName else "Verified Civic Publisher",
        EndDate=end_date_str
    )
    db.add(new_survey)
    db.flush()

    for idx, q_data in enumerate(data.questions):
        q = SurveyQuestionModel(
            SurveyId=new_id,
            Index=idx,
            QuestionText=_plain_text(q_data.questionText, "Question text", 500),
            QuestionType=q_data.questionType or "choice",
            OptionsJson=json.dumps([_plain_text(option, "Question option", 200) for option in (q_data.options or [])]),
            ResponsesJson=json.dumps({})
        )
        db.add(q)

    db.commit()
    db.refresh(new_survey)
    return map_survey_to_out(new_survey)

def submit_survey_response(db: Session, survey_id: str, sub: SurveyResponseSubmission) -> SurveySubmissionReceipt:
    survey = db.query(SurveyModel).filter(SurveyModel.Id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Survey {survey_id} not found")
    if (survey.Status or "").lower() != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This survey is not accepting responses")
    if survey.EndDate:
        try:
            end_at = datetime.fromisoformat(survey.EndDate.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
            if end_at <= datetime.now(timezone.utc):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This survey has ended")
        except ValueError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This survey has an invalid closing time")
    if not sub.answers or len(sub.answers) > len(survey.questions):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Survey answers are incomplete or invalid")
    valid_question_ids = {q.Id for q in survey.questions}
    submitted_question_ids = [answer.questionId for answer in sub.answers]
    if len(submitted_question_ids) != len(set(submitted_question_ids)) or any(qid not in valid_question_ids for qid in submitted_question_ids):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Survey answers contain invalid questions")
    if set(submitted_question_ids) != valid_question_ids or any(
        answer.answer is None or not str(answer.answer).strip() for answer in sub.answers
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: answer every survey question before submitting.",
        )

    voter_name, voter_id_num = validate_voter_details(
        voter_name=sub.voterName,
        voter_id_number=sub.voterIdNumber,
        county=sub.county,
        dob=sub.dob,
        latitude=sub.latitude,
        longitude=sub.longitude,
        accuracy=sub.accuracy,
    )
    duplicate_identity_filters = [SurveyResponseModel.VoterIdNumber == voter_id_num]
    if sub.userId and sub.userId.strip():
        duplicate_identity_filters.append(SurveyResponseModel.UserId == sub.userId.strip())
    existing_response = db.query(SurveyResponseModel).filter(
        SurveyResponseModel.SurveyId == survey.Id,
        or_(*duplicate_identity_filters),
    ).first()
    if existing_response:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted a response to this survey with this National ID.",
        )

    try:
        reserve_ballot_identities(
            db,
            "survey",
            survey.Id,
            [
                ("national_id", voter_id_num),
                ("account_id", sub.userId),
                ("voter_key", sub.voterPseudonym),
            ],
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted a response to this survey with this National ID.",
        )

    user_id = sub.userId.strip() if sub.userId and str(sub.userId).strip() else None
    loc_tag = (sub.county or "LOCATION1").replace(" ", "").upper()
    voter = (sub.voterPseudonym or f"USER@{loc_tag}-{uuid.uuid4().hex[:6].upper()}").strip()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    receipt = "0x" + hashlib.sha256(f"{survey_id}:{voter}:{timestamp}".encode("utf-8")).hexdigest()

    survey.TotalResponses += 1
    leaf_index = survey.TotalResponses

    # Update question response counts
    answers_dict = {a.questionId: a.answer for a in sub.answers}
    for q in survey.questions:
        if q.Id in answers_dict:
            try:
                resp_map = json.loads(q.ResponsesJson) if q.ResponsesJson else {}
            except Exception:
                resp_map = {}
            ans_str = str(answers_dict[q.Id])
            resp_map[ans_str] = resp_map.get(ans_str, 0) + 1
            q.ResponsesJson = json.dumps(resp_map)

    gps_coords = None
    if sub.latitude is not None and sub.longitude is not None:
        gps_coords = f"{sub.latitude},{sub.longitude}"

    # Save individual response with UserId in DB
    resp_record = SurveyResponseModel(
        SurveyId=survey_id,
        UserId=user_id,
        VoterPseudonym=voter,
        AnswersJson=json.dumps([{ "questionId": a.questionId, "answer": a.answer } for a in sub.answers]),
        ReceiptHash=receipt,
        MerkleLeafIndex=leaf_index,
        Timestamp=timestamp,
        VoterName=voter_name,
        VoterIdNumber=voter_id_num,
        Dob=(sub.dob or "").strip(),
        DeviceName=(sub.deviceName or "Web Browser").strip() or None,
        DeviceOS=(sub.deviceOS or "").strip() or None,
        County=(sub.county or "").strip() or None,
        Latitude=sub.latitude,
        Longitude=sub.longitude,
        Accuracy=sub.accuracy,
        GpsCoordinates=gps_coords
    )
    db.add(resp_record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted a response to this survey with this National ID.",
        )

    return SurveySubmissionReceipt(
        success=True,
        surveyId=survey_id,
        receiptHash=receipt,
        merkleLeafIndex=leaf_index,
        timestamp=timestamp,
        userId=user_id
    )

def get_survey_user_response(db: Session, survey_id: str, user_id: Optional[str] = None, voter_key: Optional[str] = None, voter_id_number: Optional[str] = None):
    query = db.query(SurveyResponseModel).filter(SurveyResponseModel.SurveyId == survey_id)
    u_id = user_id.strip() if user_id and str(user_id).strip() else None
    v_key = voter_key.strip() if voter_key and str(voter_key).strip() else None
    id_number = voter_id_number.strip() if voter_id_number and str(voter_id_number).strip() else None
    identity_filters = []
    if u_id:
        identity_filters.append(SurveyResponseModel.UserId == u_id)
    if v_key:
        identity_filters.append(SurveyResponseModel.VoterPseudonym == v_key)
    if id_number:
        identity_filters.append(SurveyResponseModel.VoterIdNumber == id_number)

    if not identity_filters:
        return None
    return query.filter(or_(*identity_filters)).order_by(SurveyResponseModel.Id.desc()).first()


def update_survey_status(db: Session, survey_id: str, new_status: str) -> SurveyOut:
    survey = db.query(SurveyModel).filter(SurveyModel.Id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Survey {survey_id} not found")
    valid_statuses = ["Active", "Paused", "Closed"]
    formatted = next((s for s in valid_statuses if s.lower() == new_status.strip().lower()), new_status.capitalize())
    survey.Status = formatted
    db.commit()
    db.refresh(survey)
    return map_survey_to_out(survey)

def get_survey_analytics(db: Session, survey_id: str) -> SurveyAnalyticsOut:
    survey = db.query(SurveyModel).filter(SurveyModel.Id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Survey {survey_id} not found")
    
    questions_sorted = sorted(survey.questions, key=lambda q: q.Index)
    analytics_questions = []
    
    for q in questions_sorted:
        resp_map = {}
        try:
            resp_map = json.loads(q.ResponsesJson) if q.ResponsesJson else {}
        except Exception:
            resp_map = {}
        total_answers = sum(resp_map.values()) if isinstance(resp_map, dict) else 0
        analytics_questions.append(QuestionAnalytics(
            questionId=q.Id,
            index=q.Index,
            questionText=q.QuestionText,
            questionType=q.QuestionType,
            totalAnswers=total_answers,
            breakdown=resp_map
        ))
    
    comp_rate = round((survey.TotalResponses / survey.TargetResponses) * 100.0, 1) if survey.TargetResponses > 0 else 0.0
    
    return SurveyAnalyticsOut(
        surveyId=survey.Id,
        title=survey.Title,
        status=survey.Status,
        plan=survey.Plan,
        targetResponses=survey.TargetResponses,
        totalResponses=survey.TotalResponses,
        completionRate=min(comp_rate, 100.0),
        merkleCohortRoot=survey.MerkleCohortRoot,
        questions=analytics_questions
    )

def verify_survey_receipt(db: Session, survey_id: str, receipt_hash: str) -> ReceiptVerificationOut:
    survey = db.query(SurveyModel).filter(SurveyModel.Id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Survey {survey_id} not found")
    
    resp = db.query(SurveyResponseModel).filter(
        SurveyResponseModel.SurveyId == survey_id,
        SurveyResponseModel.ReceiptHash == receipt_hash.strip()
    ).first()
    
    if not resp:
        return ReceiptVerificationOut(
            valid=False,
            surveyId=survey_id,
            receiptHash=receipt_hash,
            merkleLeafIndex=0,
            timestamp="",
            merkleCohortRoot=survey.MerkleCohortRoot
        )
    
    return ReceiptVerificationOut(
        valid=True,
        surveyId=survey_id,
        receiptHash=resp.ReceiptHash,
        merkleLeafIndex=resp.MerkleLeafIndex,
        timestamp=resp.Timestamp,
        merkleCohortRoot=survey.MerkleCohortRoot
    )
