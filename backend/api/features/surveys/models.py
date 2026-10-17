from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.api.core.database import Base

class SurveyModel(Base):
    __tablename__ = "Surveys"
    __table_args__ = {"extend_existing": True}

    Id = Column(String, primary_key=True, index=True)
    Title = Column(String, nullable=False)
    Description = Column(String, nullable=True)
    Track = Column(String, nullable=True)
    Plan = Column(String, nullable=False, index=True, default="free")
    Status = Column(String, nullable=False, default="Active")
    TargetResponses = Column(Integer, default=100)
    TotalResponses = Column(Integer, default=0)
    CreatedAt = Column(String, nullable=False)
    OwnerId = Column(String, nullable=False)
    MerkleCohortRoot = Column(String, nullable=False)
    TargetAudience = Column(String, nullable=True, default="General Public")
    OrganizationName = Column(String, nullable=True, default="Verified Civic Publisher")
    EndDate = Column(String, nullable=True)

    questions = relationship("SurveyQuestionModel", back_populates="survey", cascade="all, delete-orphan", lazy="joined")

class SurveyQuestionModel(Base):
    __tablename__ = "SurveyQuestions"
    __table_args__ = {"extend_existing": True}

    Id = Column(Integer, primary_key=True, autoincrement=True)
    SurveyId = Column(String, ForeignKey("Surveys.Id"), nullable=False, index=True)
    Index = Column(Integer, nullable=False)
    QuestionText = Column(String, nullable=False)
    QuestionType = Column(String, nullable=False, default="choice")  # choice, rating, text
    OptionsJson = Column(String, nullable=True, default="[]")
    ResponsesJson = Column(String, nullable=True, default="{}")

    survey = relationship("SurveyModel", back_populates="questions")

class SurveyResponseModel(Base):
    __tablename__ = "SurveyResponses"
    __table_args__ = {"extend_existing": True}

    Id = Column(Integer, primary_key=True, autoincrement=True)
    SurveyId = Column(String, nullable=False, index=True)
    UserId = Column(String, nullable=True, index=True)
    VoterPseudonym = Column(String, nullable=False)
    AnswersJson = Column(String, nullable=False)
    ReceiptHash = Column(String, nullable=False)
    MerkleLeafIndex = Column(Integer, nullable=False)
    Timestamp = Column(String, nullable=False)
    VoterName = Column(String, nullable=True)
    VoterIdNumber = Column(String, nullable=True)
    DeviceName = Column(String, nullable=True)
    DeviceOS = Column(String, nullable=True)
    County = Column(String, nullable=True)
    Latitude = Column(Float, nullable=True)
    Longitude = Column(Float, nullable=True)
    GpsCoordinates = Column(String, nullable=True)

