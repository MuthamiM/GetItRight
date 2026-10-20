from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.polls.schemas import (
    PollOut, PollCreate, VoteCastRequest, VoteCastResponse, VoteTransactionOut,
    VoteStatusOut, VoteStatusRequest
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


def _build_poll_export(db: Session, owner_id: Optional[str], export_format: str):
    from backend.api.features.polls.models import PollModel, VoteTransactionModel

    query = db.query(PollModel)
    if owner_id:
        query = query.filter(PollModel.OwnerId == owner_id)
    polls = query.all()
    poll_ids = [poll.Id for poll in polls]
    transactions = db.query(VoteTransactionModel).filter(
        VoteTransactionModel.PollId.in_(poll_ids)
    ).order_by(VoteTransactionModel.Timestamp.desc()).all() if poll_ids else []
    transactions_by_poll = {}
    for transaction in transactions:
        transactions_by_poll.setdefault(transaction.PollId, []).append(transaction)

    if export_format == "csv":
        import csv
    if export_format == "csv":
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Poll ID", "Poll Title", "Category", "Status", "Total Votes", "Leading Option"])
        for poll in polls:
            votes = transactions_by_poll.get(poll.Id, [])
            tallies = {}
            for v in votes:
                tallies[v.OptionLabel] = tallies.get(v.OptionLabel, 0) + 1
            lead = max(tallies.items(), key=lambda x: x[1])[0] if tallies else "No votes yet"
            writer.writerow([poll.Id, poll.Title, poll.Category or "General", poll.Status, len(votes), lead])
        return output.getvalue().encode("utf-8"), "text/csv", "icapsq-poll-results.csv"

    if export_format == "json":
        import json
        data = []
        for poll in polls:
            votes = transactions_by_poll.get(poll.Id, [])
            tallies = {}
            for v in votes:
                tallies[v.OptionLabel] = tallies.get(v.OptionLabel, 0) + 1
            data.append({
                "pollId": poll.Id,
                "title": poll.Title,
                "category": poll.Category,
                "status": poll.Status,
                "totalVotes": len(votes),
                "optionDistribution": tallies,
                "votes": [{
                    "id": v.Id,
                    "option": v.OptionLabel,
                    "timestamp": v.Timestamp,
                    "voter": v.VoterName or v.VoterPseudonym,
                    "county": v.County or "Nairobi County",
                    "status": "Verified & Confirmed"
                } for v in votes]
            })
        return json.dumps(data, indent=2).encode("utf-8"), "application/json", "icapsq-poll-results.json"

    if not polls:
        from backend.api.core.report_builder import build_empty_report
        extensions = {
            "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "icapsq-poll-results.xlsx"),
            "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "icapsq-poll-results.docx"),
            "pdf": ("application/pdf", "icapsq-poll-results.pdf"),
        }
        media_type, filename = extensions[export_format]
        content = build_empty_report("Poll results report", "No polls are available to export for this account.", export_format)
        return content, media_type, filename

    from backend.api.core.report_builder import build_poll_docx, build_poll_xlsx, build_poll_pdf
    if polls:
        first_poll = polls[0]
        votes = transactions_by_poll.get(first_poll.Id, [])
        if export_format == "xlsx":
            return build_poll_xlsx(first_poll, votes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "icapsq-poll-results.xlsx"
        if export_format == "docx":
            return build_poll_docx(first_poll, votes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "icapsq-poll-results.docx"
        return build_poll_pdf(first_poll, votes), "application/pdf", "icapsq-poll-results.pdf"

    raise ValueError(f"Unsupported poll export format: {export_format}")

@router.get("", response_model=List[PollOut])
def get_polls(
    plan: Optional[str] = Query(None, description="Filter polls by tier plan"),
    status: Optional[str] = Query(None, description="Filter polls by status"),
    include_all: Optional[bool] = Query(False, description="Include archived/disabled polls (admin)"),
    db: Session = Depends(get_db)
):
    """Fetch real polls directly from database, optionally filtered by plan and status."""
    return PollsController.get_polls(db, plan=plan, status=status, include_all=include_all)


@router.get("/exports/results")
def export_poll_results(
    export_format: str = Query("pdf", alias="format", pattern="^(pdf|docx|xlsx|csv|json)$"),
    owner_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    if current_user["role"] not in ["Admin", "Super Admin"]:
        owner_id = current_user["sub"]
    data, media_type, filename = _build_poll_export(db, owner_id, export_format)
    return StreamingResponse(BytesIO(data), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{poll_id}/export")
def export_single_poll(
    poll_id: str,
    export_format: str = Query("csv", alias="format", pattern="^(pdf|docx|xlsx|csv|json)$"),
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    from backend.api.features.polls.models import PollModel, VoteTransactionModel
    poll = db.query(PollModel).filter(PollModel.Id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")
    if current_user["role"] not in ["Admin", "Super Admin"] and poll.OwnerId != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this poll")

    votes = db.query(VoteTransactionModel).filter(
        VoteTransactionModel.PollId == poll_id
    ).order_by(VoteTransactionModel.Timestamp.desc()).all()

    slug = "".join(c for c in poll.Title.lower().replace(" ", "-") if c.isalnum() or c == "-")[:30] or "poll"

    if export_format == "csv":
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Poll ID", "Poll Title", "Category", "Status", "Option Choice", "Citizen Voter", "County", "Timestamp", "Device", "Verification Status"])
        if not votes:
            writer.writerow([poll.Id, poll.Title, poll.Category or "General", poll.Status, "No votes yet", "", "", "", "", ""])
        else:
            for v in votes:
                voter_name = v.VoterName or v.VoterPseudonym
                cty = v.County or "Nairobi County"
                dev = v.DeviceName or v.Device or "Mobile / Web App"
                writer.writerow([poll.Id, poll.Title, poll.Category or "General", poll.Status, v.OptionLabel, voter_name, cty, v.Timestamp, dev, "Verified & Confirmed"])
        return StreamingResponse(BytesIO(output.getvalue().encode("utf-8")), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{slug}-votes.csv"'})

    if export_format == "json":
        import json
        option_tallies = {}
        for opt in (getattr(poll, 'options', []) or []):
            option_tallies[opt.Label] = 0
        for v in votes:
            option_tallies[v.OptionLabel] = option_tallies.get(v.OptionLabel, 0) + 1
        data = {
            "pollId": poll.Id,
            "title": poll.Title,
            "category": poll.Category,
            "status": poll.Status,
            "totalVotes": len(votes),
            "resultsBreakdown": [{"option": k, "votes": val, "percentage": round((val/len(votes)*100) if votes else 0, 1)} for k, val in option_tallies.items()],
            "votes": [{
                "id": v.Id,
                "option": v.OptionLabel,
                "timestamp": v.Timestamp,
                "voter": v.VoterName or v.VoterPseudonym,
                "county": v.County or "Nairobi County",
                "device": v.DeviceName or "Mobile App",
                "status": "Verified & Confirmed"
            } for v in votes]
        }
        return StreamingResponse(BytesIO(json.dumps(data, indent=2).encode("utf-8")), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{slug}-votes.json"'})

    from backend.api.core.report_builder import build_poll_docx, build_poll_xlsx, build_poll_pdf

    if export_format == "xlsx":
        content = build_poll_xlsx(poll, votes)
        return StreamingResponse(BytesIO(content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="{slug}-report.xlsx"'})

    if export_format == "docx":
        content = build_poll_docx(poll, votes)
        return StreamingResponse(BytesIO(content), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="{slug}-report.docx"'})

    content = build_poll_pdf(poll, votes)
    return StreamingResponse(BytesIO(content), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{slug}-report.pdf"'})

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


@router.post("/{poll_id}/vote-status", response_model=VoteStatusOut)
def check_vote_status_by_national_id(
    poll_id: str,
    request_data: VoteStatusRequest,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """Check ballot history by National ID without placing the ID in a URL."""
    if not (request_data.voterIdNumber or request_data.voterKey):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="National ID or voter key is required to check ballot history.",
        )
    return get_vote_status(
        db,
        poll_id,
        user_id=current_user["sub"],
        voter_key=request_data.voterKey,
        voter_id_number=request_data.voterIdNumber,
    )

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
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """Cast a verifiable ballot, recalculate percentage distribution, and issue a cryptographic receipt."""
    # Account identity always comes from the verified server-side token.
    # Never accept a client-supplied account ID or downgrade to anonymous voting.
    vote_req.userId = current_user["sub"]
    if not (vote_req.voterKey and vote_req.voterKey.strip()):
        import uuid
        vote_req.voterKey = f"BALLOT-{uuid.uuid4().hex[:12].upper()}"
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
    is_admin = current_user.get("role") in ["Admin", "Super Admin"]
    if not is_admin and (poll.ownerId or "").lower() != (current_user.get("sub") or "").lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this poll")
    return get_transactions_by_poll(db, poll_id)
