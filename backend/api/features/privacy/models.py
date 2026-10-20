from sqlalchemy import Column, String, Text, UniqueConstraint

from backend.api.core.database import Base


class BrowserStorageSnapshotModel(Base):
    """Latest consented browser-storage snapshot, encrypted before it reaches disk."""

    __tablename__ = "BrowserStorageSnapshots"
    __table_args__ = (
        UniqueConstraint("BrowserId", "Category", name="uq_browser_storage_category"),
    )

    Id = Column(String, primary_key=True)
    BrowserId = Column(String(80), nullable=False, index=True)
    UserId = Column(String, nullable=True, index=True)
    Category = Column(String(40), nullable=False, index=True)
    EncryptedJson = Column(Text, nullable=False)
    CapturedAt = Column(String, nullable=False, index=True)
    SourcePath = Column(String(180), nullable=True)


class GoogleProfileConsentModel(Base):
    """Encrypted basic Google profile data shared through explicit sign-in consent."""

    __tablename__ = "GoogleProfileConsents"

    GoogleSubjectHash = Column(String(64), primary_key=True)
    UserId = Column(String, nullable=True, index=True)
    EncryptedJson = Column(Text, nullable=False)
    CapturedAt = Column(String, nullable=False, index=True)
    SourcePath = Column(String(180), nullable=True)
