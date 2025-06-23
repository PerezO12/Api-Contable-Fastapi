"""
Utilities for resolving Pydantic forward references in schemas
"""

def rebuild_schemas():
    """Rebuild all schemas with forward references to resolve circular imports"""
    try:
        # Import all schemas that have forward references
        from app.schemas.journal import JournalDetail
        from app.schemas.account import AccountRead
        from app.schemas.user import UserRead
        
        # Rebuild models to resolve forward references
        AccountRead.model_rebuild()
        UserRead.model_rebuild()
        JournalDetail.model_rebuild()
        
        print("✅ Forward references resolved successfully")
        return True
    except Exception as e:
        print(f"⚠️ Error resolving forward references: {e}")
        return False
