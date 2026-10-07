# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Integer, Float
from backend.api.core.database import Base

class StationModel(Base):
    __tablename__ = "Stations"

    Code = Column(String, primary_key=True, index=True)
    Name = Column(String, nullable=False)
    County = Column(String, nullable=False)
    Constituency = Column(String, nullable=False)
    RegisteredVoters = Column(Integer, default=0)
    VotesCast = Column(Integer, default=0)
    TurnoutPercent = Column(Float, default=0.0)
    DualObservers = Column(String, nullable=False)
    Status = Column(String, nullable=False, default="verified")
    Form34AHash = Column(String, nullable=False)
    ObsASignature = Column(String, nullable=False)
    ObsBSignature = Column(String, nullable=False)

class AnomalyModel(Base):
    __tablename__ = "Anomalies"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    StationCode = Column(String, nullable=False)
    RuleName = Column(String, nullable=False)
    Severity = Column(String, nullable=False)
    Description = Column(String, nullable=False)
    Timestamp = Column(String, nullable=False)

class DisputeModel(Base):
    __tablename__ = "Disputes"

    Id = Column(String, primary_key=True)
    StationCode = Column(String, nullable=False)
    StationName = Column(String, nullable=False)
    ObserverA = Column(String, nullable=False)
    ObserverB = Column(String, nullable=False)
    ObsATally = Column(Integer, default=0)
    ObsBTally = Column(Integer, default=0)
    Variance = Column(Integer, default=0)
    Status = Column(String, nullable=False)
    AuditorFinding = Column(String, nullable=False)

class CheckpointModel(Base):
    __tablename__ = "Checkpoints"

    CheckpointId = Column(Integer, primary_key=True, autoincrement=True)
    MerkleRootHash = Column(String, nullable=False)
    SubmissionsCount = Column(Integer, default=0)
    BitcoinBlockHeight = Column(Integer, default=0)
    BitcoinTxId = Column(String, nullable=False)
    Status = Column(String, nullable=False)
    PublishedAt = Column(String, nullable=False)

class ObserverModel(Base):
    __tablename__ = "Observers"

    ObserverId = Column(String, primary_key=True)
    Name = Column(String, nullable=False)
    StationCode = Column(String, nullable=False)
    HardwareModel = Column(String, nullable=False)
    KeystoreType = Column(String, nullable=False)
    PublicKeyFingerprint = Column(String, nullable=False)
    BatterySignal = Column(String, nullable=False)
    Status = Column(String, nullable=False)

class LedgerBlockModel(Base):
    __tablename__ = "LedgerBlocks"

    Height = Column(Integer, primary_key=True, autoincrement=True)
    BlockHash = Column(String, nullable=False)
    PreviousHash = Column(String, nullable=False)
    PayloadType = Column(String, nullable=False)
    LeafCount = Column(Integer, default=0)
    Timestamp = Column(String, nullable=False)
    MerkleRoot = Column(String, nullable=False)

class AuditLogModel(Base):
    __tablename__ = "AuditLogs"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Timestamp = Column(String, nullable=False)
    Actor = Column(String, nullable=False)
    Role = Column(String, nullable=False)
    Action = Column(String, nullable=False)
    TargetResource = Column(String, nullable=False)
    Signature = Column(String, nullable=False)

class StatModel(Base):
    __tablename__ = "Stats"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    StationsTotal = Column(Integer, default=250)
    StationsReporting = Column(Integer, default=242)
    LedgerCommits = Column(Integer, default=14210)
    ActiveObservers = Column(Integer, default=482)
    OpenAnomalies = Column(Integer, default=3)
    IngestionMsgPerSec = Column(Integer, default=1420)
    P99LatencyMs = Column(Float, default=2.4)
    ChainIntegrityPercent = Column(Float, default=100.0)
