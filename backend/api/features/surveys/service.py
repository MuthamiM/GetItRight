import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, List
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status
from backend.api.features.surveys.models import SurveyModel, SurveyQuestionModel, SurveyResponseModel
from backend.api.features.surveys.schemas import (
    SurveyOut, QuestionOut, SurveyCreate, SurveyResponseSubmission, SurveySubmissionReceipt
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

    new_survey = SurveyModel(
        Id=new_id,
        Title=data.title.strip(),
        Description=data.description.strip() if data.description else "",
        Track=data.track or "General",
        Plan=plan_key,
        Status="Active",
        TargetResponses=data.targetResponses or 500,
        TotalResponses=0,
        CreatedAt=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        OwnerId=data.ownerId or "USR-001",
        MerkleCohortRoot=root,
        TargetAudience=data.targetAudience or "General Public",
        OrganizationName=data.organizationName or "Verified Civic Publisher"
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

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    voter = sub.voterPseudonym or f"Respondent-{uuid.uuid4().hex[:6]}"
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

    # Save individual response
    resp_record = SurveyResponseModel(
        SurveyId=survey_id,
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
        timestamp=timestamp
    )
