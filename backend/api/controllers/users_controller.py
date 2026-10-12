from typing import Optional, List
from sqlalchemy.orm import Session
from backend.api.features.users.schemas import (
    UserDetailOut, CreateUserRequest, UserStatusUpdate,
    UpdateUserPlanRequest, UpdateUserRoleRequest, RoleOut
)
from backend.api.features.users import service as users_service

class UsersController:
    """Controller for user identity management, roles, and plan allocations."""

    @staticmethod
    def get_users(db: Session, plan: Optional[str] = None) -> List[UserDetailOut]:
        return users_service.list_users(db, plan=plan)

    @staticmethod
    def create_user(db: Session, data: CreateUserRequest) -> UserDetailOut:
        return users_service.create_user(db, data)

    @staticmethod
    def get_user(db: Session, user_id: str) -> UserDetailOut:
        return users_service.get_user_by_id(db, user_id)

    @staticmethod
    def update_status(db: Session, user_id: str, payload: UserStatusUpdate) -> UserDetailOut:
        return users_service.update_user_status(db, user_id, payload.status)

    @staticmethod
    def update_plan(db: Session, user_id: str, payload: UpdateUserPlanRequest) -> UserDetailOut:
        return users_service.update_user_plan(db, user_id, payload.plan)

    @staticmethod
    def update_role(db: Session, user_id: str, payload: UpdateUserRoleRequest) -> UserDetailOut:
        return users_service.update_user_role(db, user_id, payload.role)

    @staticmethod
    def list_roles(db: Session) -> List[RoleOut]:
        return users_service.get_roles(db)
