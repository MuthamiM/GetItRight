from datetime import datetime, timezone
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.api.features.auth.models import UserModel
from backend.api.features.users.schemas import UserDetailOut, UserStatusUpdate, CreateUserRequest, UpdateUserPlanRequest
from backend.api.core.security import get_password_hash

PLAN_METADATA = {
    "free": {"name": "Civic Starter", "voters": 1000, "polls": 5, "url": "/console/user.html"},
    "pro": {"name": "Civic Pro", "voters": 25000, "polls": 50, "url": "/console/user.html"},
    "org": {"name": "Institutional Org", "voters": 100000, "polls": 200, "url": "/console/user.html"},
    "election": {"name": "Sovereign Election Guard", "voters": 10000000, "polls": 1000, "url": "/console/user.html"},
}

PLAN_TIER_RANK = {"free": 0, "pro": 1, "org": 2, "election": 3}

# Map full plan names and common variants to canonical short keys
_PLAN_NAME_TO_KEY = {
    "free": "free",
    "civic starter": "free",
    "civic_starter": "free",
    "pro": "pro",
    "civic pro": "pro",
    "civic_pro": "pro",
    "org": "org",
    "institutional org": "org",
    "institutional_org": "org",
    "election": "election",
    "sovereign election guard": "election",
    "sovereign_election_guard": "election",
}

def resolve_plan_key(raw: str) -> str:
    """Accept 'pro', 'Civic Pro', 'civic_pro', etc. and return canonical key."""
    key = raw.strip().lower()
    if key in PLAN_METADATA:
        return key
    return _PLAN_NAME_TO_KEY.get(key, key)

def map_user(u: UserModel) -> UserDetailOut:
    is_admin = (u.Role in ["Admin", "Super Admin"])
    redirect_url = "/console/admin.html" if is_admin else u.ConsoleUrl
    return UserDetailOut(
        id=u.Id,
        fullName=u.FullName,
        email=u.Email,
        role=u.Role,
        plan=None if is_admin else u.Plan,
        planName=None if is_admin else u.PlanName,
        organization=u.Organization,
        createdAt=u.CreatedAt,
        status=u.Status,
        totalPollsCreated=u.TotalPollsCreated,
        totalVotesReceived=u.TotalVotesReceived,
        voterQuota=None if is_admin else u.VoterQuota,
        pollsQuota=None if is_admin else u.PollsQuota,
        consoleUrl=redirect_url,
        lastLogin=u.LastLogin,
        isAdmin=is_admin
    )

def list_users(db: Session, plan: Optional[str] = None) -> List[UserDetailOut]:
    # The administration console is an operational directory, not an archive.
    # Hide disabled legacy/duplicate accounts so the visible directory contains
    # only the current administrator and active clients.
    query = db.query(UserModel).filter(UserModel.Status == "Active")
    if plan:
        query = query.filter(UserModel.Plan == plan.lower())
    users = query.all()
    return [map_user(u) for u in users]

def get_user_by_id(db: Session, user_id: str) -> UserDetailOut:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return map_user(user)

