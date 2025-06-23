"""
Bank Extract service for importing and managing bank statements.
Handles bank statement import, validation, and processing following Odoo workflow.
"""
import uuid
import hashlib
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.bank_extract import BankExtract, BankExtractLine, BankExtractStatus, BankExtractLineType
from app.models.account import Account
from app.models.user import User
from app.schemas.bank_extract import (
    BankExtractCreate, BankExtractUpdate, BankExtractResponse,
    BankExtractLineCreate, BankExtractLineResponse,
    BankExtractImport, BankExtractImportResult,
    BankExtractWithLines, BankExtractListResponse,
    BankExtractValidation, BankExtractSummary
)
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.utils.logging import get_logger
from app.utils.codes import generate_code

logger = get_logger(__name__)


class BankExtractService:
    """Servicio para gestión de extractos bancarios"""
    
    def __init__(self, db: Session):
        self.db = db

    def import_bank_extract(
        self, 
        extract_data: BankExtractImport, 
        created_by_id: uuid.UUID,
        file_content: Optional[bytes] = None
    ) -> BankExtractImportResult:
        """
        Importar extracto bancario con líneas
        Flujo similar a Odoo: importación → validación → procesamiento
        """
        try:
            # Validar que la cuenta existe
            account = self.db.query(Account).filter(
                Account.id == extract_data.account_id
            ).first()
            if not account:
                raise NotFoundError(f"Account with id {extract_data.account_id} not found")

            # Calcular hash del archivo para evitar duplicados
            file_hash = None
            if file_content:
                file_hash = hashlib.md5(file_content).hexdigest()
                
                # Verificar si ya existe un extracto con el mismo hash
                existing = self.db.query(BankExtract).filter(
                    BankExtract.file_hash == file_hash
                ).first()
                if existing:
                    raise BusinessRuleError(f"Bank extract already imported: {existing.name}")

            # Crear el extracto
            extract = BankExtract(
                name=extract_data.name,
                reference=extract_data.reference,
                account_id=extract_data.account_id,
                statement_date=extract_data.statement_date,
                start_date=extract_data.start_date,
                end_date=extract_data.end_date,
                starting_balance=extract_data.starting_balance,
                ending_balance=extract_data.ending_balance,
                currency_code=extract_data.currency_code,
                description=extract_data.description,
                notes=extract_data.notes,
                file_name=extract_data.file_name,
                file_hash=file_hash,
                created_by_id=created_by_id,
                imported_at=datetime.utcnow()
            )

            self.db.add(extract)
            self.db.flush()

            # Importar líneas
            imported_lines = 0
            errors = []
            warnings = []

            for line_data in extract_data.lines:
                try:
                    # Crear línea de extracto
                    line = BankExtractLine(
                        bank_extract_id=extract.id,
                        sequence=line_data.sequence,
                        transaction_date=line_data.transaction_date,
                        value_date=line_data.value_date,
                        reference=line_data.reference,
                        bank_reference=line_data.bank_reference,
                        check_number=line_data.check_number,
                        description=line_data.description,
                        additional_info=line_data.additional_info,
                        line_type=line_data.line_type,
                        debit_amount=line_data.debit_amount,
                        credit_amount=line_data.credit_amount,
                        balance=line_data.balance,
                        partner_name=line_data.partner_name,
                        partner_account=line_data.partner_account,
                        created_by_id=created_by_id
                    )

                    # Calcular monto pendiente
                    line.pending_amount = abs(line.credit_amount - line.debit_amount)

                    self.db.add(line)
                    imported_lines += 1

                except Exception as e:
                    errors.append(f"Line {line_data.sequence}: {str(e)}")

            self.db.flush()

            # Validar el extracto
            validation = self.validate_extract(extract.id)
            if not validation.is_valid:
                warnings.extend(validation.warnings)
                if validation.errors:
                    errors.extend(validation.errors)

            # Cambiar estado si todo está bien
            if not errors:
                extract.status = BankExtractStatus.IMPORTED
            
            self.db.commit()

            logger.info(f"Bank extract imported: {extract.id}, {imported_lines} lines")
            
            return BankExtractImportResult(
                extract_id=extract.id,
                total_lines=len(extract_data.lines),
                imported_lines=imported_lines,
                errors=errors,
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Error importing bank extract: {str(e)}")
            self.db.rollback()
            raise

    def create_extract(self, extract_data: BankExtractCreate, created_by_id: uuid.UUID) -> BankExtractResponse:
        """Crear extracto bancario básico"""
        try:
            # Validar cuenta
            account = self.db.query(Account).filter(
                Account.id == extract_data.account_id
            ).first()
            if not account:
                raise NotFoundError(f"Account with id {extract_data.account_id} not found")

            extract = BankExtract(
                name=extract_data.name,
                reference=extract_data.reference,
                account_id=extract_data.account_id,
                statement_date=extract_data.statement_date,
                start_date=extract_data.start_date,
                end_date=extract_data.end_date,
                starting_balance=extract_data.starting_balance,
                ending_balance=extract_data.ending_balance,
                currency_code=extract_data.currency_code,
                description=extract_data.description,
                notes=extract_data.notes,
                file_name=extract_data.file_name,
                created_by_id=created_by_id,
                imported_at=datetime.utcnow()
            )

            self.db.add(extract)
            self.db.commit()

            logger.info(f"Bank extract created: {extract.id}")
            return BankExtractResponse.from_orm(extract)

        except Exception as e:
            logger.error(f"Error creating bank extract: {str(e)}")
            self.db.rollback()
            raise

    def get_extract(self, extract_id: uuid.UUID) -> BankExtractResponse:
        """Obtener extracto por ID"""
        extract = self.db.query(BankExtract).filter(BankExtract.id == extract_id).first()
        if not extract:
            raise NotFoundError(f"Bank extract with id {extract_id} not found")
        
        return BankExtractResponse.from_orm(extract)

    def get_extract_with_lines(self, extract_id: uuid.UUID) -> BankExtractWithLines:
        """Obtener extracto con líneas"""
        extract = self.db.query(BankExtract).filter(BankExtract.id == extract_id).first()
        if not extract:
            raise NotFoundError(f"Bank extract with id {extract_id} not found")
        
        lines = self.db.query(BankExtractLine).filter(
            BankExtractLine.bank_extract_id == extract_id
        ).order_by(BankExtractLine.sequence).all()
        
        return BankExtractWithLines(
            **BankExtractResponse.from_orm(extract).dict(),
            lines=[BankExtractLineResponse.from_orm(line) for line in lines]
        )

    def add_extract_line(
        self, 
        extract_id: uuid.UUID, 
        line_data: BankExtractLineCreate, 
        created_by_id: uuid.UUID
    ) -> BankExtractLineResponse:
        """Agregar línea a extracto"""
        extract = self.db.query(BankExtract).filter(BankExtract.id == extract_id).first()
        if not extract:
            raise NotFoundError(f"Bank extract with id {extract_id} not found")

        if extract.status != BankExtractStatus.IMPORTED:
            raise BusinessRuleError("Cannot add lines to extract in current status")

        line = BankExtractLine(
            bank_extract_id=extract_id,
            sequence=line_data.sequence,
            transaction_date=line_data.transaction_date,
            value_date=line_data.value_date,
            reference=line_data.reference,
            bank_reference=line_data.bank_reference,
            check_number=line_data.check_number,
            description=line_data.description,
            additional_info=line_data.additional_info,
            line_type=line_data.line_type,
            debit_amount=line_data.debit_amount,
            credit_amount=line_data.credit_amount,
            balance=line_data.balance,
            partner_name=line_data.partner_name,
            partner_account=line_data.partner_account,
            created_by_id=created_by_id
        )

        # Calcular monto pendiente
        line.pending_amount = abs(line.credit_amount - line.debit_amount)

        self.db.add(line)
        self.db.commit()

        logger.info(f"Extract line added to extract {extract_id}")
        return BankExtractLineResponse.from_orm(line)

    def validate_extract(self, extract_id: uuid.UUID) -> BankExtractValidation:
        """
        Validar extracto bancario
        Verificar balances y consistencia como en Odoo
        """
        extract = self.db.query(BankExtract).filter(BankExtract.id == extract_id).first()
        if not extract:
            raise NotFoundError(f"Bank extract with id {extract_id} not found")

        lines = self.db.query(BankExtractLine).filter(
            BankExtractLine.bank_extract_id == extract_id
        ).all()

        errors = []
        warnings = []

        # Calcular totales
        total_debits = sum(line.debit_amount for line in lines)
        total_credits = sum(line.credit_amount for line in lines)
        
        # Calcular saldo final teórico
        calculated_ending_balance = extract.starting_balance + total_credits - total_debits
        balance_difference = extract.ending_balance - calculated_ending_balance

        # Validaciones
        if abs(balance_difference) > Decimal('0.01'):  # Tolerancia de 1 centavo
            errors.append(f"Balance mismatch: expected {calculated_ending_balance}, got {extract.ending_balance}")

        # Verificar secuencias
        sequences = [line.sequence for line in lines]
        if len(sequences) != len(set(sequences)):
            errors.append("Duplicate sequence numbers found")

        # Verificar fechas
        for line in lines:
            if line.transaction_date < extract.start_date or line.transaction_date > extract.end_date:
                warnings.append(f"Line {line.sequence}: transaction date outside extract period")

        is_valid = len(errors) == 0

        return BankExtractValidation(
            is_valid=is_valid,
            balance_difference=balance_difference,
            total_debits=Decimal(str(total_debits)),
            total_credits=Decimal(str(total_credits)),
            calculated_ending_balance=calculated_ending_balance,
            errors=errors,
            warnings=warnings
        )

    def get_extracts(
        self,
        account_id: Optional[uuid.UUID] = None,
        status: Optional[BankExtractStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        size: int = 50
    ) -> BankExtractListResponse:
        """Obtener lista de extractos con filtros"""
        query = self.db.query(BankExtract)

        # Aplicar filtros
        if account_id:
            query = query.filter(BankExtract.account_id == account_id)
        
        if status:
            query = query.filter(BankExtract.status == status)
            
        if date_from:
            query = query.filter(BankExtract.statement_date >= date_from)
            
        if date_to:
            query = query.filter(BankExtract.statement_date <= date_to)

        # Contar total
        total = query.count()

        # Paginación
        offset = (page - 1) * size
        extracts = query.order_by(desc(BankExtract.statement_date)).offset(offset).limit(size).all()

        return BankExtractListResponse(
            extracts=[BankExtractResponse.from_orm(e) for e in extracts],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )

    def start_reconciliation_process(self, extract_id: uuid.UUID) -> BankExtractResponse:
        """
        Iniciar proceso de conciliación
        Cambiar estado del extracto a "processing"
        """
        extract = self.db.query(BankExtract).filter(BankExtract.id == extract_id).first()
        if not extract:
            raise NotFoundError(f"Bank extract with id {extract_id} not found")

        if extract.status != BankExtractStatus.IMPORTED:
            raise BusinessRuleError("Extract must be imported to start reconciliation")

        # Validar antes de iniciar conciliación
        validation = self.validate_extract(extract_id)
        if not validation.is_valid:
            raise BusinessRuleError(f"Extract validation failed: {', '.join(validation.errors)}")

        extract.status = BankExtractStatus.PROCESSING
        self.db.commit()

        logger.info(f"Reconciliation process started for extract {extract_id}")
        return BankExtractResponse.from_orm(extract)

    def close_extract(self, extract_id: uuid.UUID, closed_by_id: uuid.UUID) -> BankExtractResponse:
        """
        Cerrar extracto después de conciliación completa
        """
        extract = self.db.query(BankExtract).filter(BankExtract.id == extract_id).first()
        if not extract:
            raise NotFoundError(f"Bank extract with id {extract_id} not found")

        if extract.status != BankExtractStatus.RECONCILED:
            raise BusinessRuleError("Extract must be reconciled to close")

        extract.status = BankExtractStatus.CLOSED
        extract.reconciled_by_id = closed_by_id
        extract.reconciled_at = datetime.utcnow()
        
        self.db.commit()

        logger.info(f"Extract closed: {extract_id}")
        return BankExtractResponse.from_orm(extract)
