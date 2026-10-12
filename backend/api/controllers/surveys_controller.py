from typing import Optional, List
from sqlalchemy.orm import Session

from backend.api.features.surveys.schemas import (
    SurveyOut, SurveyCreate, SurveyResponseSubmission,
    SurveySubmissionReceipt, SurveyAnalyticsOut, SurveyStatusUpdate,
    ReceiptVerificationOut
)
from backend.api.features.surveys import service as surveys_service

class SurveysController:
    """Controller for surveys, census questionnaires, and response analytics."""

    @staticmethod
    def get_surveys(db: Session, plan: Optional[str] = None) -> List[SurveyOut]:
        return surveys_service.get_all_surveys(db, plan=plan)

    @staticmethod
    def get_survey(db: Session, survey_id: str) -> SurveyOut:
        return surveys_service.get_survey_by_id(db, survey_id)

    @staticmethod
    def create_survey(db: Session, data: SurveyCreate) -> SurveyOut:
        return surveys_service.create_survey(db, data)

    @staticmethod
    def change_status(db: Session, survey_id: str, data: SurveyStatusUpdate) -> SurveyOut:
        return surveys_service.update_survey_status(db, survey_id, data)

    @staticmethod
    def submit_response(db: Session, survey_id: str, sub: SurveyResponseSubmission) -> SurveySubmissionReceipt:
        return surveys_service.submit_survey_response(db, survey_id, sub)

    @staticmethod
    def get_analytics(db: Session, survey_id: str) -> SurveyAnalyticsOut:
        return surveys_service.get_survey_analytics(db, survey_id)

    @staticmethod
    def verify_receipt(db: Session, survey_id: str, receipt_hash: str) -> ReceiptVerificationOut:
        return surveys_service.verify_survey_receipt(db, survey_id, receipt_hash)