def create_user(db: Session, req: CreateUserRequest) -> UserDetailOut:
    effective_name = (req.fullName or req.name or req.full_name or "").strip()
    if not req.email or not effective_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and Full Name are required.")

    existing = db.query(UserModel).filter(UserModel.Email == req.email.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists.")

    if req.role and req.role.lower() == "admin":
        existing_admin = db.query(UserModel).filter(UserModel.Role == "Admin").first()
        if existing_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Security policy violation: Only ONE Admin account is permitted in the platform.")

    plan_key = resolve_plan_key(req.plan or "free")
    meta = PLAN_METADATA[plan_key]
    new_id = f"USR-{uuid.uuid4().hex[:6].upper()}"

    user = UserModel(
        Id=new_id,
        FullName=effective_name,
        Email=req.email.strip().lower(),
        Password=get_password_hash(req.password),
        Role="Customer" if not req.role or req.role.lower() != "admin" else "Admin",
        Plan=plan_key,
        PlanName=meta["name"],
        Organization=req.organization.strip() if req.organization else "Independent",
        CreatedAt=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        Status="Active",
        TotalPollsCreated=0,
        TotalVotesReceived=0,
        VoterQuota=meta["voters"],
        PollsQuota=meta["polls"],
        ConsoleUrl=meta["url"],
        LastLogin="Just now"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return map_user(user)

def update_user_status(db: Session, user_id: str, update_data: UserStatusUpdate) -> UserDetailOut:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    if user.Role in ["Admin", "Super Admin"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot modify the primary Admin status.")
    if update_data.status not in {"Active", "Suspended"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Status must be Active or Suspended")
    user.Status = update_data.status
    user.TokenVersion = (user.TokenVersion or 0) + 1
    db.commit()
    db.refresh(user)
    return map_user(user)

def update_user_plan(db: Session, user_id: str, req: UpdateUserPlanRequest, is_admin: bool = False) -> UserDetailOut:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    plan_key = resolve_plan_key(req.plan)
    if plan_key not in PLAN_METADATA:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid plan '{req.plan}'. Available plans: free, pro, org")

    # If client is self-updating, enforce upgrade-only rule
    if not is_admin:
        current_rank = PLAN_TIER_RANK.get((user.Plan or "free").lower(), 0)
        target_rank = PLAN_TIER_RANK.get(plan_key.lower(), 0)
        if target_rank <= current_rank:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can only switch plans by upgrading to a higher tier."
            )

    meta = PLAN_METADATA[plan_key]
    user.Plan = plan_key
    user.PlanName = meta["name"]
    user.ConsoleUrl = "/console/user.html" if user.Role == "Customer" else "/console/admin.html"
    user.VoterQuota = meta["voters"]
    user.PollsQuota = meta["polls"]
    user.TokenVersion = (user.TokenVersion or 0) + 1
    db.commit()
    db.refresh(user)
    return map_user(user)

SYSTEM_ROLES = [
    {
        "id": "ROLE-ADMIN",
        "name": "Admin",
        "description": "Primary Platform Administrator with full access to encryption keys and security control.",
        "isSystem": True,
        "permissions": ["create_poll", "create_survey", "open_input_fields", "manage_users", "manage_roles", "audit_merkle", "export_data"]
    },
    {
        "id": "ROLE-ANALYST",
        "name": "Analyst",
        "description": "Data Analyst with real-time chart insights and report generation access.",
        "isSystem": True,
        "permissions": ["view_analytics", "export_data", "audit_merkle"]
    },
    {
        "id": "ROLE-AUDITOR",
        "name": "Auditor",
        "description": "Independent Security & Merkle Ledger Auditor.",
        "isSystem": True,
        "permissions": ["audit_merkle", "view_checkpoint_ledger"]
    },
    {
        "id": "ROLE-ENTERPRISE",
        "name": "Enterprise Publisher",
        "description": "Enterprise Organization author with open input field surveys and custom quota.",
        "isSystem": True,
        "permissions": ["create_poll", "create_survey", "open_input_fields", "export_data"]
    },
    {
        "id": "ROLE-PRO",
        "name": "Civic Pro",
        "description": "Verified Civic Publisher with expanded voting quota.",
        "isSystem": True,
        "permissions": ["create_poll", "create_survey", "open_input_fields"]
    },
    {
        "id": "ROLE-CUSTOMER",
        "name": "Customer",
        "description": "Standard polling and survey user.",
        "isSystem": True,
        "permissions": ["create_poll", "create_survey"]
    }
]

CUSTOM_ROLES = []

def list_roles():
    return SYSTEM_ROLES + CUSTOM_ROLES

def create_role(req):
    role_id = f"ROLE-CUST-{uuid.uuid4().hex[:4].upper()}"
    new_role = {
        "id": role_id,
        "name": req.name.strip(),
        "description": (req.description or "").strip(),
        "isSystem": False,
        "permissions": req.permissions or ["create_poll", "create_survey"]
    }
    CUSTOM_ROLES.append(new_role)
    return new_role

def update_user_role(db: Session, user_id: str, req) -> UserDetailOut:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    allowed_roles = {role["name"] for role in SYSTEM_ROLES}
    if req.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown system role")
    user.Role = req.role
    user.TokenVersion = (user.TokenVersion or 0) + 1
    db.commit()
    db.refresh(user)
    return map_user(user)
