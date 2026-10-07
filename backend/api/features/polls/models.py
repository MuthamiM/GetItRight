from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.api.core.database import Base

class PollModel(Base):
    __tablename__ = "Polls"

    Id = Column(String, primary_key=True, index=True)
    Title = Column(String, nullable=False)
    Description = Column(String, nullable=False)
    Category = Column(String, nullable=False)
    Plan = Column(String, nullable=False, index=True)
    OwnerId = Column(String, nullable=False)
    CreatedAt = Column(String, nullable=False)
    Status = Column(String, nullable=False, default="live")
    TotalVotes = Column(Integer, default=0)
    MerkleRoot = Column(String, nullable=False)
    IsEncryptedBallot = Column(Integer, default=1)

    options = relationship("PollOptionModel", back_populates="poll", cascade="all, delete-orphan", lazy="joined")

class PollOptionModel(Base):
    __tablename__ = "PollOptions"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    PollId = Column(String, ForeignKey("Polls.Id"), nullable=False, index=True)
    Index = Column(Integer, nullable=False)
    Label = Column(String, nullable=False)
    Votes = Column(Integer, default=0)
    Percentage = Column(Float, default=0.0)

    poll = relationship("PollModel", back_populates="options")

class VoteTransactionModel(Base):
    __tablename__ = "VoteTransactions"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    PollId = Column(String, nullable=False, index=True)
    OptionIndex = Column(Integer, nullable=False)
    OptionLabel = Column(String, nullable=False)
    ReceiptHash = Column(String, nullable=False)
    MerkleLeafIndex = Column(Integer, nullable=False)
    VoterPseudonym = Column(String, nullable=False)
    Timestamp = Column(String, nullable=False)
