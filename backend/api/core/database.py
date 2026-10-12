import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.api.core.config import settings

# SQLite synchronous engine for reliable local and production transactions
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

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
        except Exception:
            pass
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        with engine.connect() as conn:
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
    except Exception as e:
        print(f"[DB SCHEMA SYNC WARNING] {e}")

sync_db_schema()
