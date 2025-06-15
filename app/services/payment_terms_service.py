import uuid
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import selectinload

from app.models.payment_terms import PaymentTerms, PaymentSchedule
from app.schemas.payment_terms import (
    PaymentTermsCreate, PaymentTermsUpdate, PaymentTermsFilter,
    PaymentCalculationRequest, PaymentCalculationResponse, PaymentCalculation
)
from app.utils.exceptions import NotFoundError, ValidationError


class PaymentTermsService:
    """Servicio para gestión de condiciones de pago"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment_terms(self, payment_terms_data: PaymentTermsCreate) -> PaymentTerms:
        """
        Crea nuevas condiciones de pago con su cronograma
        
        Args:
            payment_terms_data: Datos de las condiciones de pago
            
        Returns:
            PaymentTerms: Condiciones de pago creadas
            
        Raises:
            ValidationError: Si el código ya existe
        """
        # Verificar que el código no exista
        existing = await self.db.execute(
            select(PaymentTerms).where(PaymentTerms.code == payment_terms_data.code)
        )
        if existing.scalar_one_or_none():
            raise ValidationError(f"Ya existe una condición de pago con código: {payment_terms_data.code}")

        # Crear condiciones de pago
        payment_terms = PaymentTerms(
            code=payment_terms_data.code,
            name=payment_terms_data.name,
            description=payment_terms_data.description,
            is_active=payment_terms_data.is_active,
            notes=payment_terms_data.notes
        )

        self.db.add(payment_terms)
        await self.db.flush()  # Para obtener el ID

        # Crear cronograma de pagos
        for schedule_data in payment_terms_data.payment_schedules:
            schedule = PaymentSchedule(
                payment_terms_id=payment_terms.id,
                sequence=schedule_data.sequence,
                days=schedule_data.days,
                percentage=schedule_data.percentage,
                description=schedule_data.description
            )
            self.db.add(schedule)

        await self.db.commit()
        await self.db.refresh(payment_terms)
        
        # Cargar cronograma
        result = await self.db.execute(
            select(PaymentTerms)
            .options(selectinload(PaymentTerms.payment_schedules))
            .where(PaymentTerms.id == payment_terms.id)
        )
        return result.scalar_one()

    async def get_payment_terms_by_id(self, payment_terms_id: uuid.UUID) -> PaymentTerms:
        """
        Obtiene condiciones de pago por ID
        
        Args:
            payment_terms_id: ID de las condiciones de pago
            
        Returns:
            PaymentTerms: Condiciones de pago encontradas
            
        Raises:
            NotFoundError: Si no se encuentra
        """
        result = await self.db.execute(
            select(PaymentTerms)
            .options(selectinload(PaymentTerms.payment_schedules))
            .where(PaymentTerms.id == payment_terms_id)
        )
        
        payment_terms = result.scalar_one_or_none()
        if not payment_terms:
            raise NotFoundError(f"Condiciones de pago no encontradas: {payment_terms_id}")
        
        return payment_terms

    async def get_payment_terms_by_code(self, code: str) -> PaymentTerms:
        """
        Obtiene condiciones de pago por código
        
        Args:
            code: Código de las condiciones de pago
            
        Returns:
            PaymentTerms: Condiciones de pago encontradas
            
        Raises:
            NotFoundError: Si no se encuentra
        """
        result = await self.db.execute(
            select(PaymentTerms)
            .options(selectinload(PaymentTerms.payment_schedules))
            .where(PaymentTerms.code == code)
        )
        
        payment_terms = result.scalar_one_or_none()
        if not payment_terms:
            raise NotFoundError(f"Condiciones de pago no encontradas con código: {code}")
        
        return payment_terms

    async def list_payment_terms(
        self,
        filters: Optional[PaymentTermsFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[PaymentTerms], int]:
        """
        Lista condiciones de pago con filtros
        
        Args:
            filters: Filtros de búsqueda
            skip: Número de registros a omitir
            limit: Número máximo de registros
            
        Returns:
            tuple: (lista de condiciones de pago, total de registros)
        """
        query = select(PaymentTerms).options(selectinload(PaymentTerms.payment_schedules))
        count_query = select(func.count(PaymentTerms.id))

        # Aplicar filtros
        if filters:
            conditions = []
            
            if filters.is_active is not None:
                conditions.append(PaymentTerms.is_active == filters.is_active)
            
            if filters.search_text:
                search_term = f"%{filters.search_text}%"
                conditions.append(
                    or_(
                        PaymentTerms.code.ilike(search_term),
                        PaymentTerms.name.ilike(search_term),
                        PaymentTerms.description.ilike(search_term)
                    )
                )
            
            # Filtros por días (requiere subconsulta)
            if filters.min_days is not None or filters.max_days is not None:
                # Subconsulta para obtener días mínimos y máximos por payment_terms
                subquery = (
                    select(
                        PaymentSchedule.payment_terms_id,
                        func.min(PaymentSchedule.days).label('min_days'),
                        func.max(PaymentSchedule.days).label('max_days')
                    )
                    .group_by(PaymentSchedule.payment_terms_id)
                    .subquery()
                )
                
                query = query.join(subquery, PaymentTerms.id == subquery.c.payment_terms_id)
                count_query = count_query.join(subquery, PaymentTerms.id == subquery.c.payment_terms_id)
                
                if filters.min_days is not None:
                    conditions.append(subquery.c.min_days >= filters.min_days)
                
                if filters.max_days is not None:
                    conditions.append(subquery.c.max_days <= filters.max_days)
            
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))        # Obtener total
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Aplicar paginación y ordenamiento
        query = query.order_by(PaymentTerms.code).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        payment_terms = result.scalars().all()

        return list(payment_terms), total

    async def update_payment_terms(
        self,
        payment_terms_id: uuid.UUID,
        payment_terms_data: PaymentTermsUpdate
    ) -> PaymentTerms:
        """
        Actualiza condiciones de pago
        
        Args:
            payment_terms_id: ID de las condiciones de pago
            payment_terms_data: Datos actualizados
            
        Returns:
            PaymentTerms: Condiciones de pago actualizadas
            
        Raises:
            NotFoundError: Si no se encuentra
        """
        payment_terms = await self.get_payment_terms_by_id(payment_terms_id)

        # Actualizar campos básicos
        if payment_terms_data.name is not None:
            payment_terms.name = payment_terms_data.name
        if payment_terms_data.description is not None:
            payment_terms.description = payment_terms_data.description
        if payment_terms_data.is_active is not None:
            payment_terms.is_active = payment_terms_data.is_active
        if payment_terms_data.notes is not None:
            payment_terms.notes = payment_terms_data.notes

        # Si se incluye nuevo cronograma, reemplazar completamente
        if payment_terms_data.payment_schedules is not None:
            # Eliminar cronograma actual
            for schedule in payment_terms.payment_schedules:
                await self.db.delete(schedule)
            
            await self.db.flush()
            
            # Crear nuevo cronograma
            for schedule_data in payment_terms_data.payment_schedules:
                schedule = PaymentSchedule(
                    payment_terms_id=payment_terms.id,
                    sequence=schedule_data.sequence,
                    days=schedule_data.days,
                    percentage=schedule_data.percentage,
                    description=schedule_data.description
                )
                self.db.add(schedule)

        await self.db.commit()
        await self.db.refresh(payment_terms)
        
        # Recargar con cronograma
        result = await self.db.execute(
            select(PaymentTerms)
            .options(selectinload(PaymentTerms.payment_schedules))
            .where(PaymentTerms.id == payment_terms.id)
        )
        return result.scalar_one()

    async def delete_payment_terms(self, payment_terms_id: uuid.UUID) -> None:
        """
        Elimina condiciones de pago
        
        Args:
            payment_terms_id: ID de las condiciones de pago
            
        Raises:
            NotFoundError: Si no se encuentra
            ValidationError: Si está en uso
        """
        payment_terms = await self.get_payment_terms_by_id(payment_terms_id)        # Verificar si está en uso (en journal_entry_lines)
        from app.models.journal_entry import JournalEntryLine
        usage_check = await self.db.execute(
            select(func.count(JournalEntryLine.id))
            .where(JournalEntryLine.payment_terms_id == payment_terms_id)
        )
        
        usage_count = usage_check.scalar() or 0
        if usage_count > 0:
            raise ValidationError(
                f"No se puede eliminar la condición de pago '{payment_terms.code}' "
                "porque está siendo utilizada en asientos contables"
            )

        await self.db.delete(payment_terms)
        await self.db.commit()

    async def toggle_active_status(self, payment_terms_id: uuid.UUID) -> PaymentTerms:
        """
        Alterna el estado activo/inactivo de las condiciones de pago
        
        Args:
            payment_terms_id: ID de las condiciones de pago
            
        Returns:
            PaymentTerms: Condiciones de pago actualizadas
        """
        payment_terms = await self.get_payment_terms_by_id(payment_terms_id)
        payment_terms.is_active = not payment_terms.is_active
        
        await self.db.commit()
        await self.db.refresh(payment_terms)
        
        return payment_terms

    async def calculate_payment_dates(
        self,
        request: PaymentCalculationRequest
    ) -> PaymentCalculationResponse:
        """
        Calcula fechas y montos de pago basados en condiciones de pago
        
        Args:
            request: Solicitud de cálculo con términos, fecha y monto
            
        Returns:
            PaymentCalculationResponse: Respuesta con cronograma calculado
        """
        payment_terms = await self.get_payment_terms_by_id(request.payment_terms_id)
        
        if not payment_terms.is_valid:
            raise ValidationError(
                f"Las condiciones de pago '{payment_terms.code}' no son válidas"
            )

        # Calcular fechas y montos
        invoice_datetime = datetime.combine(request.invoice_date, datetime.min.time())
        payments = []
        
        for schedule in payment_terms.payment_schedules:
            payment_date = schedule.calculate_payment_date(invoice_datetime)
            payment_amount = schedule.calculate_amount(request.total_amount)
            
            payments.append(PaymentCalculation(
                sequence=schedule.sequence,
                days=schedule.days,
                percentage=schedule.percentage,
                amount=payment_amount,
                payment_date=payment_date.date(),
                description=schedule.description
            ))

        # Ordenar por secuencia
        payments.sort(key=lambda x: x.sequence)
        
        # Fecha de vencimiento final (último pago)
        final_due_date = max(payment.payment_date for payment in payments)

        return PaymentCalculationResponse(
            payment_terms_code=payment_terms.code,
            payment_terms_name=payment_terms.name,
            invoice_date=request.invoice_date,
            total_amount=request.total_amount,
            payments=payments,
            final_due_date=final_due_date
        )

    async def get_active_payment_terms(self) -> List[PaymentTerms]:
        """
        Obtiene todas las condiciones de pago activas
        
        Returns:
            List[PaymentTerms]: Lista de condiciones de pago activas
        """
        result = await self.db.execute(
            select(PaymentTerms)
            .options(selectinload(PaymentTerms.payment_schedules))
            .where(PaymentTerms.is_active == True)
            .order_by(PaymentTerms.code)
        )
        
        return list(result.scalars().all())

    async def validate_payment_terms(self, payment_terms_id: uuid.UUID) -> Dict[str, Any]:
        """
        Valida las condiciones de pago y retorna detalles de la validación
        
        Args:
            payment_terms_id: ID de las condiciones de pago
            
        Returns:
            Dict: Resultado de la validación con detalles
        """
        payment_terms = await self.get_payment_terms_by_id(payment_terms_id)
        
        validation_result = {
            'is_valid': payment_terms.is_valid,
            'total_percentage': payment_terms.total_percentage,
            'schedule_count': len(payment_terms.payment_schedules),
            'errors': [],
            'warnings': []
        }
        
        # Validaciones específicas
        if not payment_terms.payment_schedules:
            validation_result['errors'].append("No tiene cronograma de pagos definido")
        
        if payment_terms.total_percentage != Decimal('100.00'):
            validation_result['errors'].append(
                f"El porcentaje total es {payment_terms.total_percentage}%, debe ser 100%"
            )
        
        # Validar secuencias
        sequences = [s.sequence for s in payment_terms.payment_schedules]
        if len(set(sequences)) != len(sequences):
            validation_result['errors'].append("Hay secuencias duplicadas")
        
        if sequences and (min(sequences) != 1 or max(sequences) != len(sequences)):
            validation_result['errors'].append("Las secuencias deben ser consecutivas desde 1")
        
        # Validar días en orden
        days_by_sequence = {s.sequence: s.days for s in payment_terms.payment_schedules}
        ordered_days = [days_by_sequence[seq] for seq in sorted(sequences)]
        if ordered_days != sorted(ordered_days):
            validation_result['warnings'].append(
                "Los días no están en orden ascendente según la secuencia"
            )
        
        return validation_result
