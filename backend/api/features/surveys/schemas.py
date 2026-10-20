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
    endDate: Optional[str] = None
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
    endDate: Optional[str] = None
    durationHours: Optional[int] = None
    questions: List[QuestionCreate]

class SurveyAnswerSubmission(BaseModel):
    questionId: Any
    answer: Any

class SurveyResponseSubmission(BaseModel):
    voterPseudonym: Optional[str] = None
    userId: Optional[str] = None
    answers: List[SurveyAnswerSubmission]
    voterName: Optional[str] = None
    voterIdNumber: Optional[str] = None
    deviceName: Optional[str] = None
    deviceOS: Optional[str] = None
    county: Optional[str] = None
    dob: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None

class SurveySubmissionReceipt(BaseModel):
    success: bool
    surveyId: str
    receiptHash: str
    merkleLeafIndex: int
    timestamp: str
    userId: Optional[str] = None

class SurveyResponseStatusOut(BaseModel):
    hasResponded: bool
    surveyId: str
    receiptHash: Optional[str] = None
    merkleLeafIndex: Optional[int] = None
    timestamp: Optional[str] = None
    answers: Optional[List[Any]] = None
    userId: Optional[str] = None
    voterPseudonym: Optional[str] = None


class SurveyStatusUpdate(BaseModel):
    status: str

class QuestionAnalytics(BaseModel):
    questionId: int
    index: int
    questionText: str
    questionType: str
    totalAnswers: int
    breakdown: Dict[str, Any]

class SurveyAnalyticsOut(BaseModel):
    surveyId: str
    title: str
    status: str
    plan: str
    targetResponses: int
    totalResponses: int
    completionRate: float
    merkleCohortRoot: str
    questions: List[QuestionAnalytics]

class ReceiptVerificationOut(BaseModel):
    valid: bool
    surveyId: str
    receiptHash: str
    merkleLeafIndex: int
    timestamp: str
    merkleCohortRoot: str
