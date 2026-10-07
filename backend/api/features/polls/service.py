import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.api.features.polls.models import PollModel, PollOptionModel, VoteTransactionModel
from backend.api.features.polls.schemas import (
    PollOut, PollOptionOut, PollCreate, VoteCastRequest, VoteCastResponse, VoteTransactionOut
)
from backend.api.core.security import generate_merkle_receipt

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
        track_name=p.Category or "General",
        author_name=p.OwnerId or "GetItRight Sovereign",
        total_votes=p.TotalVotes or 0,
        created_at=p.CreatedAt or "",
        is_multiple_choice=False
    )

def list_polls(db: Session, plan: Optional[str] = None) -> List[PollOut]:
    query = db.query(PollModel)
    if plan:
        query = query.filter(PollModel.Plan == plan.lower())
    polls = query.all()
    # Prioritize Kitui East / Zak Syengo poll at the top of the feed
    polls_sorted = sorted(polls, key=lambda p: 0 if p.Id == "PL-KITUI-EAST-2027" else 1)
    return [map_poll_to_out(p) for p in polls_sorted]

def get_poll_by_id(db: Session, poll_id: str) -> PollOut:
    poll = db.query(PollModel).filter(PollModel.Id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Poll {poll_id} not found")
    return map_poll_to_out(poll)

def create_poll(db: Session, data: PollCreate) -> PollOut:
    options_list = [opt.strip() for opt in (data.options or []) if opt and opt.strip()]
    if not options_list:
        # Author left choices blank -> automatically enable open text input field option
        options_list = ["Open Text Response Input Field"]

    plan_key = (data.plan or "free").lower()
    prefix = "PL-" + plan_key.upper()[:4]
    new_id = f"{prefix}-{uuid.uuid4().hex[:4].upper()}"

    initial_root = "0x" + hashlib.sha256(f"{new_id}:{data.title}".encode("utf-8")).hexdigest()[:16]

    new_poll = PollModel(
        Id=new_id,
        Title=data.title.strip(),
        Description=data.description.strip() if data.description else "",
        Category=data.category.strip() if data.category else "General",
        Plan=plan_key,
        OwnerId=data.ownerId or "USR-001",
        CreatedAt=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        Status="live",
        TotalVotes=0,
        MerkleRoot=initial_root,
        IsEncryptedBallot=1 if plan_key in ["pro", "org", "election"] else 0
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
    return map_poll_to_out(new_poll)

def cast_vote(db: Session, poll_id: str, vote_req: VoteCastRequest) -> VoteCastResponse:
    poll = db.query(PollModel).filter(PollModel.Id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Poll {poll_id} not found")

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

    if not target_option and poll.options:
        target_option = poll.options[0]

    if not target_option:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid option identifier for poll {poll_id}"
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    voter_key = vote_req.voterKey or f"Voter-{uuid.uuid4().hex[:6]}"
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

    # Record Vote Transaction
    tx = VoteTransactionModel(
        PollId=poll.Id,
        OptionIndex=target_option.Index,
        OptionLabel=target_option.Label,
        ReceiptHash=receipt_hash,
        MerkleLeafIndex=leaf_index,
        VoterPseudonym=voter_key,
        Timestamp=timestamp
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
    poll = db.query(PollModel).filter(PollModel.Id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Poll {poll_id} not found")
    
    for opt in poll.options:
        opt.Votes = 0
        opt.Percentage = 0.0
    poll.TotalVotes = 0
    db.commit()
    db.refresh(poll)
    return map_poll_to_out(poll)

def get_transactions_by_poll(db: Session, poll_id: str) -> List[VoteTransactionOut]:
    txs = db.query(VoteTransactionModel).filter(
        VoteTransactionModel.PollId == poll_id
    ).order_by(VoteTransactionModel.Id.desc()).limit(100).all()

    return [
        VoteTransactionOut(
            id=t.Id,
            pollId=t.PollId,
            optionIndex=t.OptionIndex,
            optionLabel=t.OptionLabel,
            receiptHash=t.ReceiptHash,
            merkleLeafIndex=t.MerkleLeafIndex,
            voterPseudonym=t.VoterPseudonym,
            timestamp=t.Timestamp
        )
        for t in txs
    ]
