"""
Feature-First modular business domains for GetItRight API.
"""

from backend.api.features.auth.routes import router as auth_router
from backend.api.features.polls.routes import router as polls_router
from backend.api.features.surveys.routes import router as surveys_router
from backend.api.features.analytics.routes import router as analytics_router
from backend.api.features.users.routes import router as users_router

__all__ = [
    "auth_router",
    "polls_router",
    "surveys_router",
    "analytics_router",
    "users_router"
]
