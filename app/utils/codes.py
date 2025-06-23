"""
Code generation utilities for creating sequential codes.
"""
import uuid
from datetime import datetime
from typing import Type, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.base import Base


def generate_code(
    db: Session, 
    model_class: Type[Base], 
    field_name: str, 
    prefix: str = "", 
    length: int = 6,
    date_format: Optional[str] = None
) -> str:
    """
    Generate a sequential code for a model field.
    
    Args:
        db: Database session
        model_class: SQLAlchemy model class
        field_name: Field name to generate code for
        prefix: Code prefix
        length: Number length (default 6 digits)
        date_format: Optional date format to include (e.g., "YYYYMM")
        
    Returns:
        Generated code string
        
    Example:
        generate_code(db, Payment, "payment_number", "PAY", 6)  # PAY000001
        generate_code(db, Invoice, "invoice_number", "INV", 6, "YYYYMM")  # INV202412000001
    """
    # Build the base pattern for searching existing codes
    date_part = ""
    if date_format:
        date_part = datetime.now().strftime(date_format.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d"))
    
    pattern_prefix = f"{prefix}{date_part}"
    
    # Get the highest existing number for this pattern
    field = getattr(model_class, field_name)
    query = db.query(field).filter(field.like(f"{pattern_prefix}%"))
    
    existing_codes = [str(code[0]) for code in query.all() if code[0]]
    
    # Extract numeric parts and find the maximum
    max_number = 0
    for code in existing_codes:
        if code.startswith(pattern_prefix):
            try:
                # Extract the numeric part after the prefix
                numeric_part = code[len(pattern_prefix):]
                if numeric_part.isdigit():
                    max_number = max(max_number, int(numeric_part))
            except (ValueError, IndexError):
                continue
    
    # Generate next number
    next_number = max_number + 1
    numeric_part = str(next_number).zfill(length)
    
    return f"{pattern_prefix}{numeric_part}"


def generate_uuid_code() -> str:
    """Generate a UUID-based code"""
    return str(uuid.uuid4())


def generate_reference(prefix: str = "REF", separator: str = "-") -> str:
    """
    Generate a reference code with timestamp.
    
    Args:
        prefix: Reference prefix
        separator: Separator character
        
    Returns:
        Reference string like "REF-20241222-001"
    """
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M%S")
    
    return f"{prefix}{separator}{date_part}{separator}{time_part}"


def validate_code_format(code: str, prefix: str, expected_length: Optional[int] = None) -> bool:
    """
    Validate if a code follows the expected format.
    
    Args:
        code: Code to validate
        prefix: Expected prefix
        expected_length: Expected total length
        
    Returns:
        True if valid, False otherwise
    """
    if not code.startswith(prefix):
        return False
    
    if expected_length and len(code) != expected_length:
        return False
    
    # Check if the part after prefix is numeric
    numeric_part = code[len(prefix):]
    return numeric_part.isdigit() if numeric_part else False
