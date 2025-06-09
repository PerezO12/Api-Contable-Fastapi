from fastapi import APIRouter

from app.api.v1 import accounts, journal_entries, users, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(journal_entries.router, prefix="/journal-entries", tags=["journal-entries"])
