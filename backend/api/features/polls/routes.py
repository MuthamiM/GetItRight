from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.polls.schemas import (
    PollOut, PollCreate, VoteCastRequest, VoteCastResponse, VoteTransactionOut
)
from backend.api.features.polls.service import (
    list_polls, get_poll_by_id, create_poll, cast_vote, get_transactions_by_poll, reset_poll
)

router = APIRouter(prefix="/polls", tags=["Polls"])

@router.get("", response_model=List[PollOut])
def get_polls(plan: Optional[str] = Query(None, description="Filter polls by tier plan"), db: Session = Depends(get_db)):
    """Fetch real polls directly from database, optionally filtered by plan (free, pro, org, election)."""
    return list_polls(db, plan)

@router.get("/{poll_id}", response_model=PollOut)
def get_single_poll(poll_id: str, db: Session = Depends(get_db)):
    """Fetch a single poll by ID with real option counts and calculated percentages."""
    return get_poll_by_id(db, poll_id)

@router.post("", response_model=PollOut)
def create_new_poll(data: PollCreate, db: Session = Depends(get_db)):
    """Create a new poll with custom voting options."""
    return create_poll(db, data)

@router.post("/{poll_id}/vote", response_model=VoteCastResponse)
def submit_vote(poll_id: str, vote_req: VoteCastRequest, db: Session = Depends(get_db)):
    """Cast a verifiable ballot, recalculate percentage distribution, and issue a cryptographic receipt."""
    return cast_vote(db, poll_id, vote_req)

@router.post("/{poll_id}/reset", response_model=PollOut)
def reset_poll_endpoint(poll_id: str, db: Session = Depends(get_db)):
    """Reset a poll's tally to zero."""
    return reset_poll(db, poll_id)

@router.get("/{poll_id}/transactions", response_model=List[VoteTransactionOut])
def get_poll_audit_transactions(poll_id: str, db: Session = Depends(get_db)):
    """Retrieve audit transactions and Merkle receipts for a specific poll."""
    return get_transactions_by_poll(db, poll_id)
