import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.api.features.auth.models import UserModel
from backend.api.features.polls.models import PollModel, PollOptionModel, VoteTransactionModel
from backend.api.features.polls.schemas import (
    PollOut, PollOptionOut, PollCreate, VoteCastRequest, VoteCastResponse, VoteTransactionOut
)
from backend.api.core.security import generate_merkle_receipt


def _plain_text(value: str, field: str, maximum: int) -> str:
    clean = (value or "").strip()
    if not clean or len(clean) > maximum or any(char in clean for char in "<>"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field} must be plain text and no longer than {maximum} characters",
        )
    return clean

def map_poll_to_out(p: PollModel) -> PollOut:
    options_sorted = sorted(p.options, key=lambda opt: opt.Index)
    return PollOut(
        id=p.Id,
        title=p.Title,
        description=p.Description or "",
        category=p.Category or "General",
        plan=p.Plan or "free",
        ownerId=p.OwnerId or "USR-001",
        createdAt=p.CreatedAt or "",
        status=p.Status or "live",
        totalVotes=p.TotalVotes or 0,
        merkleRoot=p.MerkleRoot or "",
        isEncryptedBallot=bool(p.IsEncryptedBallot),
        options=[
            PollOptionOut(
                id=opt.Id,
                pollId=opt.PollId,
                index=opt.Index,
                label=opt.Label,
                text=opt.Label,
                votes=opt.Votes or 0,
                percentage=opt.Percentage or 0.0
            )
            for opt in options_sorted
        ],
        endDate=getattr(p, 'EndDate', None),
        track_name=p.Category or "General",
        author_name=p.OwnerId or "GetItRight Sovereign",
        total_votes=p.TotalVotes or 0,
        created_at=p.CreatedAt or "",
        is_multiple_choice=False
    )

def list_polls(db: Session, plan: Optional[str] = None, status: Optional[str] = None, include_all: bool = False) -> List[PollOut]:
    query = db.query(PollModel)
    if not include_all:
        if status:
            query = query.filter(PollModel.Status == status.lower())
        else:
            query = query.filter(PollModel.Status == "live")
    elif status and status.lower() != "all":
        query = query.filter(PollModel.Status == status.lower())
    if plan:
        query = query.filter(PollModel.Plan == plan.lower())
    polls = query.all()
    polls_sorted = sorted(polls, key=lambda p: (0 if p.Status == "live" else 1, p.CreatedAt or ""), reverse=False)
    return [map_poll_to_out(p) for p in polls_sorted]

