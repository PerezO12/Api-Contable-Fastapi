from typing import NoReturn, Optional, Dict, Any, Union
from fastapi import HTTPException, status


class AccountingSystemException(Exception):
    """Base exception for the accounting system"""
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message} (Code: {self.error_code})" if self.error_code else self.message


class UserNotFoundException(AccountingSystemException):
    """Exception for when a user is not found"""
    def __init__(self, user_id: Optional[str] = None, email: Optional[str] = None):
        identifier = user_id or email or "unknown"
        message = f"User not found: {identifier}"
        super().__init__(message, "USER_NOT_FOUND", {"identifier": identifier})


class UserNotFoundError(UserNotFoundException):
    """Alias for UserNotFoundException - maintaining compatibility"""
    pass


class UserValidationError(AccountingSystemException):
    """Exception for user validation errors"""
    def __init__(self, field: str, value: Any = None, reason: str = "Invalid value"):
        message = f"User validation error in field '{field}': {reason}"
        details = {"field": field, "value": str(value) if value is not None else None, "reason": reason}
        super().__init__(message, "USER_VALIDATION_ERROR", details)


class AuthenticationError(AccountingSystemException):
    """Exception for authentication errors"""
    def __init__(self, reason: str = "Authentication failed", attempt_count: Optional[int] = None):
        message = f"Authentication error: {reason}"
        details: Dict[str, Any] = {"reason": reason}
        if attempt_count is not None:
            details["attempt_count"] = attempt_count
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class PasswordValidationError(AccountingSystemException):
    """Exception for password validation errors"""
    def __init__(self, issues: list[str]):
        message = f"Password validation failed: {', '.join(issues)}"
        super().__init__(message, "PASSWORD_VALIDATION_ERROR", {"issues": issues})


class SessionError(AccountingSystemException):
    """Exception for session errors"""
    def __init__(self, reason: str = "Session error", session_id: Optional[str] = None):
        message = f"Session error: {reason}"
        details: Dict[str, Any] = {"reason": reason}
        if session_id:
            details["session_id"] = session_id
        super().__init__(message, "SESSION_ERROR", details)


class TokenError(AccountingSystemException):
    """Exception for token errors"""
    def __init__(self, reason: str = "Invalid token", token_type: str = "access"):
        message = f"Token error ({token_type}): {reason}"
        super().__init__(message, "TOKEN_ERROR", {"reason": reason, "token_type": token_type})


class InsufficientPermissionsException(AccountingSystemException):
    """Exception for insufficient permissions"""
    def __init__(self, required_permission: str, user_role: Optional[str] = None):
        message = f"Insufficient permissions. Required: {required_permission}"
        if user_role:
            message += f", Current role: {user_role}"
        details: Dict[str, Any] = {"required_permission": required_permission, "user_role": user_role}
        super().__init__(message, "INSUFFICIENT_PERMISSIONS", details)


class InvalidPasswordException(AccountingSystemException):
    """Exception for invalid passwords"""
    def __init__(self, reason: str = "Invalid password format"):
        message = f"Invalid password: {reason}"
        super().__init__(message, "INVALID_PASSWORD", {"reason": reason})


class UserAlreadyExistsException(AccountingSystemException):
    """Exception for users that already exist"""
    def __init__(self, email: str):
        message = f"User already exists with email: {email}"
        super().__init__(message, "USER_ALREADY_EXISTS", {"email": email})


class AccountLockedException(AccountingSystemException):
    """Exception for locked accounts"""
    def __init__(self, user_id: str, locked_until: Optional[str] = None, reason: str = "Too many failed attempts"):
        message = f"Account locked for user {user_id}: {reason}"
        details: Dict[str, Any] = {"user_id": user_id, "reason": reason}
        if locked_until:
            details["locked_until"] = locked_until
            message += f" until {locked_until}"
        super().__init__(message, "ACCOUNT_LOCKED", details)


class AccountNotFoundError(AccountingSystemException):
    """Exception for when an account is not found"""
    def __init__(self, account_id: Optional[str] = None, account_code: Optional[str] = None):
        identifier = account_id or account_code or "unknown"
        field = "code" if account_code else "id"
        message = f"Account not found with {field}: {identifier}"
        super().__init__(message, "ACCOUNT_NOT_FOUND", {"identifier": identifier, "field": field})


class AccountValidationError(AccountingSystemException):
    """Exception for account validation errors"""
    def __init__(self, field: str, value: Any = None, reason: str = "Invalid value"):
        message = f"Account validation error in field '{field}': {reason}"
        details: Dict[str, Any] = {"field": field, "value": str(value) if value is not None else None, "reason": reason}
        super().__init__(message, "ACCOUNT_VALIDATION_ERROR", details)


class JournalEntryError(AccountingSystemException):
    """Exception for journal entry errors"""
    def __init__(self, reason: str, entry_id: Optional[str] = None, entry_reference: Optional[str] = None):
        message = f"Journal entry error: {reason}"
        details: Dict[str, Any] = {"reason": reason}
        if entry_id:
            details["entry_id"] = entry_id
        if entry_reference:
            details["entry_reference"] = entry_reference
        super().__init__(message, "JOURNAL_ENTRY_ERROR", details)


