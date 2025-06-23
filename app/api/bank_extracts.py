"""
Bank Extract API endpoints for managing bank statements.
Implements bank statement import and reconciliation workflow following Odoo pattern.
"""
import uuid
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bank_extract import BankExtractStatus
from app.schemas.bank_extract import (
    BankExtractCreate, BankExtractUpdate, BankExtractResponse,
    BankExtractImport, BankExtractImportResult,
    BankExtractWithLines, BankExtractListResponse,
    BankExtractValidation, BankExtractSummary,
    BankExtractLineCreate, BankExtractLineResponse
)
from app.services.bank_extract_service import BankExtractService
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/import", response_model=BankExtractImportResult, status_code=http_status.HTTP_201_CREATED)
async def import_bank_extract(
    extract_data: BankExtractImport,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Importar extracto bancario con líneas
    
    Flujo Odoo:
    1. Importar archivo de extracto (CSV, MT940, etc.)
    2. Validar balances y consistencia
    3. Crear extracto en estado IMPORTED
    4. Preparar para proceso de conciliación
    """
    try:
        service = BankExtractService(db)
        
        file_content = None
        if file:
            file_content = await file.read()
            if not extract_data.file_name:
                extract_data.file_name = file.filename
        
        return service.import_bank_extract(extract_data, current_user.id, file_content)
        
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/", response_model=BankExtractResponse, status_code=http_status.HTTP_201_CREATED)
def create_bank_extract(
    extract_data: BankExtractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear extracto bancario básico
    
    Para crear extractos manualmente sin importar archivo
    """
    try:
        service = BankExtractService(db)
        return service.create_extract(extract_data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, BusinessRuleError) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=BankExtractListResponse)
def get_bank_extracts(
    account_id: Optional[uuid.UUID] = Query(None, description="Filter by account ID"),
    status: Optional[BankExtractStatus] = Query(None, description="Filter by extract status"),
    date_from: Optional[date] = Query(None, description="Filter extracts from this date"),
    date_to: Optional[date] = Query(None, description="Filter extracts to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de extractos bancarios con filtros
    
    Vista principal de extractos bancarios importados
    """
    try:
        service = BankExtractService(db)
        return service.get_extracts(
            account_id=account_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{extract_id}", response_model=BankExtractResponse)
def get_bank_extract(
    extract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener extracto bancario por ID"""
    try:
        service = BankExtractService(db)
        return service.get_extract(extract_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{extract_id}/with-lines", response_model=BankExtractWithLines)
def get_bank_extract_with_lines(
    extract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener extracto bancario con todas sus líneas
    
    Vista detallada para revisión y conciliación
    """
    try:
        service = BankExtractService(db)
        return service.get_extract_with_lines(extract_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{extract_id}/lines", response_model=BankExtractLineResponse, status_code=http_status.HTTP_201_CREATED)
def add_extract_line(
    extract_id: uuid.UUID,
    line_data: BankExtractLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Agregar línea a extracto existente
    
    Para ajustes manuales o correcciones
    """
    try:
        service = BankExtractService(db)
        return service.add_extract_line(extract_id, line_data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{extract_id}/validate", response_model=BankExtractValidation)
def validate_bank_extract(
    extract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validar extracto bancario
    
    Verificar balances, secuencias y consistencia
    Similar a la validación automática de Odoo
    """
    try:
        service = BankExtractService(db)
        return service.validate_extract(extract_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{extract_id}/start-reconciliation", response_model=BankExtractResponse)
def start_reconciliation_process(
    extract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Iniciar proceso de conciliación
    
    Flujo Odoo:
    1. Validar extracto
    2. Cambiar estado a PROCESSING
    3. Permitir conciliación manual y automática
    """
    try:
        service = BankExtractService(db)
        return service.start_reconciliation_process(extract_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{extract_id}/close", response_model=BankExtractResponse)
def close_bank_extract(
    extract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cerrar extracto después de conciliación
    
    Flujo Odoo:
    1. Verificar que está completamente conciliado
    2. Cambiar estado a CLOSED
    3. Bloquear modificaciones
    """
    try:
        service = BankExtractService(db)
        return service.close_extract(extract_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/summary/statistics", response_model=BankExtractSummary)
def get_bank_extract_summary(
    account_id: Optional[uuid.UUID] = Query(None, description="Filter by account ID"),
    date_from: Optional[date] = Query(None, description="Filter extracts from this date"),
    date_to: Optional[date] = Query(None, description="Filter extracts to this date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener resumen estadístico de extractos bancarios
    
    Dashboard de conciliación bancaria
    """
    try:
        # Por ahora retornamos un resumen básico
        from app.models.bank_extract import BankExtract, BankExtractLine
        from decimal import Decimal
        
        query = db.query(BankExtract)
        if account_id:
            query = query.filter(BankExtract.account_id == account_id)
        if date_from:
            query = query.filter(BankExtract.statement_date >= date_from)
        if date_to:
            query = query.filter(BankExtract.statement_date <= date_to)
            
        extracts = query.all()
        
        total_lines = sum(len(e.extract_lines) for e in extracts)
        reconciled_lines = sum(
            len([l for l in e.extract_lines if l.is_reconciled]) 
            for e in extracts
        )
        pending_lines = total_lines - reconciled_lines
        
        total_debits = sum(
            sum(l.debit_amount for l in e.extract_lines)
            for e in extracts
        )
        total_credits = sum(
            sum(l.credit_amount for l in e.extract_lines)
            for e in extracts
        )
        
        by_status = {}
        by_account = {}
        
        for status in BankExtractStatus:
            count = len([e for e in extracts if e.status == status])
            if count > 0:
                by_status[status.value] = count
          # Agrupar por cuenta (simplificado)
        for extract in extracts:
            account_name = str(extract.account_id)  # En el futuro usar el nombre de la cuenta
            by_account[account_name] = by_account.get(account_name, 0) + 1
        
        return BankExtractSummary(
            total_extracts=len(extracts),
            total_lines=total_lines,
            reconciled_lines=reconciled_lines,
            pending_lines=pending_lines,
            total_debits=Decimal(str(total_debits)),
            total_credits=Decimal(str(total_credits)),
            by_status=by_status,
            by_account=by_account
        )
        
    except Exception as e:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Endpoints auxiliares

@router.get("/statuses/", response_model=List[dict])
def get_extract_statuses():
    """Obtener estados de extracto disponibles"""
    return [{"value": s.value, "label": s.value.replace("_", " ").title()} for s in BankExtractStatus]
