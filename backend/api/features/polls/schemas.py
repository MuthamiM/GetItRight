from typing import Optional, List, Any
from pydantic import BaseModel

class PollOptionOut(BaseModel):
    id: Any
    pollId: str
    index: int
    label: str
    text: Optional[str] = None
    votes: int = 0
    percentage: float = 0.0

class PollOut(BaseModel):
    id: str
    title: str
    description: str
    category: str
    plan: str
    ownerId: str
    createdAt: str
    status: str
    totalVotes: int
    merkleRoot: str
    isEncryptedBallot: bool
    options: List[PollOptionOut] = []
    endDate: Optional[str] = None
    track_name: Optional[str] = None
    author_name: Optional[str] = None
    total_votes: Optional[int] = None
    created_at: Optional[str] = None
    is_multiple_choice: bool = False

class PollOptionCreate(BaseModel):
    label: str

class PollCreate(BaseModel):
    title: str
    description: str
    category: Optional[str] = "General"
    plan: Optional[str] = "free"
    ownerId: Optional[str] = "USR-001"
    endDate: Optional[str] = None
    durationHours: Optional[int] = None
    options: List[str]

class VoteCastRequest(BaseModel):
    optionIndex: Optional[int] = None
    option_id: Optional[Any] = None
    optionId: Optional[Any] = None
    voterKey: Optional[str] = None
    voterFingerprint: Optional[str] = None
    userId: Optional[str] = None
    platform: Optional[str] = "web"
    county: Optional[str] = None
    dob: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    gps: Optional[str] = None

class VoteCastResponse(BaseModel):
    success: bool
    receiptHash: str
    merkleLeafIndex: int
    pollId: str
    optionIndex: int
    totalVotes: int
    timestamp: str

class VoteTransactionOut(BaseModel):
    id: int
    pollId: str
    userId: Optional[str] = None
    optionIndex: int
    optionLabel: str
    receiptHash: str
    merkleLeafIndex: int
    voterPseudonym: str
    timestamp: str

class VoteStatusOut(BaseModel):
    hasVoted: bool
    pollId: str
    userId: Optional[str] = None
    voterPseudonym: Optional[str] = None
    optionIndex: Optional[int] = None
    optionLabel: Optional[str] = None
    merkleLeafIndex: Optional[int] = None
    timestamp: Optional[str] = None