class BalanceError(AccountingSystemException):
    """Exception for balance errors"""
    def __init__(self, expected_balance: Union[float, str], actual_balance: Union[float, str], account_info: Optional[str] = None):
        message = f"Balance error - Expected: {expected_balance}, Actual: {actual_balance}"
        if account_info:
            message += f" for {account_info}"
        details: Dict[str, Any] = {
            "expected_balance": str(expected_balance),
            "actual_balance": str(actual_balance),
            "difference": str(float(str(actual_balance)) - float(str(expected_balance)))
        }
        if account_info:
            details["account_info"] = account_info
        super().__init__(message, "BALANCE_ERROR", details)


class JournalEntryNotFoundError(AccountingSystemException):
    """Exception for when a journal entry is not found"""
    def __init__(self, entry_id: Optional[str] = None, entry_reference: Optional[str] = None, entry_number: Optional[str] = None):
        identifier = entry_id or entry_reference or entry_number or "unknown"
        field = "reference" if entry_reference else "number" if entry_number else "id"
        message = f"Journal entry not found with {field}: {identifier}"
        super().__init__(message, "JOURNAL_ENTRY_NOT_FOUND", {"identifier": identifier, "field": field})


class ReportGenerationError(AccountingSystemException):
    """Exception for report generation errors"""
    def __init__(self, report_type: str, reason: str, parameters: Optional[Dict[str, Any]] = None):
        message = f"Report generation error for {report_type}: {reason}"
        details: Dict[str, Any] = {"report_type": report_type, "reason": reason}
        if parameters:
            details["parameters"] = parameters
        super().__init__(message, "REPORT_GENERATION_ERROR", details)


# Helper functions to convert exceptions to HTTPException
def raise_user_not_found() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


def raise_insufficient_permissions() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to perform this action"
    )


def raise_invalid_credentials() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_user_already_exists() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User already exists with this email"
    )


def raise_account_locked() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_423_LOCKED,
        detail="Account temporarily locked"
    )


def raise_password_change_required() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Password change required before continuing"
    )


def raise_validation_error(detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail
    )


def raise_authentication_error(detail: str = "Authentication error") -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_account_not_found() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Account not found"
    )


def raise_journal_entry_not_found() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Journal entry not found"
    )


def raise_balance_error(detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Balance error: {detail}"
    )


def raise_business_rule_violation(detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Business rule violation: {detail}"
    )


def raise_session_expired() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired",
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_token_invalid() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_report_generation_error(report_type: str, reason: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to generate {report_type} report: {reason}"
    )


def raise_data_integrity_error(detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Data integrity error: {detail}"
    )


def raise_operation_not_allowed(detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=f"Operation not allowed: {detail}"
    )


def raise_resource_locked(resource_type: str, resource_id: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_423_LOCKED,
        detail=f"{resource_type} {resource_id} is currently locked"
    )


def raise_concurrency_error(detail: str = "Resource was modified by another process") -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Concurrency error: {detail}"
    )


def raise_configuration_error(detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Configuration error: {detail}"
    )


# ====================
# Import-specific exceptions
# ====================

class ImportError(AccountingSystemException):
    """Exception for data import errors"""
    def __init__(
        self, 
        message: str, 
        import_id: Optional[str] = None, 
        row_number: Optional[int] = None,
        field_name: Optional[str] = None,
        import_type: Optional[str] = None
    ):
        details = {
            "import_id": import_id,
            "row_number": row_number,
            "field_name": field_name,
            "import_type": import_type
        }
        super().__init__(message, "IMPORT_ERROR", details)


class ImportValidationError(ImportError):
    """Exception for import validation errors"""
    def __init__(
        self, 
        message: str, 
        field_name: str,
        row_number: Optional[int] = None,
        expected_format: Optional[str] = None
    ):
        super().__init__(
            message=message,
            import_id=None,
            row_number=row_number,
            field_name=field_name,
            import_type="validation"
        )


# Import exception raising functions
def raise_import_error(detail: str, import_id: Optional[str] = None) -> NoReturn:
    """Raise a general import error"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": "Import error",
            "detail": detail,
            "import_id": import_id,
            "error_code": "IMPORT_ERROR"
        }
    )


def raise_import_validation_error(detail: str, field: Optional[str] = None, row: Optional[int] = None) -> NoReturn:
    """Raise an import validation error"""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "Import validation error",
            "detail": detail,
            "field": field,
            "row": row,
            "error_code": "IMPORT_VALIDATION_ERROR"
        }
    )


# Additional exception classes for Sprint 2
class NotFoundError(AccountingSystemException):
    """Generic not found error"""
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, "NOT_FOUND", {"resource": resource, "identifier": identifier})


class ConflictError(AccountingSystemException):
    """Generic conflict error"""
    def __init__(self, message: str, resource: Optional[str] = None):
        super().__init__(message, "CONFLICT", {"resource": resource})


class ValidationError(AccountingSystemException):
    """Generic validation error"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field})


class BusinessLogicError(AccountingSystemException):
    """Business logic violation error"""
    def __init__(self, message: str, rule: Optional[str] = None):
        super().__init__(message, "BUSINESS_LOGIC_ERROR", {"rule": rule})


# Helper functions for Sprint 2
def raise_not_found(detail: str) -> NoReturn:
    """Raise a not found error"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )


def raise_conflict_error(detail: str) -> NoReturn:
    """Raise a conflict error"""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail
    )
