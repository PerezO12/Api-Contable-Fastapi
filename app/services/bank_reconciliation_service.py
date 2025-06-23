"""
Bank Reconciliation service for matching bank movements with payments and invoices.
Implements automatic and manual reconciliation following Odoo workflow.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text

from app.models.bank_reconciliation import BankReconciliation, ReconciliationType
from app.models.bank_extract import BankExtract, BankExtractLine, BankExtractStatus
from app.models.payment import Payment, PaymentStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.third_party import ThirdParty
from app.schemas.bank_reconciliation import (
    BankReconciliationCreate, BankReconciliationUpdate, BankReconciliationResponse,
    BulkReconciliationCreate, BulkReconciliationResult,
    AutoReconciliationRequest, AutoReconciliationResult,
    ReconciliationValidation, ReconciliationSummary,
    BankReconciliationListResponse, BankReconciliationWithDetails
)
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class BankReconciliationService:
    """Servicio para conciliación bancaria"""
    
    def __init__(self, db: Session):
        self.db = db

    def create_reconciliation(
        self, 
        reconciliation_data: BankReconciliationCreate, 
        created_by_id: uuid.UUID
    ) -> BankReconciliationResponse:
        """
        Crear conciliación manual
        Vincula línea de extracto con pago o factura
        """
        try:
            # Validar línea de extracto
            extract_line = self.db.query(BankExtractLine).filter(
                BankExtractLine.id == reconciliation_data.extract_line_id
            ).first()
            if not extract_line:
                raise NotFoundError(f"Extract line with id {reconciliation_data.extract_line_id} not found")

            # Validar que la línea no esté completamente conciliada
            if extract_line.is_fully_reconciled:
                raise BusinessRuleError("Extract line is already fully reconciled")

            # Validar pago o factura
            payment = None
            invoice = None
            
            if reconciliation_data.payment_id:
                payment = self.db.query(Payment).filter(
                    Payment.id == reconciliation_data.payment_id
                ).first()
                if not payment:
                    raise NotFoundError(f"Payment with id {reconciliation_data.payment_id} not found")
                
                if payment.status != PaymentStatus.CONFIRMED:
                    raise BusinessRuleError("Payment must be confirmed for reconciliation")

            if reconciliation_data.invoice_id:
                invoice = self.db.query(Invoice).filter(
                    Invoice.id == reconciliation_data.invoice_id
                ).first()
                if not invoice:
                    raise NotFoundError(f"Invoice with id {reconciliation_data.invoice_id} not found")
                
                if invoice.status not in [InvoiceStatus.POSTED, InvoiceStatus.PARTIALLY_PAID]:
                    raise BusinessRuleError("Invoice must be posted for reconciliation")

            # Validar monto
            if reconciliation_data.amount > extract_line.pending_amount:
                raise BusinessRuleError("Reconciliation amount exceeds extract line pending amount")

            # Crear conciliación
            reconciliation = BankReconciliation(
                extract_line_id=reconciliation_data.extract_line_id,
                payment_id=reconciliation_data.payment_id,
                invoice_id=reconciliation_data.invoice_id,
                amount=reconciliation_data.amount,
                reconciliation_type=reconciliation_data.reconciliation_type,
                reconciliation_date=reconciliation_data.reconciliation_date,
                description=reconciliation_data.description,
                notes=reconciliation_data.notes,
                created_by_id=created_by_id
            )

            self.db.add(reconciliation)
            self.db.flush()

            # Actualizar línea de extracto
            extract_line.calculate_pending_amount()

            # Actualizar extracto si todas las líneas están conciliadas
            self._update_extract_status(extract_line.bank_extract_id)

            self.db.commit()

            logger.info(f"Bank reconciliation created: {reconciliation.id}")
            return BankReconciliationResponse.from_orm(reconciliation)

        except Exception as e:
            logger.error(f"Error creating reconciliation: {str(e)}")
            self.db.rollback()
            raise

    def auto_reconcile_extract(
        self,
        extract_id: uuid.UUID,
        request: AutoReconciliationRequest,
        created_by_id: uuid.UUID
    ) -> AutoReconciliationResult:
        """
        Conciliación automática de extracto
        Busca coincidencias automáticas como en Odoo
        """
        try:
            extract = self.db.query(BankExtract).filter(BankExtract.id == extract_id).first()
            if not extract:
                raise NotFoundError(f"Extract with id {extract_id} not found")

            if extract.status != BankExtractStatus.PROCESSING:
                raise BusinessRuleError("Extract must be in processing status for auto reconciliation")

            # Obtener líneas a procesar
            lines_query = self.db.query(BankExtractLine).filter(
                BankExtractLine.bank_extract_id == extract_id,
                BankExtractLine.is_reconciled == False
            )

            if request.extract_line_ids:
                lines_query = lines_query.filter(
                    BankExtractLine.id.in_(request.extract_line_ids)
                )

            lines = lines_query.all()

            processed_lines = 0
            reconciled_lines = 0
            suggested_reconciliations = []
            errors = []

            for line in lines:
                try:
                    # Buscar pagos coincidentes
                    matches = self._find_payment_matches(
                        line, 
                        request.tolerance_amount or Decimal('0'),
                        request.tolerance_days or 0,
                        request.date_range_start,
                        request.date_range_end
                    )

                    processed_lines += 1
                    
                    if matches:
                        # Crear conciliación automática con la mejor coincidencia
                        best_match = matches[0]  # Ya ordenado por prioridad
                        
                        reconciliation_data = BankReconciliationCreate(
                            extract_line_id=line.id,
                            payment_id=best_match['payment_id'] if 'payment_id' in best_match else None,
                            invoice_id=best_match['invoice_id'] if 'invoice_id' in best_match else None,
                            amount=min(line.pending_amount, best_match['amount']),
                            reconciliation_type=ReconciliationType.AUTOMATIC,
                            reconciliation_date=date.today(),
                            description=f"Auto reconciliation: {best_match['match_reason']}",
                            notes=f"Automatically matched with confidence: {best_match.get('confidence', 0)}"
                        )

                        reconciliation = self.create_reconciliation(reconciliation_data, created_by_id)
                        suggested_reconciliations.append(reconciliation)
                        reconciled_lines += 1

                except Exception as e:
                    errors.append(f"Line {line.sequence}: {str(e)}")

            logger.info(f"Auto reconciliation completed: {reconciled_lines}/{processed_lines} lines")

            return AutoReconciliationResult(
                processed_lines=processed_lines,
                reconciled_lines=reconciled_lines,
                suggested_reconciliations=suggested_reconciliations,
                errors=errors
            )

        except Exception as e:
            logger.error(f"Error in auto reconciliation: {str(e)}")
            self.db.rollback()
            raise

    def _find_payment_matches(
        self, 
        extract_line: BankExtractLine, 
        tolerance_amount: Decimal,
        tolerance_days: int,
        date_range_start: Optional[date] = None,
        date_range_end: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar pagos que coincidan con la línea de extracto
        Algoritmo similar al de Odoo
        """
        matches = []
        line_amount = abs(extract_line.credit_amount - extract_line.debit_amount)

        # Rango de fechas para búsqueda
        search_date_start = extract_line.transaction_date - timedelta(days=tolerance_days)
        search_date_end = extract_line.transaction_date + timedelta(days=tolerance_days)

        if date_range_start:
            search_date_start = max(search_date_start, date_range_start)
        if date_range_end:
            search_date_end = min(search_date_end, date_range_end)

        # Buscar pagos
        payments_query = self.db.query(Payment).filter(
            Payment.status == PaymentStatus.CONFIRMED,
            Payment.payment_date >= search_date_start,
            Payment.payment_date <= search_date_end
        )

        for payment in payments_query.all():
            # Verificar si el pago ya está conciliado
            existing_reconciliation = self.db.query(BankReconciliation).filter(
                BankReconciliation.payment_id == payment.id
            ).first()
            
            if existing_reconciliation:
                continue

            # Calcular score de coincidencia
            amount_diff = abs(payment.amount - line_amount)
            date_diff = abs((payment.payment_date - extract_line.transaction_date).days)

            # Verificar tolerancias
            if amount_diff <= tolerance_amount and date_diff <= tolerance_days:
                score = 100 - (amount_diff * 10) - (date_diff * 5)
                
                # Bonus por coincidencias exactas
                if amount_diff == 0:
                    score += 50
                if date_diff == 0:
                    score += 30

                # Bonus por coincidencia en referencia/descripción
                if payment.reference and extract_line.reference:
                    if payment.reference.lower() in extract_line.reference.lower():
                        score += 20

                match_reason = f"Amount: {payment.amount}, Date: {payment.payment_date}"
                if amount_diff == 0 and date_diff == 0:
                    match_reason = "Exact match"
                elif amount_diff == 0:
                    match_reason = "Exact amount match"
                elif date_diff == 0:
                    match_reason = "Exact date match"

                matches.append({
                    'payment_id': payment.id,
                    'amount': payment.amount,
                    'score': score,
                    'match_reason': match_reason,
                    'amount_diff': amount_diff,
                    'date_diff': date_diff
                })

        # Ordenar por score (mejor primero)
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches[:5]  # Retornar top 5 coincidencias

    def validate_reconciliation(self, reconciliation_id: uuid.UUID) -> ReconciliationValidation:
        """Validar conciliación"""
        reconciliation = self.db.query(BankReconciliation).filter(
            BankReconciliation.id == reconciliation_id
        ).first()
        
        if not reconciliation:
            raise NotFoundError(f"Reconciliation with id {reconciliation_id} not found")

        errors = []
        warnings = []

        # Validar línea de extracto
        extract_line = reconciliation.extract_line
        extract_line_amount = abs(extract_line.credit_amount - extract_line.debit_amount)
        
        # Calcular total conciliado para esta línea
        total_reconciled = self.db.query(func.sum(BankReconciliation.amount)).filter(
            BankReconciliation.extract_line_id == extract_line.id
        ).scalar() or Decimal('0')

        remaining_amount = extract_line_amount - total_reconciled

        # Validaciones
        if reconciliation.amount > remaining_amount + reconciliation.amount:
            errors.append("Reconciliation amount exceeds extract line remaining amount")

        if reconciliation.amount <= 0:
            errors.append("Reconciliation amount must be positive")

        # Validar fechas
        if reconciliation.reconciliation_date > date.today():
            warnings.append("Reconciliation date is in the future")

        is_valid = len(errors) == 0

        return ReconciliationValidation(
            is_valid=is_valid,
            extract_line_amount=extract_line_amount,
            reconciled_amount=total_reconciled,
            remaining_amount=remaining_amount,
            errors=errors,
            warnings=warnings
        )

    def confirm_reconciliations(
        self, 
        reconciliation_ids: List[uuid.UUID], 
        confirmed_by_id: uuid.UUID
    ) -> List[BankReconciliationResponse]:
        """Confirmar múltiples conciliaciones"""
        try:
            reconciliations = self.db.query(BankReconciliation).filter(
                BankReconciliation.id.in_(reconciliation_ids)
            ).all()

            if len(reconciliations) != len(reconciliation_ids):
                raise NotFoundError("Some reconciliations not found")

            confirmed = []
            for reconciliation in reconciliations:
                reconciliation.is_confirmed = True
                reconciliation.confirmed_by_id = confirmed_by_id
                reconciliation.confirmed_at = datetime.utcnow()
                confirmed.append(BankReconciliationResponse.from_orm(reconciliation))

                # Actualizar línea de extracto
                reconciliation.extract_line.calculate_pending_amount()

            self.db.commit()

            logger.info(f"Confirmed {len(confirmed)} reconciliations")
            return confirmed

        except Exception as e:
            logger.error(f"Error confirming reconciliations: {str(e)}")
            self.db.rollback()
            raise

    def _update_extract_status(self, extract_id: uuid.UUID):
        """Actualizar estado del extracto basado en conciliación"""
        extract = self.db.query(BankExtract).filter(BankExtract.id == extract_id).first()
        if not extract:
            return

        # Verificar si todas las líneas están conciliadas
        total_lines = len(extract.extract_lines)
        reconciled_lines = sum(1 for line in extract.extract_lines if line.is_fully_reconciled)

        if reconciled_lines == total_lines and total_lines > 0:
            extract.status = BankExtractStatus.RECONCILED
            logger.info(f"Extract {extract_id} fully reconciled")

    def get_reconciliations(
        self,
        extract_id: Optional[uuid.UUID] = None,
        payment_id: Optional[uuid.UUID] = None,
        invoice_id: Optional[uuid.UUID] = None,
        is_confirmed: Optional[bool] = None,
        page: int = 1,
        size: int = 50
    ) -> BankReconciliationListResponse:
        """Obtener lista de conciliaciones con filtros"""
        query = self.db.query(BankReconciliation)

        # Aplicar filtros
        if extract_id:
            query = query.join(BankExtractLine).filter(
                BankExtractLine.bank_extract_id == extract_id
            )
        
        if payment_id:
            query = query.filter(BankReconciliation.payment_id == payment_id)
            
        if invoice_id:
            query = query.filter(BankReconciliation.invoice_id == invoice_id)
            
        if is_confirmed is not None:
            query = query.filter(BankReconciliation.is_confirmed == is_confirmed)

        # Contar total
        total = query.count()

        # Paginación
        offset = (page - 1) * size
        reconciliations = query.order_by(desc(BankReconciliation.created_at)).offset(offset).limit(size).all()
        
        return BankReconciliationListResponse(
            reconciliations=[BankReconciliationResponse.from_orm(r) for r in reconciliations],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )

    def list_reconciliations(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        account_id: Optional[uuid.UUID] = None,
        extract_id: Optional[uuid.UUID] = None    ) -> BankReconciliationListResponse:
        """Listar conciliaciones con filtros"""
        return self.get_reconciliations(
            extract_id=extract_id,
            is_confirmed=status == "confirmed" if status else None,
            page=(skip // limit) + 1,
            size=limit
        )

    def get_reconciliation(self, reconciliation_id: uuid.UUID) -> BankReconciliationResponse:
        """Obtener conciliación por ID"""
        reconciliation = self.db.query(BankReconciliation).filter(
            BankReconciliation.id == reconciliation_id
        ).first()
        if not reconciliation:
            raise NotFoundError(f"Bank reconciliation with id {reconciliation_id} not found")
        
        return BankReconciliationResponse.from_orm(reconciliation)

    def update_reconciliation(
        self, 
        reconciliation_id: uuid.UUID, 
        reconciliation_data: BankReconciliationUpdate, 
        updated_by_id: uuid.UUID
    ) -> BankReconciliationResponse:
        """Actualizar conciliación"""
        reconciliation = self.db.query(BankReconciliation).filter(
            BankReconciliation.id == reconciliation_id
        ).first()
        if not reconciliation:
            raise NotFoundError(f"Bank reconciliation with id {reconciliation_id} not found")

        # Verificar que se puede actualizar
        if reconciliation.is_confirmed:
            raise BusinessRuleError("Cannot update confirmed reconciliation")        # Actualizar campos
        update_data = reconciliation_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(reconciliation, field, value)

        reconciliation.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Bank reconciliation updated: {reconciliation_id}")
        return BankReconciliationResponse.from_orm(reconciliation)

    def delete_reconciliation(self, reconciliation_id: uuid.UUID, deleted_by_id: uuid.UUID):
        """Eliminar conciliación"""
        reconciliation = self.db.query(BankReconciliation).filter(
            BankReconciliation.id == reconciliation_id
        ).first()
        if not reconciliation:
            raise NotFoundError(f"Bank reconciliation with id {reconciliation_id} not found")

        # Verificar que se puede eliminar
        if reconciliation.is_confirmed:
            raise BusinessRuleError("Cannot delete confirmed reconciliation")

        self.db.delete(reconciliation)
        self.db.commit()

        logger.info(f"Bank reconciliation deleted: {reconciliation_id}")

    def confirm_reconciliation(self, reconciliation_id: uuid.UUID, confirmed_by_id: uuid.UUID) -> BankReconciliationResponse:
        """Confirmar conciliación"""
        reconciliation = self.db.query(BankReconciliation).filter(
            BankReconciliation.id == reconciliation_id
        ).first()
        if not reconciliation:
            raise NotFoundError(f"Bank reconciliation with id {reconciliation_id} not found")

        if reconciliation.is_confirmed:
            raise BusinessRuleError("Reconciliation is already confirmed")

        reconciliation.is_confirmed = True
        reconciliation.confirmed_by_id = confirmed_by_id
        reconciliation.confirmed_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Bank reconciliation confirmed: {reconciliation_id}")
        return BankReconciliationResponse.from_orm(reconciliation)

    def cancel_reconciliation(self, reconciliation_id: uuid.UUID, cancelled_by_id: uuid.UUID) -> BankReconciliationResponse:
        """Cancelar conciliación"""
        reconciliation = self.db.query(BankReconciliation).filter(
            BankReconciliation.id == reconciliation_id
        ).first()
        if not reconciliation:
            raise NotFoundError(f"Bank reconciliation with id {reconciliation_id} not found")

        if reconciliation.is_confirmed:
            raise BusinessRuleError("Cannot cancel confirmed reconciliation")        # Marcar como cancelada (puedes agregar un campo cancelled si lo necesitas)
        reconciliation.is_confirmed = False
        reconciliation.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Bank reconciliation cancelled: {reconciliation_id}")
        return BankReconciliationResponse.from_orm(reconciliation)

    def auto_reconcile(
        self,
        extract_id: uuid.UUID,
        account_id: Optional[uuid.UUID] = None,
        tolerance_amount: Optional[Decimal] = None,
        tolerance_days: Optional[int] = None,
        created_by_id: Optional[uuid.UUID] = None
    ):
        """Conciliación automática usando parámetros simples"""
        from app.schemas.bank_reconciliation import BankReconciliationAutoResponse
        
        # Obtener líneas del extracto
        extract_lines = self.db.query(BankExtractLine).filter(
            BankExtractLine.bank_extract_id == extract_id,
            BankExtractLine.is_reconciled == False
        ).all()
        
        # Crear request para el método existente
        from app.schemas.bank_reconciliation import AutoReconciliationRequest
        request = AutoReconciliationRequest(
            tolerance_amount=tolerance_amount or Decimal('0.01'),
            tolerance_days=tolerance_days or 7,
            date_range_start=None,
            date_range_end=None,
            extract_line_ids=[line.id for line in extract_lines]
        )
        
        # Usar método existente
        result = self.auto_reconcile_extract(extract_id, request, created_by_id or uuid.uuid4())
        
        # Calcular monto conciliado
        reconciled_amount = Decimal('0')
        for reconciliation in result.suggested_reconciliations:
            reconciled_amount += reconciliation.amount
        
        # Convertir a la respuesta esperada
        return BankReconciliationAutoResponse(
            processed_lines=result.processed_lines,
            reconciled_lines=result.reconciled_lines,
            reconciled_amount=reconciled_amount,
            unreconciled_lines=result.processed_lines - result.reconciled_lines,
            reconciliations=result.suggested_reconciliations
        )
