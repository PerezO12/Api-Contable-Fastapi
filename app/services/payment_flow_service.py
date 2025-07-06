"""
Simplified async PaymentFlowService focused on core functionality.
This is a clean implementation that provides the essential payment workflow capabilities.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, func, delete

from app.models.payment import Payment, PaymentInvoice, PaymentStatus, PaymentType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.journal import Journal, JournalType
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType, TransactionOrigin
from app.models.account import Account
from app.schemas.payment import PaymentResponse
from app.services.payment_service import PaymentService
from app.utils.exceptions import NotFoundError, ValidationError, BusinessRuleError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PaymentFlowService:
    """
    Async Payment Flow Service for orchestrating complete payment workflows.
    
    Responsibilities:
    - Payment confirmation with journal entry creation
    - Payment validation and business rule enforcement
    - Payment-invoice reconciliation
    - Bulk payment operations
    
    Architecture:
    - Uses async/await throughout
    - Delegates basic CRUD to PaymentService
    - Focuses on workflow orchestration
    - Clean separation from other services
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payment_service = PaymentService(db)
    
    async def confirm_payment(self, payment_id: uuid.UUID, confirmed_by_id: uuid.UUID, force: bool = False) -> PaymentResponse:
        """
        Confirm/Post payment: DRAFT → POSTED (contabilización)
        
        FLUJO CORRECTO:
        1. DRAFT → POSTED (se contabiliza y genera journal entry)
        2. POSTED → PAID (cuando se concilie, pero por ahora va directo a PAID)
        
        Este método maneja la contabilización:
        1. Valida que el pago esté en DRAFT
        2. Crea journal entry para contabilidad
        3. Actualiza payment status a POSTED (temporalmente PAID hasta implementar conciliación)
        4. Procesa reconciliación de facturas
        """
        try:
            logger.info(f"🚀 [CONFIRM_PAYMENT] Starting confirmation process for payment {payment_id}")
            logger.info(f"🔍 [CONFIRM_PAYMENT] Confirmed by user: {confirmed_by_id}, Force mode: {force}")
            
            # Get payment with all required relations
            logger.debug(f"📋 [CONFIRM_PAYMENT] Loading payment {payment_id} with all relations")
            payment_result = await self.db.execute(
                select(Payment).options(
                    selectinload(Payment.payment_invoices).selectinload(PaymentInvoice.invoice),
                    selectinload(Payment.third_party),
                    selectinload(Payment.account),
                    selectinload(Payment.journal)
                ).where(Payment.id == payment_id)
            )
            payment = payment_result.scalar_one_or_none()
            
            if not payment:
                error_msg = f"Payment with id {payment_id} not found"
                logger.error(f"❌ [CONFIRM_PAYMENT] {error_msg}")
                raise NotFoundError(error_msg)
            
            logger.info(f"✅ [CONFIRM_PAYMENT] Payment {payment.number} loaded successfully")
            logger.info(f"📊 [CONFIRM_PAYMENT] Payment details: Status={payment.status}, Amount={payment.amount}, Type={payment.payment_type}")
            logger.info(f"🏢 [CONFIRM_PAYMENT] Third party: {payment.third_party.name if payment.third_party else 'None'}")
            logger.info(f"💰 [CONFIRM_PAYMENT] Account: {payment.account.name if payment.account else 'None'}")
            
            # Check if payment is in DRAFT status (only status allowed for confirmation)
            if payment.status != PaymentStatus.DRAFT:
                error_msg = f"Payment can only be confirmed from DRAFT status, current: {payment.status}"
                logger.error(f"❌ [CONFIRM_PAYMENT] Payment {payment.number} - {error_msg}")
                raise BusinessRuleError(error_msg)
            
            logger.info(f"✅ [CONFIRM_PAYMENT] Payment {payment.number} status validation passed (DRAFT)")
            
            # Validate payment for confirmation (skip if force=True)
            if not force:
                logger.info(f"🔍 [CONFIRM_PAYMENT] Starting validation for payment {payment.number}")
                validation_errors = await self._validate_payment_for_confirmation(payment)
                
                if validation_errors:
                    error_msg = f"Payment validation failed: {'; '.join(validation_errors)}"
                    logger.error(f"❌ [CONFIRM_PAYMENT] Payment {payment.number} - {error_msg}")
                    raise BusinessRuleError(error_msg)
                
                logger.info(f"✅ [CONFIRM_PAYMENT] Payment {payment.number} validation passed")
            else:
                logger.warning(f"⚠️ [CONFIRM_PAYMENT] FORCE MODE: Skipping validation for payment {payment.number}")
            
            # Ensure payment has required journal
            if not payment.journal_id:
                logger.info(f"🔧 [CONFIRM_PAYMENT] Payment {payment.number} missing journal, getting default journal")
                journal_id = await self._get_default_payment_journal(payment.payment_type)
                payment.journal_id = journal_id
                logger.info(f"✅ [CONFIRM_PAYMENT] Payment {payment.number} assigned journal ID: {journal_id}")
            
            # Create journal entry for the payment
            logger.info(f"📝 [CONFIRM_PAYMENT] Creating journal entry for payment {payment.number}")
            journal_entry = await self._create_payment_journal_entry(payment, confirmed_by_id)
            payment.journal_entry_id = journal_entry.id
            logger.info(f"✅ [CONFIRM_PAYMENT] Journal entry {journal_entry.number} created for payment {payment.number}")
            
            # Update payment status to POSTED (will be PAID until reconciliation is implemented)
            logger.info(f"📝 [CONFIRM_PAYMENT] Updating payment {payment.number} status to POSTED")
            payment.status = PaymentStatus.POSTED  # Temporalmente POSTED, luego será PAID
            payment.posted_by_id = confirmed_by_id
            payment.posted_at = datetime.utcnow()
            payment.confirmed_by_id = confirmed_by_id
            payment.confirmed_at = datetime.utcnow()
            payment.updated_at = datetime.utcnow()
            
            logger.info(f"✅ [CONFIRM_PAYMENT] Payment {payment.number} status updated to {payment.status}")
            
            # Process invoice reconciliation
            logger.info(f"🔗 [CONFIRM_PAYMENT] Processing invoice reconciliation for payment {payment.number}")
            await self._reconcile_payment_invoices(payment)
            logger.info(f"✅ [CONFIRM_PAYMENT] Invoice reconciliation completed for payment {payment.number}")
            
            await self.db.commit()
            
            logger.info(f"🎉 [CONFIRM_PAYMENT] Payment {payment.number} processed successfully - Final Status: {payment.status}")
            return PaymentResponse.from_orm(payment)
            
        except Exception as e:
            logger.error(f"💥 [CONFIRM_PAYMENT] Error confirming payment {payment_id}: {str(e)}")
            logger.error(f"💥 [CONFIRM_PAYMENT] Exception type: {type(e).__name__}")
            await self.db.rollback()
            raise
    
    async def reset_payment_to_draft(self, payment_id: uuid.UUID, reset_by_id: uuid.UUID) -> PaymentResponse:
        """
        Reset payment to DRAFT from any status
        
        Handles different payment states:
        - DRAFT: Already in draft, no action needed (returns success)
        - CONFIRMED: Reset to DRAFT, no journal entry to remove  
        - POSTED: Remove journal entry and reset to DRAFT
        - CANCELLED: Remove journal entry (if exists) and reset to DRAFT
        """
        try:
            logger.info(f"Resetting payment {payment_id} to draft")
            
            payment_result = await self.db.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            payment = payment_result.scalar_one_or_none()
            
            if not payment:
                raise NotFoundError(f"Payment with id {payment_id} not found")
            
            # If already in DRAFT, just return success
            if payment.status == PaymentStatus.DRAFT:
                logger.info(f"Payment {payment.number} is already in DRAFT status")
                return PaymentResponse.from_orm(payment)
            
            # Handle different payment states
            if payment.status in [PaymentStatus.POSTED, PaymentStatus.CANCELLED]:
                # For POSTED and CANCELLED payments, remove journal entry if it exists
                if payment.journal_entry_id:
                    journal_entry_result = await self.db.execute(
                        select(JournalEntry).where(JournalEntry.id == payment.journal_entry_id)
                    )
                    journal_entry = journal_entry_result.scalar_one_or_none()
                    
                    if journal_entry:
                        # Delete journal entry lines first
                        await self.db.execute(
                            delete(JournalEntryLine).where(JournalEntryLine.journal_entry_id == journal_entry.id)
                        )
                        # Delete journal entry
                        await self.db.delete(journal_entry)
                        logger.info(f"Deleted journal entry {journal_entry.number} for payment {payment.number}")
                
                # For CANCELLED payments, also remove any reversal journal entries
                if payment.status == PaymentStatus.CANCELLED:
                    # Find all reversal entries for this payment by looking for entries that reverse the original entry
                    if payment.journal_entry_id:
                        original_entry_result = await self.db.execute(
                            select(JournalEntry).where(JournalEntry.id == payment.journal_entry_id)
                        )
                        original_entry = original_entry_result.scalar_one_or_none()
                        
                        if original_entry:
                            # Find reversal entries that reference the original entry
                            reversal_entries_result = await self.db.execute(
                                select(JournalEntry).where(
                                    JournalEntry.entry_type == JournalEntryType.REVERSAL,
                                    JournalEntry.reference.like(f"%{original_entry.reference}%")
                                )
                            )
                            reversal_entries = reversal_entries_result.scalars().all()
                            
                            for reversal_entry in reversal_entries:
                                # Delete reversal entry lines first
                                await self.db.execute(
                                    delete(JournalEntryLine).where(JournalEntryLine.journal_entry_id == reversal_entry.id)
                                )
                                # Delete reversal entry
                                await self.db.delete(reversal_entry)
                                logger.info(f"Deleted reversal journal entry {reversal_entry.number} for payment {payment.number}")
            
            elif payment.status == PaymentStatus.CONFIRMED:
                # For CONFIRMED payments, just reset status (no journal entry should exist)
                logger.info(f"Resetting CONFIRMED payment {payment.number} to DRAFT")
            
            # Reset payment status and related fields
            original_status = payment.status  # Store original status for logging
            payment.status = PaymentStatus.DRAFT
            payment.posted_by_id = None
            payment.posted_at = None
            payment.confirmed_by_id = None
            payment.confirmed_at = None
            payment.cancelled_by_id = None
            payment.cancelled_at = None
            payment.journal_entry_id = None
            payment.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Payment {payment.number} reset to draft successfully from {original_status} status")
            return PaymentResponse.from_orm(payment)
            
        except Exception as e:
            logger.error(f"Error resetting payment {payment_id}: {str(e)}")
            await self.db.rollback()
            raise
    
    async def cancel_payment(self, payment_id: uuid.UUID, cancelled_by_id: uuid.UUID, reason: Optional[str] = None) -> PaymentResponse:
        """
        Cancela un pago siguiendo el flujo completo de cancelación:
        
        1. Verificación de estado y permisos
        2. Deshacer conciliaciones previas (N/A - se implementará más tarde)
        3. Anulación del asiento contable del pago
        4. Marcado del pago como 'Cancelled'
        5. Efecto final - pago no aparece como realizado
        
        Args:
            payment_id: ID del pago a cancelar
            cancelled_by_id: ID del usuario que cancela
            reason: Razón de la cancelación (opcional)
            
        Returns:
            PaymentResponse: Pago cancelado
            
        Raises:
            NotFoundError: Si el pago no existe
            BusinessRuleError: Si el pago no puede ser cancelado
        """
        try:
            logger.info(f"Starting payment cancellation process for payment {payment_id}")
            
            # 1. VERIFICACIÓN DE ESTADO Y PERMISOS
            logger.info("Step 1: Verification of status and permissions")
            
            payment_result = await self.db.execute(
                select(Payment).options(
                    selectinload(Payment.payment_invoices).selectinload(PaymentInvoice.invoice),
                    selectinload(Payment.journal_entry),
                    selectinload(Payment.journal)
                ).where(Payment.id == payment_id)
            )
            payment = payment_result.scalar_one_or_none()
            
            if not payment:
                raise NotFoundError(f"Payment with id {payment_id} not found")
            
            # Verificar que el pago esté en estado válido para cancelación
            if payment.status == PaymentStatus.CANCELLED:
                raise BusinessRuleError("Payment is already cancelled")
            
            if payment.status not in [PaymentStatus.DRAFT, PaymentStatus.POSTED]:
                raise BusinessRuleError(f"Payment cannot be cancelled from status {payment.status}")
            
            # TODO: Verificar permisos del usuario en el diario asociado
            # Por ahora, asumimos que todos los usuarios autenticados pueden cancelar
            # En el futuro, verificar: journal.allow_cancellation_by_user(cancelled_by_id)
            
            logger.info(f"✓ Payment {payment.number} is in valid status ({payment.status}) for cancellation")
            
            # 2. DESHACER CONCILIACIONES PREVIAS (pendiente de implementar)
            logger.info("Step 2: Reversing previous reconciliations")
            if payment.status == PaymentStatus.POSTED:
                # Actualmente no hay conciliaciones implementadas
                # Cuando se implemente, aquí se desharán las conciliaciones:
                # await self._reverse_payment_reconciliations(payment)
                logger.info("✓ Reconciliation reversal (not yet implemented - will be added later)")
                
                # Por ahora, revertir asignaciones de pago a facturas
                try:
                    await self._reverse_payment_invoice_reconciliation(payment)
                    logger.info("✓ Payment-invoice allocations reversed")
                except Exception as reconcile_error:
                    logger.error(f"✗ Failed to reverse payment-invoice allocations: {reconcile_error}")
                    raise BusinessRuleError(f"Failed to reverse allocations: {str(reconcile_error)}")
            
            # 3. ANULACIÓN DEL ASIENTO CONTABLE DEL PAGO
            logger.info("Step 3: Cancelling payment journal entry")
            if payment.status == PaymentStatus.POSTED and payment.journal_entry_id:
                try:
                    reversal_entry = await self._create_reversal_journal_entry(payment, cancelled_by_id, reason)
                    logger.info(f"✓ Reversal journal entry created: {reversal_entry.number}")
                except Exception as reversal_error:
                    logger.error(f"✗ Failed to create reversal journal entry: {reversal_error}")
                    raise BusinessRuleError(f"Failed to create reversal entry: {str(reversal_error)}")
            else:
                logger.info("✓ No journal entry to reverse (payment was in DRAFT status)")
            
            # 4. MARCADO DEL PAGO COMO 'CANCELLED'
            logger.info("Step 4: Marking payment as cancelled")
            payment.status = PaymentStatus.CANCELLED
            payment.cancelled_by_id = cancelled_by_id
            payment.cancelled_at = datetime.utcnow()
            
            # Agregar razón de cancelación a las notas
            if reason:
                cancellation_note = f"Cancelled on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} by user {cancelled_by_id}. Reason: {reason}"
                payment.notes = f"{payment.notes or ''}\n{cancellation_note}".strip()
            
            # Persistir cambios
            await self.db.commit()
            logger.info("✓ Payment marked as cancelled and changes committed")
            
            # 5. EFECTO FINAL
            logger.info("Step 5: Final effect verification")
            logger.info(f"✓ Payment {payment.number} is now cancelled and will not appear as 'realized' in reports")
            logger.info(f"✓ Original journal entry remains for audit (marked as reversed)")
            logger.info(f"✓ Invoice outstanding amounts have been restored")
            
            logger.info(f"Payment {payment.number} cancelled successfully following complete cancellation flow")
            return PaymentResponse.from_orm(payment)
            
        except Exception as e:
            logger.error(f"Error cancelling payment {payment_id}: {str(e)}")
            await self.db.rollback()
            raise
    
    async def validate_bulk_confirmation(self, payment_ids: List[uuid.UUID]) -> Dict[str, Any]:
        """
        Valida si múltiples pagos pueden ser confirmados en lote
        
        Returns:
            Dict con resultados de validación por pago
        """
        try:
            logger.info(f"Validating bulk confirmation for {len(payment_ids)} payments")
            
            if not payment_ids:
                raise ValidationError("Payment IDs list cannot be empty")
            
            if len(payment_ids) > 1000:
                raise ValidationError("Too many payments requested. Maximum 1000 payments per bulk operation")
            
            # Obtener todos los pagos
            payments_result = await self.db.execute(
                select(Payment).options(
                    selectinload(Payment.payment_invoices).selectinload(PaymentInvoice.invoice),
                    selectinload(Payment.third_party),
                    selectinload(Payment.account)
                ).where(Payment.id.in_(payment_ids))
            )
            payments = payments_result.scalars().all()
            
            # Crear diccionario para búsqueda rápida
            payment_dict = {p.id: p for p in payments}
            
            results = {
                "total_payments": len(payment_ids),
                "found_payments": len(payments),
                "missing_payments": [pid for pid in payment_ids if pid not in payment_dict],
                "validation_results": {},
                "summary": {
                    "valid": 0,
                    "invalid": 0,
                    "warnings": 0
                }
            }
            
            # Validar cada pago
            for payment_id in payment_ids:
                if payment_id not in payment_dict:
                    results["validation_results"][str(payment_id)] = {
                        "valid": False,
                        "errors": ["Payment not found"],
                        "warnings": []
                    }
                    results["summary"]["invalid"] += 1
                    continue
                
                payment = payment_dict[payment_id]
                
                logger.info(f"🔍 [VALIDATE_BULK] Validating payment {payment.number} - Status: {payment.status}, Amount: {payment.amount}")
                
                # Solo se pueden contabilizar pagos en estado DRAFT
                if payment.status != PaymentStatus.DRAFT:
                    error_msg = f"Payment in {payment.status} status cannot be confirmed/posted - only DRAFT payments allowed"
                    logger.warning(f"❌ [VALIDATE_BULK] Payment {payment.number} - {error_msg}")
                    validation_errors = [error_msg]
                else:
                    # Validar pago DRAFT para confirmación
                    logger.debug(f"🔍 [VALIDATE_BULK] Running DRAFT validation for payment {payment.number}")
                    validation_errors = await self._validate_payment_for_confirmation(payment)
                    
                    if validation_errors:
                        logger.warning(f"❌ [VALIDATE_BULK] Payment {payment.number} validation failed: {validation_errors}")
                    else:
                        logger.info(f"✅ [VALIDATE_BULK] Payment {payment.number} validation passed")
                
                warnings = await self._get_payment_warnings(payment)
                
                is_valid = len(validation_errors) == 0
                has_warnings = len(warnings) > 0
                
                results["validation_results"][str(payment_id)] = {
                    "valid": is_valid,
                    "errors": validation_errors,
                    "warnings": warnings,
                    "payment_number": payment.number,
                    "amount": float(payment.amount),
                    "status": payment.status.value
                }
                
                if is_valid:
                    results["summary"]["valid"] += 1
                    if has_warnings:
                        results["summary"]["warnings"] += 1
                else:
                    results["summary"]["invalid"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating bulk confirmation: {str(e)}")
            raise
    
    async def bulk_confirm_payments(
        self,
        payment_ids: List[uuid.UUID],
        confirmed_by_id: uuid.UUID,
        confirmation_notes: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Confirma/Contabiliza múltiples pagos en lote
        
        FLUJO CORRECTO:
        - Solo procesa pagos en estado DRAFT
        - DRAFT → POSTED (contabilización con journal entry)
        - Temporalmente POSTED hasta implementar conciliación
        
        Args:
            payment_ids: Lista de IDs de pagos a confirmar/contabilizar
            confirmed_by_id: ID del usuario que confirma/contabiliza
            confirmation_notes: Notas adicionales para la operación
            force: Forzar operación ignorando warnings
        """
        try:
            logger.info(f"🚀 [BULK_CONFIRM] Starting bulk confirmation for {len(payment_ids)} payments")
            logger.info(f"👤 [BULK_CONFIRM] Confirmed by user: {confirmed_by_id}")
            logger.info(f"📝 [BULK_CONFIRM] Confirmation notes: {confirmation_notes}")
            logger.info(f"⚠️ [BULK_CONFIRM] Force mode: {force}")
            
            if not payment_ids:
                error_msg = "Payment IDs list cannot be empty"
                logger.error(f"❌ [BULK_CONFIRM] {error_msg}")
                raise ValidationError(error_msg)
            
            if len(payment_ids) > 1000:
                error_msg = "Too many payments requested. Maximum 1000 payments per bulk operation"
                logger.error(f"❌ [BULK_CONFIRM] {error_msg}")
                raise ValidationError(error_msg)
            
            # Validar primero si no es forzado
            if not force:
                logger.info(f"🔍 [BULK_CONFIRM] Starting validation phase for {len(payment_ids)} payments")
                validation_result = await self.validate_bulk_confirmation(payment_ids)
                
                logger.info(f"📊 [BULK_CONFIRM] Validation results: Valid={validation_result['summary']['valid']}, Invalid={validation_result['summary']['invalid']}, Warnings={validation_result['summary']['warnings']}")
                
                if validation_result["summary"]["invalid"] > 0:
                    error_msg = f"Some payments failed validation. {validation_result['summary']['invalid']} invalid payments found. Use force=True to override or fix errors first."
                    logger.error(f"❌ [BULK_CONFIRM] {error_msg}")
                    
                    # Log detalles de errores
                    for payment_id, result in validation_result["validation_results"].items():
                        if not result["valid"]:
                            logger.error(f"❌ [BULK_CONFIRM] Payment {result.get('payment_number', payment_id)} errors: {result['errors']}")
                    
                    raise BusinessRuleError(error_msg)
                
                logger.info(f"✅ [BULK_CONFIRM] All payments passed validation")
            else:
                logger.warning(f"⚠️ [BULK_CONFIRM] FORCE MODE: Skipping validation phase")
            
            results = {
                "total_payments": len(payment_ids),
                "successful": 0,
                "failed": 0,
                "results": {},
                "processing_time": None,
                "operation": "bulk_confirm_draft_to_posted"
            }
            
            start_time = datetime.utcnow()
            logger.info(f"⏰ [BULK_CONFIRM] Processing started at {start_time}")
            
            # Procesar en lotes para mejor rendimiento
            batch_size = 50
            total_batches = (len(payment_ids) + batch_size - 1) // batch_size
            logger.info(f"📦 [BULK_CONFIRM] Processing in {total_batches} batches of {batch_size} payments each")
            
            for i in range(0, len(payment_ids), batch_size):
                batch = payment_ids[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"📦 [BULK_CONFIRM] Processing batch {batch_num}/{total_batches} with {len(batch)} payments")
                
                for payment_id in batch:
                    try:
                        logger.debug(f"🔄 [BULK_CONFIRM] Processing payment {payment_id}")
                        result = await self.confirm_payment(payment_id, confirmed_by_id, force=force)
                        
                        results["results"][str(payment_id)] = {
                            "success": True,
                            "payment_number": result.number,
                            "message": f"Payment {result.number} processed successfully" + (" (FORCED)" if force else ""),
                            "final_status": result.status.value if hasattr(result.status, 'value') else str(result.status)
                        }
                        results["successful"] += 1
                        
                        logger.info(f"✅ [BULK_CONFIRM] Payment {result.number} processed successfully - Status: {result.status}")
                        
                    except Exception as e:
                        logger.error(f"💥 [BULK_CONFIRM] Failed to confirm payment {payment_id}: {str(e)}")
                        logger.error(f"💥 [BULK_CONFIRM] Exception type: {type(e).__name__}")
                        
                        results["results"][str(payment_id)] = {
                            "success": False,
                            "error": str(e),
                            "message": f"Failed to confirm payment: {str(e)}",
                            "exception_type": type(e).__name__
                        }
                        results["failed"] += 1
                
                # Commit intermedio para evitar transacciones muy largas
                logger.debug(f"💾 [BULK_CONFIRM] Committing batch {batch_num}")
                await self.db.commit()
            
            end_time = datetime.utcnow()
            results["processing_time"] = (end_time - start_time).total_seconds()
            
            logger.info(f"🎉 [BULK_CONFIRM] Bulk confirmation completed in {results['processing_time']:.2f} seconds")
            logger.info(f"📊 [BULK_CONFIRM] Final results: {results['successful']}/{results['total_payments']} successful, {results['failed']} failed")
            
            return results
            
        except Exception as e:
            logger.error(f"💥 [BULK_CONFIRM] Critical error in bulk confirm payments: {str(e)}")
            logger.error(f"💥 [BULK_CONFIRM] Exception type: {type(e).__name__}")
            await self.db.rollback()
            raise
    
    async def bulk_cancel_payments(
        self,
        payment_ids: List[uuid.UUID],
        cancelled_by_id: uuid.UUID,
        cancellation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancela múltiples pagos en lote
        """
        try:
            logger.info(f"Starting bulk cancellation for {len(payment_ids)} payments")
            
            if not payment_ids:
                raise ValidationError("Payment IDs list cannot be empty")
            
            if len(payment_ids) > 1000:
                raise ValidationError("Too many payments requested. Maximum 1000 payments per bulk operation")
            
            results = {
                "total_payments": len(payment_ids),
                "successful": 0,
                "failed": 0,
                "results": {},
                "processing_time": None
            }
            
            start_time = datetime.utcnow()
            
            # Procesar en lotes
            batch_size = 50
            for i in range(0, len(payment_ids), batch_size):
                batch = payment_ids[i:i + batch_size]
                
                for payment_id in batch:
                    try:
                        result = await self.cancel_payment(payment_id, cancelled_by_id, cancellation_reason)
                        results["results"][str(payment_id)] = {
                            "success": True,
                            "payment_number": result.number,
                            "message": f"Payment {result.number} cancelled successfully"
                        }
                        results["successful"] += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to cancel payment {payment_id}: {str(e)}")
                        results["results"][str(payment_id)] = {
                            "success": False,
                            "error": str(e),
                            "message": f"Failed to cancel payment: {str(e)}"
                        }
                        results["failed"] += 1
                
                # Commit intermedio
                await self.db.commit()
            
            end_time = datetime.utcnow()
            results["processing_time"] = (end_time - start_time).total_seconds()
            
            logger.info(f"Bulk cancellation completed: {results['successful']}/{results['total_payments']} successful")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk cancel payments: {str(e)}")
            await self.db.rollback()
            raise
    
    async def bulk_reset_to_draft(
        self,
        payment_ids: List[uuid.UUID],
        reset_by_id: uuid.UUID,
        reset_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restablece múltiples pagos POSTED a estado DRAFT en lote
        """
        try:
            logger.info(f"Starting bulk reset to draft for {len(payment_ids)} payments")
            
            if not payment_ids:
                raise ValidationError("Payment IDs list cannot be empty")
            
            if len(payment_ids) > 1000:
                raise ValidationError("Too many payments requested. Maximum 1000 payments per bulk operation")
            
            results = {
                "total_payments": len(payment_ids),
                "successful": 0,
                "failed": 0,
                "results": {},
                "processing_time": None
            }
            
            start_time = datetime.utcnow()
            
            # Procesar en lotes
            batch_size = 50
            for i in range(0, len(payment_ids), batch_size):
                batch = payment_ids[i:i + batch_size]
                
                for payment_id in batch:
                    try:
                        result = await self.reset_payment_to_draft(payment_id, reset_by_id)
                        results["results"][str(payment_id)] = {
                            "success": True,
                            "payment_number": result.number,
                            "message": f"Payment {result.number} reset to draft successfully"
                        }
                        results["successful"] += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to reset payment {payment_id}: {str(e)}")
                        results["results"][str(payment_id)] = {
                            "success": False,
                            "error": str(e),
                            "message": f"Failed to reset payment: {str(e)}"
                        }
                        results["failed"] += 1
                
                # Commit intermedio
                await self.db.commit()
            
            end_time = datetime.utcnow()
            results["processing_time"] = (end_time - start_time).total_seconds()
            
            logger.info(f"Bulk reset to draft completed: {results['successful']}/{results['total_payments']} successful")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk reset to draft: {str(e)}")
            await self.db.rollback()
            raise
    
    async def bulk_delete_payments(
        self,
        payment_ids: List[uuid.UUID],
        deleted_by_id: uuid.UUID,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Elimina múltiples pagos en lote
        Solo permite eliminar pagos en estado DRAFT por defecto
        """
        try:
            logger.info(f"Starting bulk delete for {len(payment_ids)} payments")
            
            if not payment_ids:
                raise ValidationError("Payment IDs list cannot be empty")
            
            if len(payment_ids) > 500:  # Límite más conservador para eliminaciones
                raise ValidationError("Too many payments requested. Maximum 500 payments per bulk delete operation")
            
            results = {
                "total_payments": len(payment_ids),
                "successful": 0,
                "failed": 0,
                "results": {},
                "processing_time": None
            }
            
            start_time = datetime.utcnow()
            
            # Procesar en lotes más pequeños para eliminaciones
            batch_size = 25
            for i in range(0, len(payment_ids), batch_size):
                batch = payment_ids[i:i + batch_size]
                
                for payment_id in batch:
                    try:
                        await self.payment_service.delete_payment(payment_id)
                        results["results"][str(payment_id)] = {
                            "success": True,
                            "message": f"Payment {payment_id} deleted successfully"
                        }
                        results["successful"] += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to delete payment {payment_id}: {str(e)}")
                        results["results"][str(payment_id)] = {
                            "success": False,
                            "error": str(e),
                            "message": f"Failed to delete payment: {str(e)}"
                        }
                        results["failed"] += 1
                
                # Commit intermedio
                await self.db.commit()
            
            end_time = datetime.utcnow()
            results["processing_time"] = (end_time - start_time).total_seconds()
            
            logger.info(f"Bulk delete completed: {results['successful']}/{results['total_payments']} successful")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk delete payments: {str(e)}")
            await self.db.rollback()
            raise
    
    # Métodos auxiliares para operaciones bulk
    
    async def _validate_payment_for_confirmation(self, payment: Payment) -> List[str]:
        """Validación async para confirmación de pagos DRAFT → POSTED"""
        errors = []
        
        logger.info(f"🔍 [VALIDATE_CONFIRM] Validating payment {payment.number} (ID: {payment.id}) for confirmation")
        
        # Validaciones básicas
        logger.debug(f"🔍 [VALIDATE_CONFIRM] Payment {payment.number} - Checking status: {payment.status}")
        if payment.status != PaymentStatus.DRAFT:
            error_msg = f"Payment must be in DRAFT status to be confirmed, current: {payment.status}"
            logger.warning(f"❌ [VALIDATE_CONFIRM] Payment {payment.number} - {error_msg}")
            errors.append(error_msg)
        else:
            logger.debug(f"✅ [VALIDATE_CONFIRM] Payment {payment.number} - Status DRAFT is valid")
        
        logger.debug(f"🔍 [VALIDATE_CONFIRM] Payment {payment.number} - Checking amount: {payment.amount}")
        if not payment.amount or payment.amount <= 0:
            error_msg = f"Payment must have a positive amount, current: {payment.amount}"
            logger.warning(f"❌ [VALIDATE_CONFIRM] Payment {payment.number} - {error_msg}")
            errors.append(error_msg)
        else:
            logger.debug(f"✅ [VALIDATE_CONFIRM] Payment {payment.number} - Amount {payment.amount} is valid")
        
        logger.debug(f"🔍 [VALIDATE_CONFIRM] Payment {payment.number} - Checking third party: {payment.third_party_id}")
        if not payment.third_party_id:
            error_msg = "Payment must have a third party assigned"
            logger.warning(f"❌ [VALIDATE_CONFIRM] Payment {payment.number} - {error_msg}")
            errors.append(error_msg)
        else:
            logger.debug(f"✅ [VALIDATE_CONFIRM] Payment {payment.number} - Third party {payment.third_party_id} is assigned")
        
        logger.debug(f"🔍 [VALIDATE_CONFIRM] Payment {payment.number} - Checking account: {payment.account_id}")
        if not payment.account_id:
            error_msg = "Payment must have a bank/cash account assigned"
            logger.warning(f"❌ [VALIDATE_CONFIRM] Payment {payment.number} - {error_msg}")
            errors.append(error_msg)
        else:
            logger.debug(f"✅ [VALIDATE_CONFIRM] Payment {payment.number} - Account {payment.account_id} is assigned")
        
        logger.debug(f"🔍 [VALIDATE_CONFIRM] Payment {payment.number} - Checking payment date: {payment.payment_date}")
        if not payment.payment_date:
            error_msg = "Payment must have a payment date"
            logger.warning(f"❌ [VALIDATE_CONFIRM] Payment {payment.number} - {error_msg}")
            errors.append(error_msg)
        else:
            logger.debug(f"✅ [VALIDATE_CONFIRM] Payment {payment.number} - Payment date {payment.payment_date} is valid")
        
        # Validar tipo de pago
        logger.debug(f"🔍 [VALIDATE_CONFIRM] Payment {payment.number} - Checking payment type: {payment.payment_type}")
        if not payment.payment_type:
            error_msg = "Payment must have a payment type"
            logger.warning(f"❌ [VALIDATE_CONFIRM] Payment {payment.number} - {error_msg}")
            errors.append(error_msg)
        else:
            logger.debug(f"✅ [VALIDATE_CONFIRM] Payment {payment.number} - Payment type {payment.payment_type} is valid")
        
        # Validar facturas relacionadas
        logger.debug(f"🔍 [VALIDATE_CONFIRM] Payment {payment.number} - Checking {len(payment.payment_invoices)} related invoices")
        if payment.payment_invoices:
            for payment_invoice in payment.payment_invoices:
                invoice = payment_invoice.invoice
                logger.debug(f"🔍 [VALIDATE_CONFIRM] Payment {payment.number} - Invoice {invoice.number} status: {invoice.status}")
                if invoice.status not in [InvoiceStatus.POSTED, InvoiceStatus.PARTIALLY_PAID]:
                    error_msg = f"Invoice {invoice.number} has status {invoice.status} which does not allow payments"
                    logger.warning(f"❌ [VALIDATE_CONFIRM] Payment {payment.number} - {error_msg}")
                    errors.append(error_msg)
                else:
                    logger.debug(f"✅ [VALIDATE_CONFIRM] Payment {payment.number} - Invoice {invoice.number} status {invoice.status} is valid")
        else:
            logger.debug(f"ℹ️ [VALIDATE_CONFIRM] Payment {payment.number} - No invoices linked (allowed)")
        
        # Validar montos si hay facturas
        if payment.payment_invoices:
            total_allocated = sum(pi.amount for pi in payment.payment_invoices)
            logger.debug(f"🔍 [VALIDATE_CONFIRM] Payment {payment.number} - Total allocated: {total_allocated}, Payment amount: {payment.amount}")
            if total_allocated > payment.amount:
                error_msg = f"Allocated amount {total_allocated} exceeds payment amount {payment.amount}"
                logger.warning(f"❌ [VALIDATE_CONFIRM] Payment {payment.number} - {error_msg}")
                errors.append(error_msg)
            else:
                logger.debug(f"✅ [VALIDATE_CONFIRM] Payment {payment.number} - Amount allocation is valid")
        
        if errors:
            logger.error(f"❌ [VALIDATE_CONFIRM] Payment {payment.number} failed validation with {len(errors)} errors: {errors}")
        else:
            logger.info(f"✅ [VALIDATE_CONFIRM] Payment {payment.number} passed all validations successfully")
        
        return errors
    
    async def _get_payment_warnings(self, payment: Payment) -> List[str]:
        """Obtiene warnings no críticos para un pago"""
        warnings = []
        
        # Warning si el pago no tiene facturas asignadas
        if not payment.payment_invoices:
            warnings.append("Payment has no invoice allocations")
        
        # Warning si el monto no está completamente asignado
        total_allocated = sum(pi.amount for pi in payment.payment_invoices)
        if total_allocated < payment.amount:
            unallocated = payment.amount - total_allocated
            warnings.append(f"Payment has unallocated amount: {unallocated}")
        
        # Warning por fecha antigua
        if payment.payment_date and payment.payment_date < (date.today() - timedelta(days=90)):
            warnings.append("Payment date is more than 90 days old")
        
        return warnings
    
    async def _create_reversal_journal_entry(self, payment: Payment, reversed_by_id: uuid.UUID, reason: Optional[str]) -> JournalEntry:
        """
        Crea asiento de reversión para cancelar un pago confirmado
        
        Sigue el flujo de cancelación:
        1. Valida que el usuario existe
        2. Obtiene el asiento original
        3. Crea asiento de reversión con líneas invertidas
        4. Marca el asiento original como cancelado (para auditoría)
        5. Mantiene ambos asientos en la base de datos
        
        Args:
            payment: Pago a cancelar
            reversed_by_id: ID del usuario que realiza la reversión
            reason: Razón de la cancelación
            
        Returns:
            JournalEntry: Asiento de reversión creado
            
        Raises:
            BusinessRuleError: Si el usuario no existe o el pago no tiene asiento
        """
        if not payment.journal_entry_id:
            raise BusinessRuleError("Payment has no journal entry to reverse")
        
        logger.info(f"Creating reversal journal entry for payment {payment.number}")
        
        # 1. Validar que el usuario existe
        from app.models.user import User
        try:
            user_result = await self.db.execute(select(User).where(User.id == reversed_by_id))
            user = user_result.scalar_one_or_none()
            if not user:
                logger.error(f"✗ User validation failed: User {reversed_by_id} not found in database")
                raise BusinessRuleError(f"User with ID {reversed_by_id} not found. Cannot create journal entry.")
            logger.debug(f"✓ User validation passed: User {user.email} ({reversed_by_id}) found")
        except Exception as e:
            logger.error(f"✗ Failed to validate user {reversed_by_id}: {str(e)}")
            raise BusinessRuleError(f"Failed to validate user for journal entry creation: {str(e)}")
        
        # 2. Obtener el asiento original
        original_entry_result = await self.db.execute(
            select(JournalEntry).options(selectinload(JournalEntry.lines))
            .where(JournalEntry.id == payment.journal_entry_id)
        )
        original_entry = original_entry_result.scalar_one_or_none()
        
        if not original_entry:
            raise BusinessRuleError("Original journal entry not found")
        
        logger.info(f"Original journal entry found: {original_entry.number}")
        
        # Generar número para el asiento de reversión
        reversal_number = f"REV-{original_entry.number}"
        
        # Crear asiento de reversión
        reversal_entry = JournalEntry(
            number=reversal_number,
            reference=f"Reversal of {original_entry.reference}",
            journal_id=original_entry.journal_id,
            entry_date=datetime.utcnow(),
            status=JournalEntryStatus.POSTED,
            entry_type=JournalEntryType.REVERSAL,
            transaction_origin=TransactionOrigin.PAYMENT,
            description=f"Reversal: {reason or 'Payment cancelled'}",
            created_by_id=reversed_by_id
        )
        
        self.db.add(reversal_entry)
        await self.db.flush()
        
        logger.info(f"Reversal journal entry created: {reversal_number}")
        
        # Crear líneas de reversión (invertir débitos y créditos)
        total_debit = Decimal('0')
        total_credit = Decimal('0')
        
        for line_index, original_line in enumerate(original_entry.lines, 1):
            reversal_line = JournalEntryLine(
                journal_entry_id=reversal_entry.id,
                account_id=original_line.account_id,
                debit_amount=original_line.credit_amount,  # Invertir
                credit_amount=original_line.debit_amount,  # Invertir
                description=f"Reversal: {original_line.description}",
                line_number=line_index
            )
            self.db.add(reversal_line)
            
            # Acumular totales
            total_debit += reversal_line.debit_amount
            total_credit += reversal_line.credit_amount
        
        # Actualizar totales del asiento de reversión
        reversal_entry.total_debit = total_debit
        reversal_entry.total_credit = total_credit
        
        logger.info(f"Created {len(original_entry.lines)} reversal lines with totals: D:{total_debit}, C:{total_credit}")
        
        # Actualizar saldos de cuentas afectadas por la reversión
        await self.db.flush()  # Asegurar que las líneas están persistidas
        
        # Cargar cuentas y actualizar saldos
        for line_index, original_line in enumerate(original_entry.lines, 1):
            account_result = await self.db.execute(
                select(Account).where(Account.id == original_line.account_id)
            )
            account = account_result.scalar_one_or_none()
            
            if account:
                # Aplicar el impacto de la reversión en los saldos
                debit_amount = original_line.credit_amount  # Invertido
                credit_amount = original_line.debit_amount  # Invertido
                
                # Actualizar saldos de la cuenta
                account.update_balance(debit_amount, credit_amount)
                
                logger.debug(f"Account {account.code} balance updated by reversal: D:{debit_amount}, C:{credit_amount}")
        
        logger.info("Account balances updated for all reversal lines")
        
        # Marcar el asiento original como cancelado (para auditoría)
        # El asiento original permanece en la base de datos pero se marca como cancelado
        original_entry.status = JournalEntryStatus.CANCELLED
        original_entry.description = f"{original_entry.description} [CANCELLED - Reversed by {reversal_number}]"
        
        logger.info(f"Original journal entry {original_entry.number} marked as cancelled")
        
        await self.db.flush()
        
        logger.info(f"Reversal journal entry process completed for payment {payment.number}")
        return reversal_entry
    
    async def _reverse_payment_invoice_reconciliation(self, payment: Payment) -> None:
        """Reversa la reconciliación de facturas al cancelar un pago"""
        for payment_invoice in payment.payment_invoices:
            invoice = payment_invoice.invoice
            
            # Restaurar monto pendiente en la factura
            invoice.outstanding_amount += payment_invoice.amount
            
            # Actualizar estado de la factura si es necesario
            if invoice.outstanding_amount >= invoice.total_amount:
                invoice.status = InvoiceStatus.POSTED
            elif invoice.outstanding_amount > Decimal('0'):
                invoice.status = InvoiceStatus.PARTIALLY_PAID

    async def bulk_post_payments(
        self,
        payment_ids: List[uuid.UUID],
        posted_by_id: uuid.UUID,
        posting_notes: Optional[str] = None,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Contabiliza múltiples pagos en lote de forma optimizada
        
        Args:
            payment_ids: Lista de IDs de pagos a contabilizar (máximo 1000)
            posted_by_id: ID del usuario que contabiliza
            posting_notes: Notas de contabilización
            batch_size: Tamaño del lote para procesamiento (default: 50)
            
        Returns:
            Dict con resultados detallados de la operación bulk
        """
        from datetime import datetime, timedelta
        
        start_time = datetime.utcnow()
        total_payments = len(payment_ids)
        
        # Validar límite máximo
        if total_payments > 1000:
            raise ValidationError("Maximum 1000 payments allowed for bulk posting")
        
        results = {
            "total_payments": total_payments,
            "successful": 0,
            "failed": 0,
            "results": {},
            "processing_time": 0,
            "operation": "bulk_post",
            "batch_size": batch_size,
            "posting_notes": posting_notes
        }
        
        logger.info(f"Starting bulk posting of {total_payments} payments by user {posted_by_id}")
        
        try:
            # Procesar en lotes para optimizar rendimiento
            for i in range(0, total_payments, batch_size):
                batch_ids = payment_ids[i:i + batch_size]
                batch_number = (i // batch_size) + 1
                total_batches = (total_payments + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_number}/{total_batches} with {len(batch_ids)} payments")
                
                # Obtener pagos del lote con relaciones necesarias
                stmt = select(Payment).options(
                    selectinload(Payment.payment_invoices).selectinload(PaymentInvoice.invoice),
                    selectinload(Payment.third_party),
                    selectinload(Payment.account),
                    selectinload(Payment.bank_extract_lines)
                ).where(Payment.id.in_(batch_ids))
                
                result = await self.db.execute(stmt)
                payments = result.scalars().all()
                
                # Crear diccionario para búsqueda rápida
                payments_dict = {payment.id: payment for payment in payments}
                
                # Procesar cada pago del lote
                for payment_id in batch_ids:
                    payment = payments_dict.get(payment_id)
                    
                    if not payment:
                        results["results"][str(payment_id)] = {
                            "success": False,
                            "message": "Payment not found",
                            "error": "Payment does not exist in database"
                        }
                        results["failed"] += 1
                        continue
                    
                    try:
                        # Validar que el pago puede ser contabilizado
                        validation_errors = await self._validate_payment_for_posting(payment)
                        if validation_errors:
                            results["results"][str(payment_id)] = {
                                "success": False,
                                "message": "Validation failed",
                                "error": "; ".join(validation_errors),
                                "payment_number": payment.number
                            }
                            results["failed"] += 1
                            continue
                        
                        # Contabilizar el pago
                        await self._post_single_payment(payment, posted_by_id, posting_notes)
                        
                        results["results"][str(payment_id)] = {
                            "success": True,
                            "message": f"Payment {payment.number} posted successfully",
                            "payment_number": payment.number
                        }
                        results["successful"] += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to post payment {payment_id}: {str(e)}")
                        results["results"][str(payment_id)] = {
                            "success": False,
                            "error": str(e),
                            "message": f"Failed to post payment: {str(e)}",
                            "payment_number": getattr(payment, 'number', 'Unknown')
                        }
                        results["failed"] += 1
                
                # Commit intermedio para cada lote
                await self.db.commit()
            
            end_time = datetime.utcnow()
            results["processing_time"] = (end_time - start_time).total_seconds()
            
            logger.info(f"Bulk posting completed: {results['successful']}/{results['total_payments']} successful")
            return results
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in bulk posting operation: {str(e)}")
            raise BusinessRuleError(f"Bulk posting failed: {str(e)}")

    async def _validate_payment_for_posting(self, payment: Payment) -> List[str]:
        """Valida que un pago puede ser contabilizado"""
        errors = []
        
        # Verificar estado del pago
        if payment.status != PaymentStatus.CONFIRMED:
            errors.append(f"Payment must be CONFIRMED to be posted (current: {payment.status})")
        
        # Verificar que no esté ya contabilizado
        if payment.status == PaymentStatus.POSTED:
            errors.append("Payment is already posted")
        
        # Verificar monto válido
        if payment.amount <= 0:
            errors.append("Payment amount must be greater than zero")
        
        # Verificar cuenta contable
        if not payment.account_id:
            errors.append("Payment must have an account assigned")
        
        # Verificar tercero
        if not payment.third_party_id:
            errors.append("Payment must have a third party assigned")
        
        # Verificar fecha no muy antigua (advertencia convertida en error)
        if payment.payment_date < (datetime.now().date() - timedelta(days=365)):
            errors.append("Payment date is more than 1 year old")
        
        return errors

    async def _post_single_payment(
        self,
        payment: Payment,
        posted_by_id: uuid.UUID,
        posting_notes: Optional[str] = None
    ) -> None:
        """Contabiliza un solo pago"""
        try:
            # Marcar como contabilizado
            payment.status = PaymentStatus.POSTED
            payment.posted_at = datetime.utcnow()
            payment.posted_by_id = posted_by_id
            if posting_notes:
                payment.notes = f"{payment.notes or ''}\n[POSTING] {posting_notes}".strip()
            
            # Crear asiento contable si no existe
            if not payment.journal_entry_id:
                journal_entry = await self._create_payment_journal_entry(payment, posted_by_id)
                payment.journal_entry_id = journal_entry.id
            
            await self.db.flush()
            logger.info(f"Payment {payment.number} posted successfully")
            
        except Exception as e:
            logger.error(f"Failed to post payment {payment.id}: {str(e)}")
            raise

    async def _create_payment_journal_entry(
        self,
        payment: Payment,
        created_by_id: uuid.UUID
    ) -> "JournalEntry":
        """
        Crear asiento contable para el pago siguiendo el patrón contable estándar
        
        Lógica contable:
        - Pago de cliente (CUSTOMER_PAYMENT): 
          * DEBE: Cuenta bancaria/caja
          * HABER: Cuenta por cobrar cliente
        - Pago a proveedor (SUPPLIER_PAYMENT):
          * DEBE: Cuenta por pagar proveedor  
          * HABER: Cuenta bancaria/caja
        """
        from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType, TransactionOrigin
        from app.models.journal import Journal
        from datetime import timezone
        
        try:
            logger.info(f"Creating journal entry for payment {payment.number} (type: {payment.payment_type}, amount: {payment.amount})")
            
            # Obtener el journal
            logger.debug(f"Loading journal {payment.journal_id} for payment {payment.number}")
            stmt = select(Journal).where(Journal.id == payment.journal_id)
            result = await self.db.execute(stmt)
            journal = result.scalar_one_or_none()
            
            if not journal:
                error_msg = f"Journal not found for payment"
                logger.error(f"Payment {payment.number} - {error_msg} (journal_id: {payment.journal_id})")
                raise BusinessRuleError(error_msg)
            
            logger.info(f"Payment {payment.number} - Using journal: {journal.name} (code: {journal.code})")
            
            # Generar número del asiento
            logger.debug(f"Generating journal entry number for payment {payment.number}")
            entry_number = await self._generate_journal_entry_number(journal)
            logger.info(f"Payment {payment.number} - Generated journal entry number: {entry_number}")
            
            # Determinar origen de transacción
            if payment.payment_type == PaymentType.CUSTOMER_PAYMENT:
                transaction_origin = TransactionOrigin.COLLECTION
            elif payment.payment_type == PaymentType.SUPPLIER_PAYMENT:
                transaction_origin = TransactionOrigin.PAYMENT
            else:
                transaction_origin = TransactionOrigin.PAYMENT
            
            logger.debug(f"Payment {payment.number} - Transaction origin: {transaction_origin}")
            
            # Crear asiento principal
            logger.debug(f"Creating main journal entry for payment {payment.number}")
            journal_entry = JournalEntry(
                number=entry_number,
                entry_type=JournalEntryType.AUTOMATIC,
                status=JournalEntryStatus.POSTED,
                entry_date=datetime.combine(payment.payment_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                description=f"Payment {payment.number} - {payment.third_party.name if payment.third_party else 'Unknown'}",
                reference=payment.reference or payment.number,
                transaction_origin=transaction_origin,
                journal_id=payment.journal_id,
                created_by_id=created_by_id
            )
            
            self.db.add(journal_entry)
            await self.db.flush()
            
            logger.info(f"Payment {payment.number} - Journal entry {entry_number} created, now creating lines")
            
            # Crear líneas del asiento
            await self._create_journal_entry_lines_for_payment(journal_entry, payment)
            
            # Calcular totales del journal entry manualmente (async)
            await self._calculate_journal_entry_totals(journal_entry)
            
            logger.info(f"Payment {payment.number} - Journal entry {entry_number} completed with totals calculated")
            return journal_entry
            
        except Exception as e:
            logger.error(f"Error creating journal entry for payment {payment.number}: {str(e)}")
            raise

    async def _generate_journal_entry_number(self, journal: "Journal") -> str:
        """Generar número secuencial para el asiento contable"""
        # Obtener el último número del journal
        from app.models.journal_entry import JournalEntry
        
        stmt = select(func.max(JournalEntry.number)).where(
            JournalEntry.journal_id == journal.id,
            JournalEntry.number.like(f"{journal.code}%")
        )
        result = await self.db.execute(stmt)
        last_number = result.scalar()
        
        if last_number:
            # Extraer el número secuencial
            try:
                sequence_part = last_number.replace(journal.code, "").lstrip("0")
                next_sequence = int(sequence_part) + 1 if sequence_part else 1
            except ValueError:
                next_sequence = 1
        else:
            next_sequence = 1
        
        return f"{journal.code}{next_sequence:06d}"

    async def _create_journal_entry_lines_for_payment(
        self,
        journal_entry: "JournalEntry",
        payment: Payment
    ) -> None:
        """Crear las líneas del asiento contable para el pago"""
        from app.models.journal_entry import JournalEntryLine
        
        logger.info(f"📝 [JOURNAL_LINES] Creating journal entry lines for payment {payment.number} (type: {payment.payment_type})")
        
        line_counter = 1
        
        if payment.payment_type == PaymentType.CUSTOMER_PAYMENT:
            # Pago de cliente: entrada de dinero
            logger.info(f"💰 [JOURNAL_LINES] Creating CUSTOMER_PAYMENT lines for {payment.number}")
            
            # 1. DEBE: Cuenta bancaria/caja (entrada de dinero)
            logger.debug(f"📝 [JOURNAL_LINES] Line 1 - DEBIT: Bank account {payment.account.code} - {payment.account.name}")
            bank_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                line_number=line_counter,
                account_id=payment.account_id,
                third_party_id=payment.third_party_id,
                debit_amount=payment.amount,
                credit_amount=Decimal('0'),
                description=f"Payment received from {payment.third_party.name if payment.third_party else 'customer'}",
                reference=payment.reference or payment.number
            )
            self.db.add(bank_line)
            line_counter += 1
            
            # 2. HABER: Cuenta por cobrar
            receivable_account = await self._get_customer_receivable_account(payment)
            logger.debug(f"📝 [JOURNAL_LINES] Line 2 - CREDIT: Receivable account {receivable_account.code} - {receivable_account.name}")
            credit_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                line_number=line_counter,
                account_id=receivable_account.id,
                third_party_id=payment.third_party_id,
                debit_amount=Decimal('0'),
                credit_amount=payment.amount,
                description=f"Payment application to customer receivables",
                reference=payment.reference or payment.number
            )
            self.db.add(credit_line)
            
        elif payment.payment_type == PaymentType.SUPPLIER_PAYMENT:
            # Pago a proveedor: salida de dinero
            logger.info(f"💸 [JOURNAL_LINES] Creating SUPPLIER_PAYMENT lines for {payment.number}")
            
            # 1. DEBE: Cuenta por pagar
            payable_account = await self._get_supplier_payable_account(payment)
            logger.debug(f"📝 [JOURNAL_LINES] Line 1 - DEBIT: Payable account {payable_account.code} - {payable_account.name}")
            debit_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                line_number=line_counter,
                account_id=payable_account.id,
                third_party_id=payment.third_party_id,
                debit_amount=payment.amount,
                credit_amount=Decimal('0'),
                description=f"Payment to supplier payables",
                reference=payment.reference or payment.number
            )
            self.db.add(debit_line)
            line_counter += 1
            
            # 2. HABER: Cuenta bancaria/caja (salida de dinero)
            logger.debug(f"📝 [JOURNAL_LINES] Line 2 - CREDIT: Bank account {payment.account.code} - {payment.account.name}")
            bank_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                line_number=line_counter,
                account_id=payment.account_id,
                third_party_id=payment.third_party_id,
                debit_amount=Decimal('0'),
                credit_amount=payment.amount,
                description=f"Payment made to {payment.third_party.name if payment.third_party else 'supplier'}",
                reference=payment.reference or payment.number
            )
            self.db.add(bank_line)
        #todo:add falta comprobar
            
        elif payment.payment_type == PaymentType.INTERNAL_TRANSFER:
            # Transferencia interna: entre cuentas bancarias
            logger.info(f"🔄 [JOURNAL_LINES] Creating INTERNAL_TRANSFER lines for {payment.number}")
            
            # Para transferencias internas usar cuenta de transferencias pendientes de la configuración
            from app.models.company_settings import CompanySettings
            from app.models.account import Account, AccountType
            
            stmt = select(CompanySettings).where(CompanySettings.is_active == True)
            result = await self.db.execute(stmt)
            company_settings = result.scalar_one_or_none()
            
            transfer_account = None
            if company_settings and company_settings.internal_transfer_account_id:
                stmt = select(Account).where(Account.id == company_settings.internal_transfer_account_id)
                result = await self.db.execute(stmt)
                transfer_account = result.scalar_one_or_none()
            
            if not transfer_account:
                # Fallback: usar una cuenta de transferencias pendientes por tipo
                from app.models.account import AccountType
                stmt = select(Account).where(
                    Account.account_type == AccountType.ASSET,
                    Account.name.ilike('%transfer%'),
                    Account.is_active == True
                ).order_by(Account.code).limit(1)
                result = await self.db.execute(stmt)
                transfer_account = result.scalar_one_or_none()
            
            if not transfer_account:
                raise BusinessRuleError("No transfer destination account configured for internal transfer")
            
            # 1. DEBE: Cuenta destino/transferencias pendientes
            debit_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                line_number=line_counter,
                account_id=transfer_account.id,
                debit_amount=payment.amount,
                credit_amount=Decimal('0'),
                description=f"Internal transfer - destination",
                reference=payment.reference or payment.number
            )
            self.db.add(debit_line)
            line_counter += 1
            
            # 2. HABER: Cuenta origen (banco/caja del pago)
            credit_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                line_number=line_counter,
                account_id=payment.account_id,
                debit_amount=Decimal('0'),
                credit_amount=payment.amount,
                description=f"Internal transfer - origin",
                reference=payment.reference or payment.number
            )
            self.db.add(credit_line)
            
        else:
            # Otros tipos de pago (ADVANCE_PAYMENT, REFUND)
            logger.warning(f"⚠️ [JOURNAL_LINES] Payment type {payment.payment_type} needs specific accounting logic")
            
            # Por ahora, usar lógica simple: débito cuenta genérica, crédito banco
            # DEBE: Cuenta de gastos varios o anticipos
            from app.models.account import Account, AccountType
            stmt = select(Account).where(
                Account.account_type == AccountType.EXPENSE,
                Account.is_active == True
            ).order_by(Account.code).limit(1)
            result = await self.db.execute(stmt)
            expense_account = result.scalar_one_or_none()
            
            if not expense_account:
                raise BusinessRuleError(f"No expense account found for payment type {payment.payment_type}")
            
            # 1. DEBE: Cuenta de gastos/anticipos
            debit_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                line_number=line_counter,
                account_id=expense_account.id,
                third_party_id=payment.third_party_id,
                debit_amount=payment.amount,
                credit_amount=Decimal('0'),
                description=f"Payment - {payment.payment_type.value}",
                reference=payment.reference or payment.number
            )
            self.db.add(debit_line)
            line_counter += 1
            
            # 2. HABER: Cuenta bancaria/caja
            credit_line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                line_number=line_counter,
                account_id=payment.account_id,
                third_party_id=payment.third_party_id,
                debit_amount=Decimal('0'),
                credit_amount=payment.amount,
                description=f"Payment - {payment.payment_type.value}",
                reference=payment.reference or payment.number
            )
            self.db.add(credit_line)
        logger.info(f"✅ [JOURNAL_LINES] Created {line_counter} journal entry lines for payment {payment.number}")
        #hasta aqui

    async def _get_customer_receivable_account(self, payment: Payment) -> "Account":
        """
        Obtener cuenta por cobrar del cliente usando jerarquía de búsqueda:
        1. Cuenta específica del tercero (cliente)
        2. Cuenta específica del diario
        3. Cuenta por defecto de la empresa
        4. Búsqueda por tipo/categoría (fallback)
        """
        from app.models.account import Account, AccountType, AccountCategory
        from app.models.journal import Journal
        from app.models.company_settings import CompanySettings
        
        logger.debug(f"🔍 [RECEIVABLE_ACCOUNT] Getting receivable account for payment {payment.number}")
        
        # 1. Buscar cuenta específica del tercero
        if payment.third_party and payment.third_party.receivable_account_id:
            logger.debug(f"🔍 [RECEIVABLE_ACCOUNT] Third party has specific receivable account: {payment.third_party.receivable_account_id}")
            stmt = select(Account).where(Account.id == payment.third_party.receivable_account_id)
            result = await self.db.execute(stmt)
            account = result.scalar_one_or_none()
            if account and account.is_active:
                logger.info(f"✅ [RECEIVABLE_ACCOUNT] Using third party specific account: {account.code} - {account.name}")
                return account
        
        # 2. Buscar cuenta específica del diario
        if payment.journal_id:
            logger.debug(f"🔍 [RECEIVABLE_ACCOUNT] Checking journal specific receivable account")
            stmt = select(Journal).where(Journal.id == payment.journal_id)
            result = await self.db.execute(stmt)
            journal = result.scalar_one_or_none()
            
            if journal and journal.customer_receivable_account_id:
                logger.debug(f"🔍 [RECEIVABLE_ACCOUNT] Journal has specific receivable account: {journal.customer_receivable_account_id}")
                stmt = select(Account).where(Account.id == journal.customer_receivable_account_id)
                result = await self.db.execute(stmt)
                account = result.scalar_one_or_none()
                if account and account.is_active:
                    logger.info(f"✅ [RECEIVABLE_ACCOUNT] Using journal specific account: {account.code} - {account.name}")
                    return account
        
        # 3. Buscar cuenta por defecto de la empresa
        logger.debug(f"🔍 [RECEIVABLE_ACCOUNT] Checking company default receivable account")
        stmt = select(CompanySettings).where(CompanySettings.is_active == True)
        result = await self.db.execute(stmt)
        company_settings = result.scalar_one_or_none()
        
        if company_settings and company_settings.default_customer_receivable_account_id:
            logger.debug(f"🔍 [RECEIVABLE_ACCOUNT] Company has default receivable account: {company_settings.default_customer_receivable_account_id}")
            stmt = select(Account).where(Account.id == company_settings.default_customer_receivable_account_id)
            result = await self.db.execute(stmt)
            account = result.scalar_one_or_none()
            if account and account.is_active:
                logger.info(f"✅ [RECEIVABLE_ACCOUNT] Using company default account: {account.code} - {account.name}")
                return account
        
        # 4. Fallback: Cuenta por defecto de activo corriente (cuentas por cobrar) - usar la primera
        logger.debug(f"🔍 [RECEIVABLE_ACCOUNT] Using fallback search by type/category")
        stmt = select(Account).where(
            Account.account_type == AccountType.ASSET,
            Account.category == AccountCategory.CURRENT_ASSET,
            Account.is_active == True
        ).order_by(Account.code).limit(1)
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            error_msg = "No receivable account found"
            logger.error(f"❌ [RECEIVABLE_ACCOUNT] {error_msg}")
            raise BusinessRuleError(error_msg)
        
        logger.info(f"✅ [RECEIVABLE_ACCOUNT] Using fallback account: {account.code} - {account.name}")
        return account

    async def _get_supplier_payable_account(self, payment: Payment) -> "Account":
        """
        Obtener cuenta por pagar del proveedor usando jerarquía de búsqueda:
        1. Cuenta específica del tercero (proveedor)
        2. Cuenta específica del diario
        3. Cuenta por defecto de la empresa
        4. Búsqueda por tipo/categoría (fallback)
        """
        from app.models.account import Account, AccountType, AccountCategory
        from app.models.journal import Journal
        from app.models.company_settings import CompanySettings
        
        logger.debug(f"🔍 [PAYABLE_ACCOUNT] Getting payable account for payment {payment.number}")
        
        # 1. Buscar cuenta específica del tercero
        if payment.third_party and payment.third_party.payable_account_id:
            logger.debug(f"🔍 [PAYABLE_ACCOUNT] Third party has specific payable account: {payment.third_party.payable_account_id}")
            stmt = select(Account).where(Account.id == payment.third_party.payable_account_id)
            result = await self.db.execute(stmt)
            account = result.scalar_one_or_none()
            if account and account.is_active:
                logger.info(f"✅ [PAYABLE_ACCOUNT] Using third party specific account: {account.code} - {account.name}")
                return account
        
        # 2. Buscar cuenta específica del diario
        if payment.journal_id:
            logger.debug(f"🔍 [PAYABLE_ACCOUNT] Checking journal specific payable account")
            stmt = select(Journal).where(Journal.id == payment.journal_id)
            result = await self.db.execute(stmt)
            journal = result.scalar_one_or_none()
            
            if journal and journal.supplier_payable_account_id:
                logger.debug(f"🔍 [PAYABLE_ACCOUNT] Journal has specific payable account: {journal.supplier_payable_account_id}")
                stmt = select(Account).where(Account.id == journal.supplier_payable_account_id)
                result = await self.db.execute(stmt)
                account = result.scalar_one_or_none()
                if account and account.is_active:
                    logger.info(f"✅ [PAYABLE_ACCOUNT] Using journal specific account: {account.code} - {account.name}")
                    return account
        
        # 3. Buscar cuenta por defecto de la empresa
        logger.debug(f"🔍 [PAYABLE_ACCOUNT] Checking company default payable account")
        stmt = select(CompanySettings).where(CompanySettings.is_active == True)
        result = await self.db.execute(stmt)
        company_settings = result.scalar_one_or_none()
        
        if company_settings and company_settings.default_supplier_payable_account_id:
            logger.debug(f"🔍 [PAYABLE_ACCOUNT] Company has default payable account: {company_settings.default_supplier_payable_account_id}")
            stmt = select(Account).where(Account.id == company_settings.default_supplier_payable_account_id)
            result = await self.db.execute(stmt)
            account = result.scalar_one_or_none()
            if account and account.is_active:
                logger.info(f"✅ [PAYABLE_ACCOUNT] Using company default account: {account.code} - {account.name}")
                return account
        
        # 4. Fallback: Cuenta por defecto de pasivo corriente (cuentas por pagar) - usar la primera
        logger.debug(f"🔍 [PAYABLE_ACCOUNT] Using fallback search by type/category")
        stmt = select(Account).where(
            Account.account_type == AccountType.LIABILITY,
            Account.category == AccountCategory.CURRENT_LIABILITY,
            Account.is_active == True
        ).order_by(Account.code).limit(1)
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            error_msg = "No payable account found"
            logger.error(f"❌ [PAYABLE_ACCOUNT] {error_msg}")
            raise BusinessRuleError(error_msg)
        
        logger.info(f"✅ [PAYABLE_ACCOUNT] Using fallback account: {account.code} - {account.name}")
        return account

    async def _get_default_payment_journal(self, payment_type: PaymentType) -> uuid.UUID:
        """
        Determina el journal apropiado para el pago basado en:
        1. Journal de banco/caja por defecto
        2. Tipo de pago
        """
        # Buscar journal de banco por defecto
        stmt = select(Journal).where(
            and_(
                Journal.type.in_([JournalType.BANK, JournalType.CASH]),
                Journal.is_active == True
            )
        ).order_by(Journal.created_at)
        
        result = await self.db.execute(stmt)
        journal = result.scalar_one_or_none()
        
        if not journal:
            raise BusinessRuleError("No default payment journal found")
        
        return journal.id

    async def _reconcile_payment_invoices(self, payment: Payment) -> None:
        """Reconcilia las facturas asignadas al pago"""
        if not payment.payment_invoices:
            return
        
        for payment_invoice in payment.payment_invoices:
            invoice = payment_invoice.invoice
            
            # Actualizar monto pendiente de la factura
            invoice.outstanding_amount -= payment_invoice.amount
            
            # Actualizar estado de la factura
            if invoice.outstanding_amount <= 0:
                invoice.status = InvoiceStatus.PAID
            elif invoice.outstanding_amount < invoice.total_amount:
                invoice.status = InvoiceStatus.PARTIALLY_PAID
            
            # Validar que no quede monto negativo
            if invoice.outstanding_amount < 0:
                invoice.outstanding_amount = Decimal('0')

        await self.db.flush()
    async def _calculate_journal_entry_totals(self, journal_entry: "JournalEntry") -> None:
        """Calcula los totales de débito y crédito del asiento contable de forma asíncrona"""
        from app.models.journal_entry import JournalEntryLine
        from sqlalchemy import func
        
        # Calcular totales usando consulta asíncrona
        stmt = select(
            func.sum(JournalEntryLine.debit_amount).label('total_debit'),
            func.sum(JournalEntryLine.credit_amount).label('total_credit')
        ).where(JournalEntryLine.journal_entry_id == journal_entry.id)
        
        result = await self.db.execute(stmt)
        totals = result.first()
        
        if totals:
            journal_entry.total_debit = totals.total_debit or Decimal('0')
            journal_entry.total_credit = totals.total_credit or Decimal('0')
            logger.debug(f"📊 [JOURNAL_TOTALS] Journal entry {journal_entry.number} - Debit: {journal_entry.total_debit}, Credit: {journal_entry.total_credit}")
        else:
            journal_entry.total_debit = Decimal('0')
            journal_entry.total_credit = Decimal('0')
            logger.warning(f"⚠️ [JOURNAL_TOTALS] No lines found for journal entry {journal_entry.number}")
        
        # Guardar los totales calculados
        await self.db.flush()