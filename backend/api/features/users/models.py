# Re-export UserModel for feature-first modularity
from backend.api.features.auth.models import UserModel

__all__ = ["UserModel"]
