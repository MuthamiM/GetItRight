import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, List
# pyrefly: ignore [missing-import]
from sqlalchemy import or_
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status
from backend.api.features.surveys.models import SurveyModel, SurveyQuestionModel, SurveyResponseModel
from backend.api.features.surveys.schemas import (
    SurveyOut, QuestionOut, SurveyCreate, SurveyResponseSubmission, SurveySubmissionReceipt,
    SurveyAnalyticsOut, QuestionAnalytics, ReceiptVerificationOut
)

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

def list_surveys(db: Session, plan: Optional[str] = None) -> List[SurveyOut]:
    query = db.query(SurveyModel)
    if plan:
        query = query.filter(SurveyModel.Plan == plan.lower())
    surveys = query.all()
    return [map_survey_to_out(s) for s in surveys]

def get_survey_by_id(db: Session, survey_id: str) -> SurveyOut:
    survey = db.query(SurveyModel).filter(SurveyModel.Id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Survey {survey_id} not found")
    return map_survey_to_out(survey)

def create_survey(db: Session, data: SurveyCreate) -> SurveyOut:
    if not data.questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey must have at least one question")

    plan_key = (data.plan or "free").lower()
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
        Title=data.title.strip(),
        Description=data.description.strip() if data.description else "",
        Track=data.track or "General",
        Plan=plan_key,
        Status="Active",
        TargetResponses=data.targetResponses or 500,
        TotalResponses=0,
        CreatedAt=now.strftime("%Y-%m-%d %H:%M"),
        OwnerId=data.ownerId or "USR-001",
        MerkleCohortRoot=root,
        TargetAudience=data.targetAudience or "General Public",
        OrganizationName=data.organizationName or "Verified Civic Publisher",
        EndDate=end_date_str
    )
    db.add(new_survey)
    db.flush()

    for idx, q_data in enumerate(data.questions):
        q = SurveyQuestionModel(
            SurveyId=new_id,
            Index=idx,
            QuestionText=q_data.questionText.strip(),
            QuestionType=q_data.questionType or "choice",
            OptionsJson=json.dumps(q_data.options or []),
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

    user_id = sub.userId.strip() if sub.userId and str(sub.userId).strip() else None
    voter = (sub.voterPseudonym or (f"User-{user_id}" if user_id else f"Respondent-{uuid.uuid4().hex[:6]}")).strip()

    # NO RETAKING SURVEY: If user already completed survey, reject duplicate submission
    if user_id:
        existing_by_user = db.query(SurveyResponseModel).filter(
            SurveyResponseModel.SurveyId == survey_id,
            SurveyResponseModel.UserId == user_id
        ).first()
        if existing_by_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already completed this survey."
            )

    # NO RETAKING SURVEY: If voter pseudonym/session already submitted, reject duplicate
    if voter:
        existing_by_voter = db.query(SurveyResponseModel).filter(
            SurveyResponseModel.SurveyId == survey_id,
            SurveyResponseModel.VoterPseudonym == voter
        ).first()
        if existing_by_voter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already completed this survey."
            )

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

    # Save individual response with UserId in DB
    resp_record = SurveyResponseModel(
        SurveyId=survey_id,
        UserId=user_id,
        VoterPseudonym=voter,
        AnswersJson=json.dumps([{ "questionId": a.questionId, "answer": a.answer } for a in sub.answers]),
        ReceiptHash=receipt,
        MerkleLeafIndex=leaf_index,
        Timestamp=timestamp
    )
    db.add(resp_record)
    db.commit()

    return SurveySubmissionReceipt(
        success=True,
        surveyId=survey_id,
        receiptHash=receipt,
        merkleLeafIndex=leaf_index,
        timestamp=timestamp,
        userId=user_id
    )

def get_survey_user_response(db: Session, survey_id: str, user_id: Optional[str] = None, voter_key: Optional[str] = None):
    query = db.query(SurveyResponseModel).filter(SurveyResponseModel.SurveyId == survey_id)
    u_id = user_id.strip() if user_id and str(user_id).strip() else None
    v_key = voter_key.strip() if voter_key and str(voter_key).strip() else None

    if u_id and v_key:
        query = query.filter(or_(SurveyResponseModel.UserId == u_id, SurveyResponseModel.VoterPseudonym == v_key))
    elif u_id:
        query = query.filter(SurveyResponseModel.UserId == u_id)
    elif v_key:
        query = query.filter(SurveyResponseModel.VoterPseudonym == v_key)
    else:
        return None
    return query.first()


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
