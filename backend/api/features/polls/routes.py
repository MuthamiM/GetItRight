from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.polls.schemas import (
    PollOut, PollCreate, VoteCastRequest, VoteCastResponse, VoteTransactionOut, VoteStatusOut
)
from backend.api.features.polls.service import (
    list_polls, get_poll_by_id, create_poll, cast_vote, get_transactions_by_poll, reset_poll, get_vote_status
)

from backend.api.controllers.polls_controller import PollsController
from backend.api.middleware.auth_middleware import (
    get_current_user_token,
    get_optional_current_user_token,
)

router = APIRouter(prefix="/polls", tags=["Polls"])

@router.get("", response_model=List[PollOut])
def get_polls(plan: Optional[str] = Query(None, description="Filter polls by tier plan"), db: Session = Depends(get_db)):
    """Fetch real polls directly from database, optionally filtered by plan (free, pro, org, election)."""
    return PollsController.get_polls(db, plan)

@router.get("/{poll_id}", response_model=PollOut)
def get_single_poll(poll_id: str, db: Session = Depends(get_db)):
    """Fetch a single poll by ID with real option counts and calculated percentages."""
    return PollsController.get_single_poll(db, poll_id)

@router.get("/{poll_id}/vote-status", response_model=VoteStatusOut)
def check_vote_status(
    poll_id: str,
    userId: Optional[str] = Query(None),
    voterKey: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db)
):
    """Check if a user or voter pseudonym has already voted on this poll."""
    trusted_user_id = current_user["sub"] if current_user else None
    return get_vote_status(db, poll_id, user_id=trusted_user_id, voter_key=voterKey)

@router.post("", response_model=PollOut)
def create_new_poll(
    data: PollCreate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """Create a new poll with custom voting options."""
    data.ownerId = current_user["sub"]
    data.plan = current_user["plan"]
    return PollsController.create_poll(db, data)

@router.post("/{poll_id}/vote", response_model=VoteCastResponse)
def submit_vote(
    poll_id: str,
    vote_req: VoteCastRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db),
):
    """Cast a verifiable ballot, recalculate percentage distribution, and issue a cryptographic receipt."""
    # The browser cannot choose another account's identity. Anonymous voting
    # requires a stable voter key so duplicate submissions are detectable.
    vote_req.userId = current_user["sub"] if current_user else None
    if not vote_req.userId and not (vote_req.voterKey and vote_req.voterKey.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A voter key or authenticated session is required")
    return PollsController.submit_vote(db, poll_id, vote_req)

@router.post("/{poll_id}/reset", response_model=PollOut)
def reset_poll_endpoint(poll_id: str):
    """Retired: rewriting a tally breaks its verifiable record."""
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Poll resets are disabled. Publish a correction poll instead.")

@router.get("/{poll_id}/transactions", response_model=List[VoteTransactionOut])
def get_poll_audit_transactions(
    poll_id: str,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """Retrieve audit transactions and Merkle receipts for a specific poll."""
    poll = get_poll_by_id(db, poll_id)
    if current_user["role"] != "Admin" and poll.ownerId != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this poll")
    return get_transactions_by_poll(db, poll_id)

