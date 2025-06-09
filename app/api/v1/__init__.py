"""
API v1 router configuration.
"""
from fastapi import APIRouter

from app.api.v1 import accounts, auth, users, journal_entries, reports

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User management routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Account management routes
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])

# Journal entry routes
api_router.include_router(journal_entries.router, prefix="/journal-entries", tags=["journal-entries"])

# Report routes - Now enabled and fully functional
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])