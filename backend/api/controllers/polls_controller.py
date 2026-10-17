import asyncio
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.api.features.polls.models import PollModel, PollOptionModel, VoteTransactionModel
from backend.api.features.polls.schemas import (
    PollOut, PollCreate, VoteCastRequest, VoteCastResponse, VoteTransactionOut
)
from backend.api.features.polls import service as polls_service
from backend.api.servers.websocket_server import ws_server

class PollsController:
    """Controller for polls and real-time sovereign voting operations."""

    @staticmethod
    def get_polls(db: Session, plan: Optional[str] = None, status: Optional[str] = None, include_all: bool = False) -> List[PollOut]:
        return polls_service.list_polls(db, plan=plan, status=status, include_all=include_all)

    @staticmethod
    def get_single_poll(db: Session, poll_id: str) -> PollOut:
        return polls_service.get_poll_by_id(db, poll_id)

    @staticmethod
    def create_poll(db: Session, data: PollCreate) -> PollOut:
        return polls_service.create_poll(db, data)

    @staticmethod
    def submit_vote(db: Session, poll_id: str, vote_req: VoteCastRequest) -> VoteCastResponse:
        res = polls_service.cast_vote(db, poll_id, vote_req)

        # Broadcast live vote update via WebSocket server
        poll = db.query(PollModel).filter(PollModel.Id == poll_id).first()
        if poll:
            options_data = [
                {"id": opt.Id, "text": opt.Label, "votes": opt.Votes}
                for opt in (poll.options or [])
            ]
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(
                        ws_server.broadcast_vote_update(
                            poll_id=poll_id,
                            option_id=vote_req.optionId,
                            total_votes=poll.TotalVotes,
                            options_data=options_data
                        )
                    )
            except Exception:
                pass

        return res

    @staticmethod
    def reset_poll(db: Session, poll_id: str):
        return polls_service.reset_poll(db, poll_id)

    @staticmethod
    def get_audit_transactions(db: Session, poll_id: str) -> List[VoteTransactionOut]:
        return polls_service.get_poll_audit_transactions(db, poll_id)