def get_poll_by_id(db: Session, poll_id: str) -> PollOut:
    poll = db.query(PollModel).filter(PollModel.Id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Poll {poll_id} not found")
    return map_poll_to_out(poll)

def create_poll(db: Session, data: PollCreate) -> PollOut:
    title = _plain_text(data.title, "Poll title", 200)
    if len(title) < 3:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Poll title must be at least 3 characters")
    description = _plain_text(data.description, "Poll description", 2_000) if data.description else ""
    category = _plain_text(data.category, "Poll category", 100) if data.category else "General"
    options_list = [_plain_text(option, "Poll option", 200) for option in (data.options or []) if option and option.strip()]
    if len(options_list) < 2 or len(options_list) > 20:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A poll must have between 2 and 20 options")
    if len(set(label.casefold() for label in options_list)) != len(options_list):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Poll options must be unique")

    plan_key = (data.plan or "free").lower()
    owner_id = (data.ownerId or "").strip()
    owner = db.query(UserModel).filter(UserModel.Id == owner_id).first()
    if not owner or owner.Status != "Active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active poll owner required")
    if plan_key != owner.Plan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Poll plan must match the owner's plan")
    created_count = db.query(PollModel).filter(PollModel.OwnerId == owner_id).count()
    if created_count >= (owner.PollsQuota or 0):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Poll quota has been reached")
    prefix = "PL-" + plan_key.upper()[:4]
    new_id = f"{prefix}-{uuid.uuid4().hex[:4].upper()}"

    initial_root = "0x" + hashlib.sha256(f"{new_id}:{data.title}".encode("utf-8")).hexdigest()[:16]

    now = datetime.now(timezone.utc)
    if data.endDate:
        end_date_str = data.endDate
    elif data.durationHours:
        from datetime import timedelta
        end_date_str = (now + timedelta(hours=data.durationHours)).strftime("%Y-%m-%d %H:%M:%S")
    else:
        from datetime import timedelta
        end_date_str = (now + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

    new_poll = PollModel(
        Id=new_id,
        Title=title,
        Description=description,
        Category=category,
        Plan=plan_key,
        OwnerId=owner_id,
        CreatedAt=now.strftime("%Y-%m-%d %H:%M"),
        Status="live",
        TotalVotes=0,
        MerkleRoot=initial_root,
        IsEncryptedBallot=1 if plan_key in ["pro", "org", "election"] else 0,
        EndDate=end_date_str
    )
    db.add(new_poll)
    db.flush()

    for idx, opt_label in enumerate(options_list):
        option = PollOptionModel(
            PollId=new_id,
            Index=idx,
            Label=opt_label,
            Votes=0,
            Percentage=0.0
        )
        db.add(option)

    db.commit()
    db.refresh(new_poll)
    owner.TotalPollsCreated = created_count + 1
    db.commit()
    return map_poll_to_out(new_poll)

def cast_vote(db: Session, poll_id: str, vote_req: VoteCastRequest) -> VoteCastResponse:
    poll = db.query(PollModel).filter(PollModel.Id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Poll {poll_id} not found")
    if (poll.Status or "").lower() not in {"live", "open"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This poll is not accepting votes")
    if poll.EndDate:
        try:
            end_at = datetime.fromisoformat(poll.EndDate.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
            if end_at <= datetime.now(timezone.utc):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This poll has ended")
        except ValueError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This poll has an invalid closing time")

    target_option = None
    opt_key = None
    if vote_req.option_id is not None:
        opt_key = str(vote_req.option_id).strip()
    elif vote_req.optionId is not None:
        opt_key = str(vote_req.optionId).strip()

    if opt_key:
        for opt in poll.options:
            if str(opt.Id) == opt_key or str(opt.Index) == opt_key or f"opt{opt.Index + 1}" == opt_key or opt.Label.lower() == opt_key.lower():
                target_option = opt
                break

    if not target_option and vote_req.optionIndex is not None:
        idx = vote_req.optionIndex
        target_option = next((opt for opt in poll.options if opt.Index == idx or str(opt.Id) == str(idx)), None)

    if not target_option:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid option identifier for poll {poll_id}"
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Store User ID if authenticated, prevent duplicate voting
    user_id = vote_req.userId.strip() if vote_req.userId and str(vote_req.userId).strip() else None
    if user_id:
        existing_user_tx = db.query(VoteTransactionModel).filter(
            VoteTransactionModel.PollId == poll.Id,
            VoteTransactionModel.UserId == user_id
        ).first()
        if existing_user_tx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vote already recorded for this user. You cannot change your vote."
            )

    # REMEMBER: ONCE A VOTER VOTES, THEY CANNOT CHANGE THEIR VOTE
    if vote_req.voterKey and vote_req.voterKey.strip():
        voter_key = vote_req.voterKey.strip()
        existing_tx = db.query(VoteTransactionModel).filter(
            VoteTransactionModel.PollId == poll.Id,
            VoteTransactionModel.VoterPseudonym == voter_key
        ).first()
        if existing_tx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vote already recorded. You cannot change your vote."
            )
    else:
        voter_key = f"Voter-{user_id}" if user_id else f"Voter-{uuid.uuid4().hex[:6]}"

    receipt_hash = generate_merkle_receipt(poll_id, target_option.Index, voter_key, timestamp)

    # Increment votes
    target_option.Votes = (target_option.Votes or 0) + 1
    poll.TotalVotes = (poll.TotalVotes or 0) + 1

    # Recalculate percentages
    for opt in poll.options:
        opt.Percentage = round((opt.Votes / poll.TotalVotes) * 100.0, 1)

    # Merkle leaf index
    leaf_index = poll.TotalVotes
    new_root = "0x" + hashlib.sha256(f"{poll.MerkleRoot}:{receipt_hash}".encode("utf-8")).hexdigest()[:16]
    poll.MerkleRoot = new_root

    device_str = "Mobile App" if "mobile" in (vote_req.platform or "").lower() else "Web Browser"

    # Do not retain date of birth, county, or precise location with a ballot.
    tx = VoteTransactionModel(
        PollId=poll.Id,
        UserId=user_id,
        OptionIndex=target_option.Index,
        OptionLabel=target_option.Label,
        ReceiptHash=receipt_hash,
        MerkleLeafIndex=leaf_index,
        VoterPseudonym=voter_key,
        Timestamp=timestamp,
        County=None,
        Dob=None,
        Latitude=None,
        Longitude=None,
        GpsCoordinates=None,
        Device=device_str
    )
    db.add(tx)
    db.commit()

    return VoteCastResponse(
        success=True,
        receiptHash=receipt_hash,
        merkleLeafIndex=leaf_index,
        pollId=poll.Id,
        optionIndex=target_option.Index,
        totalVotes=poll.TotalVotes,
        timestamp=timestamp
    )

def reset_poll(db: Session, poll_id: str) -> PollOut:
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Poll resets are disabled. Publish a correction poll instead.")

def get_transactions_by_poll(db: Session, poll_id: str) -> List[VoteTransactionOut]:
    txs = db.query(VoteTransactionModel).filter(
        VoteTransactionModel.PollId == poll_id
    ).order_by(VoteTransactionModel.Id.desc()).limit(100).all()

    return [
        VoteTransactionOut(
            id=t.Id,
            pollId=t.PollId,
            userId=t.UserId,
            optionIndex=t.OptionIndex,
            optionLabel=t.OptionLabel,
            receiptHash=t.ReceiptHash,
            merkleLeafIndex=t.MerkleLeafIndex,
            voterPseudonym=t.VoterPseudonym,
            timestamp=t.Timestamp
        )
        for t in txs
    ]

def get_vote_status(db: Session, poll_id: str, user_id: Optional[str] = None, voter_key: Optional[str] = None):
    from backend.api.features.polls.schemas import VoteStatusOut
    tx = None
    if user_id and str(user_id).strip():
        tx = db.query(VoteTransactionModel).filter(
            VoteTransactionModel.PollId == poll_id,
            VoteTransactionModel.UserId == str(user_id).strip()
        ).first()

    if not tx and voter_key and str(voter_key).strip():
        tx = db.query(VoteTransactionModel).filter(
            VoteTransactionModel.PollId == poll_id,
            VoteTransactionModel.VoterPseudonym == str(voter_key).strip()
        ).first()

    if tx:
        return VoteStatusOut(
            hasVoted=True,
            pollId=poll_id,
            userId=tx.UserId,
            voterPseudonym=tx.VoterPseudonym,
            optionIndex=tx.OptionIndex,
            optionLabel=tx.OptionLabel,
            merkleLeafIndex=tx.MerkleLeafIndex,
            timestamp=tx.Timestamp
        )

    return VoteStatusOut(
        hasVoted=False,
        pollId=poll_id,
        userId=user_id,
        voterPseudonym=voter_key
    )

