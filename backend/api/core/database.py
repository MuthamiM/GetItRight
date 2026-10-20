import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.api.core.config import settings

# SQLite synchronous engine for reliable local and production transactions
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30} if "sqlite" in settings.DATABASE_URL else {}
)

if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def configure_sqlite_connection(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA busy_timeout = 30000")
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def sync_db_schema():
    """Ensure all model tables and missing columns exist in SQLite database."""
    try:
        from sqlalchemy import inspect, text
        try:
            import backend.api.features.polls.models
            import backend.api.features.users.models
            import backend.api.features.surveys.models
            import backend.api.features.analytics.models
            import backend.api.features.auth.models
            import backend.api.features.privacy.models
        except Exception:
            pass
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        with engine.connect() as conn:
            if "sqlite" in settings.DATABASE_URL:
                conn.execute(text("PRAGMA journal_mode=WAL"))
                conn.commit()
            for table_name, table in Base.metadata.tables.items():
                if inspector.has_table(table_name):
                    existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
                    for col in table.columns:
                        if col.name not in existing_cols:
                            col_type = col.type.compile(engine.dialect)
                            try:
                                conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {col_type}'))
                                conn.commit()
                                print(f"[DB MIGRATION] Added missing column {col.name} to {table_name}")
                            except Exception as ex:
                                print(f"[DB MIGRATION NOTICE] {ex}")
            if "sqlite" in settings.DATABASE_URL:
                # Keep email and phone uniqueness enforced in the live database,
                # including concurrent registration requests.
                from backend.api.core.identity import normalize_phone

                with engine.begin() as migration_conn:
                    user_rows = migration_conn.execute(text(
                        'SELECT "Id", "PhoneNumber", "PhoneCanonical" FROM "Users"'
                    )).all()
                    for user_id, phone, canonical in user_rows:
                        normalized_phone = normalize_phone(phone)
                        if canonical != normalized_phone:
                            migration_conn.execute(
                                text('UPDATE "Users" SET "PhoneCanonical" = :phone WHERE "Id" = :id'),
                                {"phone": normalized_phone, "id": user_id},
                            )

                    email_duplicates = migration_conn.execute(text(
                        'SELECT COUNT(*) FROM (SELECT lower(trim("Email")) AS normalized '
                        'FROM "Users" GROUP BY normalized HAVING COUNT(*) > 1)'
                    )).scalar_one()
                    if not email_duplicates:
                        migration_conn.execute(text(
                            'CREATE UNIQUE INDEX IF NOT EXISTS "uq_users_email_normalized" '
                            'ON "Users" (lower(trim("Email")))'
                        ))
                    else:
                        print("[DB MIGRATION NOTICE] Normalized email index skipped; duplicate account emails need review")

                    phone_duplicates = migration_conn.execute(text(
                        'SELECT COUNT(*) FROM (SELECT "PhoneCanonical" FROM "Users" '
                        'WHERE "PhoneCanonical" IS NOT NULL GROUP BY "PhoneCanonical" HAVING COUNT(*) > 1)'
                    )).scalar_one()
                    if not phone_duplicates:
                        migration_conn.execute(text(
                            'CREATE UNIQUE INDEX IF NOT EXISTS "uq_users_phone_canonical" '
                            'ON "Users" ("PhoneCanonical") WHERE "PhoneCanonical" IS NOT NULL'
                        ))
                    else:
                        print("[DB MIGRATION NOTICE] Phone uniqueness index skipped; duplicate account phones need review")

                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS "BallotIdentityClaims" (
                        "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
                        "BallotType" TEXT NOT NULL,
                        "BallotId" TEXT NOT NULL,
                        "IdentityType" TEXT NOT NULL,
                        "IdentityValue" TEXT NOT NULL,
                        UNIQUE ("BallotType", "BallotId", "IdentityType", "IdentityValue")
                    )
                '''))
                conn.commit()

                # Preserve existing ballots and reserve each recorded identity once.
                # INSERT OR IGNORE safely folds historical duplicate rows into the
                # claim ledger without altering ballot records or published totals.
                backfill_sql = (
                    '''INSERT OR IGNORE INTO "BallotIdentityClaims"
                       ("BallotType", "BallotId", "IdentityType", "IdentityValue")
                       SELECT 'poll', "PollId", 'national_id', trim("VoterIdNumber")
                       FROM "VoteTransactions"
                       WHERE "VoterIdNumber" IS NOT NULL AND trim("VoterIdNumber") <> '' ''',
                    '''INSERT OR IGNORE INTO "BallotIdentityClaims"
                       ("BallotType", "BallotId", "IdentityType", "IdentityValue")
                       SELECT 'poll', "PollId", 'account_id', lower(trim("UserId"))
                       FROM "VoteTransactions"
                       WHERE "UserId" IS NOT NULL AND trim("UserId") <> '' ''',
                    '''INSERT OR IGNORE INTO "BallotIdentityClaims"
                       ("BallotType", "BallotId", "IdentityType", "IdentityValue")
                       SELECT 'poll', "PollId", 'voter_key', lower(trim("VoterPseudonym"))
                       FROM "VoteTransactions"
                       WHERE "VoterPseudonym" IS NOT NULL AND trim("VoterPseudonym") <> '' ''',
                    '''INSERT OR IGNORE INTO "BallotIdentityClaims"
                       ("BallotType", "BallotId", "IdentityType", "IdentityValue")
                       SELECT 'survey', "SurveyId", 'national_id', trim("VoterIdNumber")
                       FROM "SurveyResponses"
                       WHERE "VoterIdNumber" IS NOT NULL AND trim("VoterIdNumber") <> '' ''',
                    '''INSERT OR IGNORE INTO "BallotIdentityClaims"
                       ("BallotType", "BallotId", "IdentityType", "IdentityValue")
                       SELECT 'survey', "SurveyId", 'account_id', lower(trim("UserId"))
                       FROM "SurveyResponses"
                       WHERE "UserId" IS NOT NULL AND trim("UserId") <> '' ''',
                    '''INSERT OR IGNORE INTO "BallotIdentityClaims"
                       ("BallotType", "BallotId", "IdentityType", "IdentityValue")
                       SELECT 'survey', "SurveyId", 'voter_key', lower(trim("VoterPseudonym"))
                       FROM "SurveyResponses"
                       WHERE "VoterPseudonym" IS NOT NULL AND trim("VoterPseudonym") <> '' ''',
                )
                for statement in backfill_sql:
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                    except Exception as ex:
                        conn.rollback()
                        print(f"[DB MIGRATION NOTICE] Ballot identity backfill skipped: {ex}")
    except Exception as e:
        print(f"[DB SCHEMA SYNC WARNING] {e}")

if os.getenv("SKIP_DB_SCHEMA_SYNC", "false").lower() not in {"1", "true", "yes"}:
    sync_db_schema()
