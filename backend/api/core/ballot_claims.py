from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple


def reserve_ballot_identities(
    db: Session,
    ballot_type: str,
    ballot_id: str,
    identities: List[Tuple[str, Optional[str]]],
) -> None:
    """Reserve identities inside the same transaction as a ballot submission.

    The unique constraint makes concurrent submissions from separate sessions
    serialize safely. Existing ballot rows are copied into this ledger during
    database startup, including when those rows already contain duplicates.
    """
    for identity_type, raw_value in identities:
        value = (raw_value or "").strip()
        if not value:
            continue
        if identity_type in {"account_id", "voter_key"}:
            value = value.casefold()
        db.execute(
            text('''
                INSERT INTO "BallotIdentityClaims"
                    ("BallotType", "BallotId", "IdentityType", "IdentityValue")
                VALUES (:ballot_type, :ballot_id, :identity_type, :identity_value)
            '''),
            {
                "ballot_type": ballot_type,
                "ballot_id": ballot_id,
                "identity_type": identity_type,
                "identity_value": value,
            },
        )
