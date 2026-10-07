from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.users.schemas import (
    UserDetailOut, UserStatusUpdate, CreateUserRequest, UpdateUserPlanRequest,
    UpdateUserRoleRequest, RoleOut, CreateRoleRequest
)
from backend.api.features.users.service import (
    list_users, get_user_by_id, update_user_status, create_user, update_user_plan,
    list_roles, create_role, update_user_role
)

router = APIRouter(prefix="/users", tags=["Users Management"])

@router.get("/roles", response_model=List[RoleOut])
def get_all_roles():
    """Retrieve all available system and custom user roles with permissions matrix."""
    return list_roles()

@router.post("/roles", response_model=RoleOut)
def add_new_role(data: CreateRoleRequest):
    """Create a new custom user role with tailored permissions."""
    return create_role(data)

@router.get("", response_model=List[UserDetailOut])
def get_all_users(plan: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Fetch registered users optionally filtered by plan."""
    return list_users(db, plan)

@router.post("", response_model=UserDetailOut)
def register_new_user(data: CreateUserRequest, db: Session = Depends(get_db)):
    """Create and provision a new user account with tier quotas and assigned console."""
    return create_user(db, data)

@router.get("/{user_id}", response_model=UserDetailOut)
def get_single_user(user_id: str, db: Session = Depends(get_db)):
    """Fetch single user profile and quotas."""
    return get_user_by_id(db, user_id)

@router.patch("/{user_id}/status", response_model=UserDetailOut)
@router.post("/{user_id}/status", response_model=UserDetailOut)
def update_status(user_id: str, payload: UserStatusUpdate, db: Session = Depends(get_db)):
    """Activate or suspend user account."""
    return update_user_status(db, user_id, payload)

@router.post("/{user_id}/plan", response_model=UserDetailOut)
def update_plan(user_id: str, payload: UpdateUserPlanRequest, db: Session = Depends(get_db)):
    """Update user plan tier and quota allocations."""
    return update_user_plan(db, user_id, payload)

@router.post("/{user_id}/role", response_model=UserDetailOut)
def update_role(user_id: str, payload: UpdateUserRoleRequest, db: Session = Depends(get_db)):
    """Update user role assignment."""
    return update_user_role(db, user_id, payload)
