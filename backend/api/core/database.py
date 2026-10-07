import os
import shutil
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

def backup_database():
    """Creates a real-time copy backup of the database."""
    try:
        db_path = settings.DATABASE_PATH
        if os.path.exists(db_path):
            backup_path = os.path.join(os.path.dirname(db_path), "getitright_backup.db")
            shutil.copy2(db_path, backup_path)
            print(f"[DB BACKUP SUCCESS] Database mirrored to: {backup_path}")
            return backup_path
    except Exception as e:
        print(f"[DB BACKUP WARNING] Could not sync backup db: {e}")
        return None

def sync_db_schema():
    """Ensure all model tables and missing columns exist in SQLite database."""
    try:
        from sqlalchemy import inspect, text
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

# Initial backup sync on startup
backup_database()
sync_db_schema()

