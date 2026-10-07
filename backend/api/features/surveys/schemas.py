import json
from typing import Optional, List, Any, Dict
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

class QuestionOut(BaseModel):
    id: int
    surveyId: str
    index: int
    questionText: str
    questionType: str
    options: List[str] = []
    responsesCount: Optional[Dict[str, Any]] = None

class SurveyOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    track: Optional[str]
    plan: str
    status: str
    targetResponses: int
    totalResponses: int
    createdAt: str
    ownerId: str
    merkleCohortRoot: str
    targetAudience: Optional[str] = "General Public"
    organizationName: Optional[str] = "Verified Civic Publisher"
    questions: List[QuestionOut] = []

class QuestionCreate(BaseModel):
    questionText: str
    questionType: Optional[str] = "choice"
    options: Optional[List[str]] = []

class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    track: Optional[str] = "General"
    plan: Optional[str] = "free"
    targetResponses: Optional[int] = 500
    ownerId: Optional[str] = "USR-001"
    targetAudience: Optional[str] = "General Public"
    organizationName: Optional[str] = "Verified Civic Publisher"
    questions: List[QuestionCreate]

class SurveyAnswerSubmission(BaseModel):
    questionId: int
    answer: Any

class SurveyResponseSubmission(BaseModel):
    voterPseudonym: Optional[str] = None
    answers: List[SurveyAnswerSubmission]

class SurveySubmissionReceipt(BaseModel):
    success: bool
    surveyId: str
    receiptHash: str
    merkleLeafIndex: int
    timestamp: str
