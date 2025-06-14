"""
Third Party Service for customer, supplier and contact management.
Handles CRUD operations, balance tracking and statement generation.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from math import ceil

from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.third_party import ThirdParty, ThirdPartyType, DocumentType
from app.models.journal_entry import JournalEntryLine, JournalEntry
from app.models.account import Account
from app.schemas.third_party import (
    ThirdPartyCreate, ThirdPartyUpdate, ThirdPartySummary, ThirdPartyList,
    ThirdPartyFilter, ThirdPartyStatement, ThirdPartyMovement, ThirdPartyBalance,
    ThirdPartyAging, ThirdPartyValidation, BulkThirdPartyOperation, ThirdPartyStats,
    ThirdPartyImport, ThirdPartyRead, BulkThirdPartyDelete, BulkThirdPartyDeleteResult,
    ThirdPartyDeleteValidation
)
from app.utils.exceptions import (
    ValidationError, NotFoundError, ConflictError, BusinessLogicError
)


class ThirdPartyService:
    """Servicio para operaciones de terceros"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_third_party(self, third_party_data: ThirdPartyCreate) -> ThirdParty:
        """Crear un nuevo tercero"""
        
        # Validar que no exista un tercero con el mismo código
        existing_code_result = await self.db.execute(
            select(ThirdParty).where(ThirdParty.code == third_party_data.code)
        )
        existing_code = existing_code_result.scalar_one_or_none()
        
        if existing_code:
            raise ConflictError(f"Ya existe un tercero con el código {third_party_data.code}")
        
        # Validar que no exista un tercero con el mismo documento
        existing_doc_result = await self.db.execute(
            select(ThirdParty).where(
                and_(
                    ThirdParty.document_type == third_party_data.document_type,
                    ThirdParty.document_number == third_party_data.document_number
                )
            )
        )
        existing_doc = existing_doc_result.scalar_one_or_none()
        
        if existing_doc:
            raise ConflictError(
                f"Ya existe un tercero con {third_party_data.document_type.value} {third_party_data.document_number}"
            )
        
        # Crear el tercero
        third_party = ThirdParty(**third_party_data.model_dump())
        
        # Validar el modelo
        validation_errors = third_party.validate_third_party()
        if validation_errors:
            raise ValidationError(f"Errores de validación: {'; '.join(validation_errors)}")
        
        self.db.add(third_party)
        await self.db.commit()
        await self.db.refresh(third_party)
        
        return third_party

    async def get_third_party_by_id(self, third_party_id: uuid.UUID) -> Optional[ThirdParty]:
        """Obtener tercero por ID"""
        result = await self.db.execute(
            select(ThirdParty).where(ThirdParty.id == third_party_id)
        )
        return result.scalar_one_or_none()

    async def get_third_party_by_code(self, code: str) -> Optional[ThirdParty]:
        """Obtener tercero por código"""
        result = await self.db.execute(
            select(ThirdParty).where(ThirdParty.code == code)
        )
        return result.scalar_one_or_none()

    async def get_third_party_by_document(
        self, 
        document_type: DocumentType, 
        document_number: str
    ) -> Optional[ThirdParty]:
        """Obtener tercero por documento"""
        result = await self.db.execute(
            select(ThirdParty).where(
                and_(
                    ThirdParty.document_type == document_type,
                    ThirdParty.document_number == document_number
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_third_party(
        self, 
        third_party_id: uuid.UUID, 
        third_party_data: ThirdPartyUpdate
    ) -> ThirdParty:
        """Actualizar tercero"""
        
        third_party = await self.get_third_party_by_id(third_party_id)
        if not third_party:
            raise NotFoundError("Tercero no encontrado")
        
        # Validar unicidad de documento si se actualiza
        if (third_party_data.document_type is not None or 
            third_party_data.document_number is not None):
            
            new_doc_type = third_party_data.document_type or third_party.document_type
            new_doc_number = third_party_data.document_number or third_party.document_number
            
            existing_doc_result = await self.db.execute(
                select(ThirdParty).where(
                    and_(
                        ThirdParty.document_type == new_doc_type,
                        ThirdParty.document_number == new_doc_number,
                        ThirdParty.id != third_party_id
                    )
                )
            )
            existing_doc = existing_doc_result.scalar_one_or_none()
            
            if existing_doc:
                raise ConflictError(
                    f"Ya existe otro tercero con {new_doc_type.value} {new_doc_number}"
                )
        
        # Actualizar campos
        for field, value in third_party_data.model_dump(exclude_unset=True).items():
            setattr(third_party, field, value)
        
        # Validar el modelo actualizado
        validation_errors = third_party.validate_third_party()
        if validation_errors:
            raise ValidationError(f"Errores de validación: {'; '.join(validation_errors)}")
        
        await self.db.commit()
        await self.db.refresh(third_party)
        
        return third_party

    async def delete_third_party(self, third_party_id: uuid.UUID) -> bool:
        """Eliminar tercero"""
        
        third_party = await self.get_third_party_by_id(third_party_id)
        if not third_party:
            raise NotFoundError("Tercero no encontrado")
        
        # Verificar que no tenga movimientos asociados
        movements_result = await self.db.execute(
            select(func.count(JournalEntryLine.id))
            .where(JournalEntryLine.third_party_id == third_party_id)
        )
        movements_count = movements_result.scalar() or 0
        
        if movements_count > 0:
            raise BusinessLogicError(
                f"No se puede eliminar el tercero porque tiene {movements_count} movimientos asociados"
            )
        
        await self.db.delete(third_party)
        await self.db.commit()
        
        return True

    async def get_third_parties_list(
        self, 
        filter_params: ThirdPartyFilter,
        skip: int = 0,
        limit: int = 100
    ) -> ThirdPartyList:
        """Obtener lista paginada de terceros"""
        
        # Construir query base
        query = select(ThirdParty)
        
        # Aplicar filtros
        conditions = []
        
        if filter_params.search:
            search_term = f"%{filter_params.search}%"
            conditions.append(
                or_(
                    ThirdParty.code.ilike(search_term),
                    ThirdParty.name.ilike(search_term),
                    ThirdParty.commercial_name.ilike(search_term),
                    ThirdParty.document_number.ilike(search_term)
                )
            )
        
        if filter_params.third_party_type is not None:
            conditions.append(ThirdParty.third_party_type == filter_params.third_party_type)
        
        if filter_params.document_type is not None:
            conditions.append(ThirdParty.document_type == filter_params.document_type)
        
        if filter_params.is_active is not None:
            conditions.append(ThirdParty.is_active == filter_params.is_active)
        
        if filter_params.city:
            conditions.append(ThirdParty.city.ilike(f"%{filter_params.city}%"))
        
        if filter_params.country:
            conditions.append(ThirdParty.country.ilike(f"%{filter_params.country}%"))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Contar total
        count_query = select(func.count(ThirdParty.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Aplicar paginación y ordenamiento
        query = query.order_by(ThirdParty.name).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        third_parties = result.scalars().all()
        
        # Convertir a summaries
        third_party_summaries = []
        for tp in third_parties:
            summary = ThirdPartySummary(
                id=tp.id,
                code=tp.code,
                name=tp.name,
                commercial_name=tp.commercial_name,
                third_party_type=tp.third_party_type,
                document_number=tp.document_number,
                email=tp.email,
                phone=tp.phone,
                is_active=tp.is_active
            )
            third_party_summaries.append(summary)
        
        # Calcular paginación
        pages = ceil(total / limit) if limit > 0 else 1
        page = (skip // limit) + 1 if limit > 0 else 1
        
        return ThirdPartyList(
            third_parties=third_party_summaries,
            total=total,
            page=page,
            size=len(third_party_summaries),
            pages=pages
        )

    async def get_third_party_movements(
        self, 
        third_party_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ThirdPartyMovement]:
        """Obtener movimientos de un tercero"""
        
        query = (
            select(
                JournalEntryLine.journal_entry_id,
                JournalEntry.number,
                JournalEntry.entry_date,
                Account.code,
                Account.name,
                JournalEntryLine.description,
                JournalEntryLine.debit_amount,
                JournalEntryLine.credit_amount,
                JournalEntryLine.reference
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .join(Account, JournalEntryLine.account_id == Account.id)
            .where(JournalEntryLine.third_party_id == third_party_id)
            .order_by(desc(JournalEntry.entry_date), JournalEntry.number)
        )
        
        # Aplicar filtros de fecha
        if start_date:
            query = query.where(JournalEntry.entry_date >= start_date)
        if end_date:
            query = query.where(JournalEntry.entry_date <= end_date)
        
        result = await self.db.execute(query)
        movements = []
        running_balance = Decimal('0')
        
        for row in result:
            # Calcular balance acumulado
            movement_amount = row.debit_amount - row.credit_amount
            running_balance += movement_amount
            
            movement = ThirdPartyMovement(
                journal_entry_id=row.journal_entry_id,
                journal_entry_number=row.number,
                entry_date=row.entry_date,
                account_code=row.code,
                account_name=row.name,
                description=row.description,
                debit_amount=row.debit_amount,
                credit_amount=row.credit_amount,
                balance=running_balance,
                reference=row.reference
            )
            movements.append(movement)
        
        return movements

    async def get_third_party_statement(
        self, 
        third_party_id: uuid.UUID,
        start_date: date,
        end_date: date
    ) -> ThirdPartyStatement:
        """Generar estado de cuenta de tercero"""
        
        third_party = await self.get_third_party_by_id(third_party_id)
        if not third_party:
            raise NotFoundError("Tercero no encontrado")
        
        # Calcular saldo inicial
        opening_balance_query = (
            select(
                func.coalesce(func.sum(JournalEntryLine.debit_amount), 0) -
                func.coalesce(func.sum(JournalEntryLine.credit_amount), 0)
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(
                and_(
                    JournalEntryLine.third_party_id == third_party_id,
                    JournalEntry.entry_date < start_date
                )
            )
        )
        
        opening_result = await self.db.execute(opening_balance_query)
        opening_balance = opening_result.scalar() or Decimal('0')
        
        # Obtener movimientos del período
        movements = await self.get_third_party_movements(
            third_party_id, start_date, end_date
        )
          # Calcular totales
        total_debits = Decimal(str(sum(m.debit_amount for m in movements))) if movements else Decimal('0')
        total_credits = Decimal(str(sum(m.credit_amount for m in movements))) if movements else Decimal('0')
        closing_balance = opening_balance + total_debits - total_credits
        
        return ThirdPartyStatement(
            third_party=ThirdPartyRead.model_validate(third_party),
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            opening_balance=opening_balance,
            movements=movements,
            closing_balance=closing_balance,
            total_debits=total_debits,
            total_credits=total_credits,
            movement_count=len(movements)
        )

    async def get_third_party_balance(self, third_party_id: uuid.UUID) -> ThirdPartyBalance:
        """Obtener saldo actual de tercero"""
        
        third_party = await self.get_third_party_by_id(third_party_id)
        if not third_party:
            raise NotFoundError("Tercero no encontrado")
        
        # Calcular saldo actual
        balance_query = (
            select(
                func.coalesce(func.sum(JournalEntryLine.debit_amount), 0) -
                func.coalesce(func.sum(JournalEntryLine.credit_amount), 0)
            )
            .where(JournalEntryLine.third_party_id == third_party_id)
        )
        
        balance_result = await self.db.execute(balance_query)
        current_balance = balance_result.scalar() or Decimal('0')
          # Convertir límite de crédito si existe
        credit_limit = None
        available_credit = None
        if third_party.credit_limit:
            try:
                credit_limit = Decimal(third_party.credit_limit)
                available_credit = credit_limit - abs(current_balance)
            except (ValueError, TypeError):
                pass
        
        return ThirdPartyBalance(
            third_party_id=third_party_id,
            third_party_code=third_party.code,
            third_party_name=third_party.name,
            third_party_type=third_party.third_party_type,
            current_balance=current_balance,
            credit_limit=credit_limit,
            available_credit=available_credit
        )

    async def get_third_parties_by_type(self, third_party_type: ThirdPartyType) -> List[ThirdParty]:
        """Obtener terceros por tipo"""
        result = await self.db.execute(
            select(ThirdParty)
            .where(
                and_(
                    ThirdParty.third_party_type == third_party_type,
                    ThirdParty.is_active == True
                )
            )
            .order_by(ThirdParty.name)
        )
        return list(result.scalars().all())

    async def validate_third_party(self, third_party_id: uuid.UUID) -> ThirdPartyValidation:
        """Validar un tercero"""
        
        third_party = await self.get_third_party_by_id(third_party_id)
        if not third_party:
            return ThirdPartyValidation(
                is_valid=False,
                errors=["Tercero no encontrado"],
                warnings=[],
                code_unique=False,
                document_unique=False
            )
        
        errors = third_party.validate_third_party()
        warnings = []
        
        # Validar unicidad del código
        code_query = select(func.count(ThirdParty.id)).where(
            and_(
                ThirdParty.code == third_party.code,
                ThirdParty.id != third_party_id
            )
        )
        code_result = await self.db.execute(code_query)
        code_unique = (code_result.scalar() or 0) == 0
        
        if not code_unique:
            errors.append("El código del tercero ya existe")
        
        # Validar unicidad del documento
        doc_query = select(func.count(ThirdParty.id)).where(
            and_(
                ThirdParty.document_type == third_party.document_type,
                ThirdParty.document_number == third_party.document_number,
                ThirdParty.id != third_party_id
            )
        )
        doc_result = await self.db.execute(doc_query)
        document_unique = (doc_result.scalar() or 0) == 0
        
        if not document_unique:
            errors.append("El documento del tercero ya existe")
        
        # Warnings
        if not third_party.email:
            warnings.append("Tercero sin email configurado")
        
        if not third_party.phone and not third_party.mobile:
            warnings.append("Tercero sin teléfono configurado")
        
        return ThirdPartyValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            code_unique=code_unique,
            document_unique=document_unique
        )

    async def get_third_party_stats(self) -> ThirdPartyStats:
        """Obtener estadísticas de terceros"""
        
        # Contar totales
        total_query = select(func.count(ThirdParty.id))
        total_result = await self.db.execute(total_query)
        total_third_parties = total_result.scalar() or 0
        
        # Contar activos
        active_query = select(func.count(ThirdParty.id)).where(ThirdParty.is_active == True)
        active_result = await self.db.execute(active_query)
        active_third_parties = active_result.scalar() or 0
        
        # Contar por tipo
        customers_query = select(func.count(ThirdParty.id)).where(
            ThirdParty.third_party_type == ThirdPartyType.CUSTOMER
        )
        customers_result = await self.db.execute(customers_query)
        customers = customers_result.scalar() or 0
        
        suppliers_query = select(func.count(ThirdParty.id)).where(
            ThirdParty.third_party_type == ThirdPartyType.SUPPLIER
        )
        suppliers_result = await self.db.execute(suppliers_query)
        suppliers = suppliers_result.scalar() or 0
        
        employees_query = select(func.count(ThirdParty.id)).where(
            ThirdParty.third_party_type == ThirdPartyType.EMPLOYEE
        )
        employees_result = await self.db.execute(employees_query)
        employees = employees_result.scalar() or 0
        
        others = total_third_parties - customers - suppliers - employees
        
        # Contar con email
        email_query = select(func.count(ThirdParty.id)).where(
            ThirdParty.email.is_not(None)
        )
        email_result = await self.db.execute(email_query)
        with_email = email_result.scalar() or 0
        
        # Contar con teléfono
        phone_query = select(func.count(ThirdParty.id)).where(
            or_(
                ThirdParty.phone.is_not(None),
                ThirdParty.mobile.is_not(None)
            )
        )
        phone_result = await self.db.execute(phone_query)
        with_phone = phone_result.scalar() or 0
        
        # Contar por país
        country_query = select(
            ThirdParty.country,
            func.count(ThirdParty.id)
        ).where(
            ThirdParty.country.is_not(None)
        ).group_by(ThirdParty.country)
        
        country_result = await self.db.execute(country_query)
        by_country = {row[0]: row[1] for row in country_result}
        
        return ThirdPartyStats(
            total_third_parties=total_third_parties,
            active_third_parties=active_third_parties,
            inactive_third_parties=total_third_parties - active_third_parties,
            customers=customers,
            suppliers=suppliers,
            employees=employees,
            others=others,
            with_email=with_email,
            with_phone=with_phone,
            by_country=by_country
        )

    async def bulk_operation(self, operation_data: BulkThirdPartyOperation) -> Dict[str, Any]:
        """Operación masiva en terceros"""
        
        results = {
            "success": [],
            "errors": [],
            "total_processed": len(operation_data.third_party_ids)
        }
        
        for third_party_id in operation_data.third_party_ids:
            try:
                third_party = await self.get_third_party_by_id(third_party_id)
                if not third_party:
                    results["errors"].append({
                        "id": str(third_party_id),
                        "error": "Tercero no encontrado"
                    })
                    continue
                
                if operation_data.operation == "activate":
                    third_party.is_active = True
                elif operation_data.operation == "deactivate":
                    third_party.is_active = False
                elif operation_data.operation == "update_type":
                    if operation_data.new_type:
                        third_party.third_party_type = operation_data.new_type
                elif operation_data.operation == "delete":
                    await self.delete_third_party(third_party_id)
                    results["success"].append(str(third_party_id))
                    continue
                
                await self.db.commit()
                results["success"].append(str(third_party_id))
                
            except Exception as e:
                results["errors"].append({
                    "id": str(third_party_id),
                    "error": str(e)
                })
        
        return results

    async def validate_third_party_for_deletion(self, third_party_id: uuid.UUID) -> 'ThirdPartyDeleteValidation':
        """Validar si un tercero puede ser eliminado"""
        from app.schemas.third_party import ThirdPartyDeleteValidation
        
        third_party = await self.get_third_party_by_id(third_party_id)
        if not third_party:
            return ThirdPartyDeleteValidation(
                third_party_id=third_party_id,
                can_delete=False,
                blocking_reasons=["Tercero no encontrado"],
                warnings=[],
                dependencies={}
            )
        
        blocking_reasons = []
        warnings = []
        dependencies = {}
          # Verificar que no tenga asientos contables
        journal_entries_result = await self.db.execute(
            select(func.count(JournalEntryLine.id))
            .where(JournalEntryLine.third_party_id == third_party_id)
        )
        journal_entries_count = journal_entries_result.scalar() or 0
        
        if journal_entries_count > 0:
            blocking_reasons.append(f"El tercero tiene {journal_entries_count} asientos contables asociados")
            dependencies["journal_entries_count"] = journal_entries_count
        
        # Advertencias - Calcular saldo actual
        balance_query = (
            select(
                func.coalesce(func.sum(JournalEntryLine.debit_amount), 0) -
                func.coalesce(func.sum(JournalEntryLine.credit_amount), 0)
            )
            .where(JournalEntryLine.third_party_id == third_party_id)
        )
        
        balance_result = await self.db.execute(balance_query)
        current_balance = balance_result.scalar() or Decimal('0')
        
        if current_balance != 0:
            warnings.append(f"El tercero tiene un saldo pendiente de {current_balance}")
            dependencies["current_balance"] = str(current_balance)
        
        if not third_party.is_active:
            warnings.append("El tercero ya está inactivo")
        
        # Verificar si tiene transacciones recientes (últimos 30 días)
        recent_transactions_result = await self.db.execute(
            select(func.count(JournalEntryLine.id))
            .where(
                and_(
                    JournalEntryLine.third_party_id == third_party_id,
                    JournalEntryLine.created_at >= datetime.now().date().replace(day=1)  # Este mes
                )
            )
        )
        recent_transactions_count = recent_transactions_result.scalar() or 0
        
        if recent_transactions_count > 0:
            warnings.append(f"El tercero tiene {recent_transactions_count} transacciones este mes")
            dependencies["recent_transactions_count"] = recent_transactions_count
        
        can_delete = len(blocking_reasons) == 0
        
        return ThirdPartyDeleteValidation(
            third_party_id=third_party_id,
            can_delete=can_delete,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            dependencies=dependencies
        )
    
    async def bulk_delete_third_parties(self, delete_request: 'BulkThirdPartyDelete') -> 'BulkThirdPartyDeleteResult':
        """Borrar múltiples terceros con validaciones exhaustivas"""
        from app.schemas.third_party import BulkThirdPartyDeleteResult
        
        result = BulkThirdPartyDeleteResult(
            total_requested=len(delete_request.third_party_ids),
            successfully_deleted=[],
            failed_to_delete=[],
            validation_errors=[],
            warnings=[]
        )
        
        # Validar primero todos los terceros
        validations = {}
        for third_party_id in delete_request.third_party_ids:
            validation = await self.validate_third_party_for_deletion(third_party_id)
            validations[third_party_id] = validation
            
            if not validation.can_delete and not delete_request.force_delete:
                result.failed_to_delete.append({
                    "third_party_id": str(third_party_id),
                    "reason": "; ".join(validation.blocking_reasons),
                    "details": validation.dependencies
                })
            elif validation.warnings:
                result.warnings.extend([
                    f"Tercero {third_party_id}: {warning}" for warning in validation.warnings
                ])
        
        # Si force_delete es False y hay errores, no proceder
        if not delete_request.force_delete and result.failed_to_delete:
            result.validation_errors.append({
                "error": "Hay terceros que no pueden eliminarse. Use force_delete=true para intentar forzar la eliminación."
            })
            return result
        
        # Proceder con la eliminación
        third_parties_to_delete = []
        for third_party_id in delete_request.third_party_ids:
            validation = validations[third_party_id]
            
            if validation.can_delete:
                third_parties_to_delete.append(third_party_id)
            elif delete_request.force_delete:
                # Con force_delete, solo proceder si no hay asientos contables críticos
                has_critical_blocks = any(
                    "asientos contables" in reason for reason in validation.blocking_reasons
                )
                if not has_critical_blocks:
                    third_parties_to_delete.append(third_party_id)
                else:
                    result.failed_to_delete.append({
                        "third_party_id": str(third_party_id),
                        "reason": "No se puede forzar la eliminación: " + "; ".join(validation.blocking_reasons),
                        "details": validation.dependencies
                    })
        
        # Eliminar los terceros validados
        for third_party_id in third_parties_to_delete:
            try:
                await self.delete_third_party(third_party_id)
                result.successfully_deleted.append(third_party_id)
                await self.db.commit()
            except Exception as e:
                await self.db.rollback()
                result.failed_to_delete.append({
                    "third_party_id": str(third_party_id),
                    "reason": str(e),
                    "details": {}
                })
        
        # Añadir información sobre la razón de eliminación si se proporcionó
        if delete_request.delete_reason and result.successfully_deleted:
            result.warnings.append(f"Razón de eliminación: {delete_request.delete_reason}")
        
        return result
