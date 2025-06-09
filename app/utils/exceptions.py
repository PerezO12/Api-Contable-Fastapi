from typing import NoReturn
from fastapi import HTTPException, status


class AccountingSystemException(Exception):
    """Excepción base para el sistema contable"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class UserNotFoundException(AccountingSystemException):
    """Excepción para cuando no se encuentra un usuario"""
    pass


class UserNotFoundError(AccountingSystemException):
    """Alias para UserNotFoundException - mantener compatibilidad"""
    pass


class UserValidationError(AccountingSystemException):
    """Excepción para errores de validación de usuarios"""
    pass


class AuthenticationError(AccountingSystemException):
    """Excepción para errores de autenticación"""
    pass


class PasswordValidationError(AccountingSystemException):
    """Excepción para errores de validación de contraseñas"""
    pass


class SessionError(AccountingSystemException):
    """Excepción para errores de sesión"""
    pass


class TokenError(AccountingSystemException):
    """Excepción para errores de tokens"""
    pass


class InsufficientPermissionsException(AccountingSystemException):
    """Excepción para permisos insuficientes"""
    pass


class InvalidPasswordException(AccountingSystemException):
    """Excepción para contraseñas inválidas"""
    pass


class UserAlreadyExistsException(AccountingSystemException):
    """Excepción para usuarios que ya existen"""
    pass


class AccountLockedException(AccountingSystemException):
    """Excepción para cuentas bloqueadas"""
    pass


class AccountNotFoundError(AccountingSystemException):
    """Excepción para cuando no se encuentra una cuenta"""
    pass


class AccountValidationError(AccountingSystemException):
    """Excepción para errores de validación de cuentas"""
    pass


class JournalEntryError(AccountingSystemException):
    """Excepción para errores en asientos contables"""
    pass


class BalanceError(AccountingSystemException):
    """Excepción para errores de balance"""
    pass


class JournalEntryNotFoundError(AccountingSystemException):
    """Excepción para cuando no se encuentra un asiento contable"""
    pass


class ReportGenerationError(AccountingSystemException):
    """Excepción para errores en la generación de reportes"""
    pass


# Funciones helper para convertir excepciones a HTTPException
def raise_user_not_found() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuario no encontrado"
    )


def raise_insufficient_permissions() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permisos insuficientes para realizar esta acción"
    )


def raise_invalid_credentials() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_user_already_exists() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Ya existe un usuario con este email"
    )


def raise_account_locked() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_423_LOCKED,
        detail="Cuenta bloqueada temporalmente"
    )


def raise_password_change_required() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Debe cambiar su contraseña antes de continuar"
    )


def raise_validation_error(detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail
    )


def raise_authentication_error(detail: str = "Error de autenticación"):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_account_not_found():
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Cuenta contable no encontrada"
    )


def raise_journal_entry_not_found() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Asiento contable no encontrado"
    )


def raise_balance_error(detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Error de balance: {detail}"
    )


def raise_business_rule_violation(detail: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Violación de regla de negocio: {detail}"
    )


def raise_session_expired():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_token_invalid():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
