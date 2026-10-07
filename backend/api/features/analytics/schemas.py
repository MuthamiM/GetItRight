from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class OverviewStatsOut(BaseModel):
    totalUsers: int
    totalPolls: int
    totalVotesCast: int
    ledgerBlocksCount: int
    stationsReporting: int
    activeAnomalies: int
    lastAnchorCheckpoint: int

class PlanCountOut(BaseModel):
    plan: str
    count: int

class PollsByPlanOut(BaseModel):
    plan: str
    count: int
    totalVotes: int

class PrivacyGuaranteesOut(BaseModel):
    zkProofEnforced: bool
    secretBallotDecryptionAllowed: bool
    rawVoterPiiStored: bool
    voterPseudonymHashing: str
    message: str

class TrackingTelemetryOut(BaseModel):
    overview: OverviewStatsOut
    usersByPlan: List[PlanCountOut]
    pollsByPlan: List[PollsByPlanOut]
    privacyGuarantees: PrivacyGuaranteesOut

class StationOut(BaseModel):
    code: str
    name: str
    county: str
    constituency: str
    registeredVoters: int
    votesCast: int
    turnoutPercent: float
    dualObservers: str
    status: str
    form34AHash: str
    obsASignature: str
    obsBSignature: str

class AnomalyOut(BaseModel):
    id: int
    stationCode: str
    ruleName: str
    severity: str
    description: str
    timestamp: str

class DisputeOut(BaseModel):
    id: str
    stationCode: str
    stationName: str
    observerA: str
    observerB: str
    obsATally: int
    obsBTally: int
    variance: int
    status: str
    auditorFinding: str

class CheckpointOut(BaseModel):
    checkpointId: int
    merkleRootHash: str
    submissionsCount: int
    bitcoinBlockHeight: int
    bitcoinTxId: str
    status: str
    publishedAt: str

class ObserverOut(BaseModel):
    observerId: str
    name: str
    stationCode: str
    hardwareModel: str
    keystoreType: str
    publicKeyFingerprint: str
    batterySignal: str
    status: str

class LedgerBlockOut(BaseModel):
    height: int
    blockHash: str
    previousHash: str
    payloadType: str
    leafCount: int
    timestamp: str
    merkleRoot: str

class AuditLogOut(BaseModel):
    id: int
    timestamp: str
    actor: str
    role: str
    action: str
    targetResource: str
    signature: str

class StatsOut(BaseModel):
    id: int
    stationsTotal: int
    stationsReporting: int
    ledgerCommits: int
    activeObservers: int
    openAnomalies: int
    ingestionMsgPerSec: int
    p99LatencyMs: float
    chainIntegrityPercent: float

# --- Dashboard Stats Schemas ---

class MonthlyVoteOut(BaseModel):
    month: str
    votes: int

class RecentVoterOut(BaseModel):
    name: str
    initials: str
    time: str
    ip: str
    device: str
    gps: str
    pollTitle: str

class AdminDashboardStatsOut(BaseModel):
    activePolls: int
    activeSurveys: int
    totalUsers: int
    totalVotesCast: int
    monthlyVotes: List[MonthlyVoteOut]
    turnoutRate: float
    votesByPlan: Dict[str, int]
    recentVoters: List[RecentVoterOut]
    verificationRate: float
    anomalyBlockRate: float
    anomalyDailyBars: List[int]

class CustomerDashboardStatsOut(BaseModel):
    myActivePolls: int
    myTotalVotes: int
    voterQuota: int
    pollsQuota: int
    monthlyVotes: List[MonthlyVoteOut]
    turnoutRate: float
    avgResponseTime: float
    planName: str
    organization: str
    quotaUsed: int

class SurveyTemplateQuestionOut(BaseModel):
    questionText: str
    questionType: str
    options: List[str] = []

class SurveyTemplateOut(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon: str
    questions: List[SurveyTemplateQuestionOut]
