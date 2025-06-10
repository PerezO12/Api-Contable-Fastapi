import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType
from app.models.account import Account
from app.schemas.journal_entry import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryRead, JournalEntryLineCreate,
    JournalEntryFilter, JournalEntryStatistics, JournalEntrySummary, JournalEntryPost,
    JournalEntryCancel
)
from app.utils.exceptions import JournalEntryError, AccountNotFoundError, BalanceError


class JournalEntryService:
    """Servicio para operaciones de asientos contables"""
    
    def __init__(self, db: AsyncSession):
        self.db = db    
    async def create_journal_entry(
        self, 
        entry_data: JournalEntryCreate, 
        created_by_id: uuid.UUID
    ) -> JournalEntry:
        """Crear un nuevo asiento contable con optimización async/await"""
        
        # Validación inicial de cuentas en batch para optimizar rendimiento
        account_ids = [line.account_id for line in entry_data.lines]
        accounts_result = await self.db.execute(
            select(Account).where(Account.id.in_(account_ids))
        )
        accounts_dict = {account.id: account for account in accounts_result.scalars().all()}
        
        # Validar que todas las cuentas existen
        missing_accounts = set(account_ids) - set(accounts_dict.keys())
        if missing_accounts:
            raise AccountNotFoundError(account_id=str(list(missing_accounts)[0]))
        
        # Validar que todas las cuentas permiten movimientos
        invalid_accounts = [
            f"{account.code} - {account.name}" 
            for account in accounts_dict.values() 
            if not account.allows_movements
        ]
        if invalid_accounts:
            raise JournalEntryError(f"Las siguientes cuentas no permiten movimientos: {', '.join(invalid_accounts)}")
        
        # Generar número de asiento
        entry_number = await self.generate_entry_number(entry_data.entry_type)
        
        # Crear las líneas en memoria primero (evitar lazy loading)
        journal_lines = []
        total_debit = Decimal('0')
        total_credit = Decimal('0')
        
        for line_number, line_data in enumerate(entry_data.lines, 1):
            # Validaciones de línea
            if line_data.debit_amount < 0 or line_data.credit_amount < 0:
                raise JournalEntryError(f"Los montos no pueden ser negativos en línea {line_number}")
            
            if (line_data.debit_amount > 0 and line_data.credit_amount > 0) or \
               (line_data.debit_amount == 0 and line_data.credit_amount == 0):
                raise JournalEntryError(f"Línea {line_number}: debe tener monto en débito O crédito, no ambos o ninguno")
            
            journal_line = JournalEntryLine(
                account_id=line_data.account_id,
                debit_amount=line_data.debit_amount,
                credit_amount=line_data.credit_amount,
                description=line_data.description,
                reference=line_data.reference,
                third_party_id=line_data.third_party,
                cost_center_id=line_data.cost_center,
                line_number=line_number
            )
            
            journal_lines.append(journal_line)
            total_debit += line_data.debit_amount
            total_credit += line_data.credit_amount
        
        # Validar balance antes de crear el asiento
        if total_debit != total_credit:
            raise BalanceError(
                expected_balance=str(total_debit),
                actual_balance=str(total_credit),
                account_info=f"Asiento {entry_number}"
            )
        
        # Crear el asiento principal con totales calculados
        journal_entry = JournalEntry(
            number=entry_number,
            reference=entry_data.reference,
            description=entry_data.description,
            entry_type=entry_data.entry_type,
            entry_date=entry_data.entry_date,
            status=JournalEntryStatus.DRAFT,
            created_by_id=created_by_id,
            notes=entry_data.notes,
            total_debit=total_debit,
            total_credit=total_credit
        )
        
        self.db.add(journal_entry)
        await self.db.flush()  # Para obtener el ID
        
        # Asignar el journal_entry_id a las líneas y agregarlas a la sesión
        for journal_line in journal_lines:
            journal_line.journal_entry_id = journal_entry.id
            self.db.add(journal_line)
        
        # Commit transaccional
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise JournalEntryError(f"Error al crear el asiento: {str(e)}")
        
        # Recargar el asiento con todas sus relaciones usando selectinload para optimizar
        result = await self.db.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines))
            .where(JournalEntry.id == journal_entry.id)
        )
        journal_entry = result.scalar_one()
        return journal_entry

    async def get_journal_entries(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[JournalEntryFilter] = None
    ) -> Tuple[List[JournalEntry], int]:
        """Obtener lista de asientos contables con filtros"""
        
        query = select(JournalEntry).options(
            selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
            selectinload(JournalEntry.created_by),
            selectinload(JournalEntry.posted_by)
        )
        
        # Aplicar filtros
        conditions = []
        
        if filters:
            if filters.status:
                conditions.append(JournalEntry.status == filters.status)
            
            if filters.entry_type:
                conditions.append(JournalEntry.entry_type == filters.entry_type)
            
            if filters.start_date:
                conditions.append(JournalEntry.entry_date >= filters.start_date)
            
            if filters.end_date:
                conditions.append(JournalEntry.entry_date <= filters.end_date)
            
            if filters.search:
                search_filter = or_(
                    JournalEntry.number.ilike(f"%{filters.search}%"),
                    JournalEntry.description.ilike(f"%{filters.search}%"),
                    JournalEntry.reference.ilike(f"%{filters.search}%")
                )
                conditions.append(search_filter)
            
            if filters.account_id:
                # Usar subconsulta para filtrar por cuenta
                subquery = select(JournalEntryLine.journal_entry_id).where(
                    JournalEntryLine.account_id == filters.account_id
                )
                conditions.append(JournalEntry.id.in_(subquery))
            
            if filters.created_by_id:
                conditions.append(JournalEntry.created_by_id == filters.created_by_id)
        
        # Construir query principal
        if conditions:
            query = query.where(and_(*conditions))
        
        # Contar total
        count_query = select(func.count(JournalEntry.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
          # Aplicar paginación y ordenamiento
        query = query.order_by(desc(JournalEntry.entry_date), JournalEntry.number)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        entries = result.scalars().all()
        
        return list(entries), total
    
    async def get_journal_entry_by_id(self, entry_id: uuid.UUID) -> Optional[JournalEntry]:
        """Obtener un asiento por ID"""
        result = await self.db.execute(
            select(JournalEntry)
            .options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account).selectinload(Account.children),
                selectinload(JournalEntry.created_by),
                selectinload(JournalEntry.posted_by),
                selectinload(JournalEntry.approved_by)
            )
            .where(JournalEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_journal_entry_by_number(self, number: str) -> Optional[JournalEntry]:
        """Obtener un asiento por número"""
        result = await self.db.execute(
            select(JournalEntry)
            .options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account).selectinload(Account.children),
                selectinload(JournalEntry.created_by),
                selectinload(JournalEntry.posted_by)
            )
            .where(JournalEntry.number == number)
        )
        return result.scalar_one_or_none()

    async def update_journal_entry(
        self, 
        entry_id: uuid.UUID, 
        entry_data: JournalEntryUpdate
    ) -> Optional[JournalEntry]:
        """Actualizar un asiento contable"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            return None
        
        # Verificar que se puede modificar
        if not journal_entry.can_be_modified:
            raise JournalEntryError("El asiento no puede ser modificado en su estado actual")
        
        # Actualizar campos básicos
        update_data = entry_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(journal_entry, field):
                setattr(journal_entry, field, value)
        
        await self.db.commit()
        await self.db.refresh(journal_entry)
        
        return journal_entry

    async def approve_journal_entry(
        self, 
        entry_id: uuid.UUID, 
        approved_by_id: uuid.UUID
    ) -> JournalEntry:
        """Aprobar un asiento contable"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            raise JournalEntryError("Asiento no encontrado")
        
        if journal_entry.status != JournalEntryStatus.DRAFT:
            raise JournalEntryError("Solo se pueden aprobar asientos en borrador")
        
        # Validar el asiento antes de aprobar
        errors = journal_entry.validate_entry()
        if errors:
            raise JournalEntryError(f"El asiento no puede ser aprobado: {'; '.join(errors)}")
        
        # Aprobar
        success = journal_entry.approve(approved_by_id)
        if not success:
            raise JournalEntryError("No se pudo aprobar el asiento")
        
        await self.db.commit()
        await self.db.refresh(journal_entry)
        
        return journal_entry

    async def post_journal_entry(
        self, 
        entry_id: uuid.UUID, 
        posted_by_id: uuid.UUID,
        post_data: Optional[JournalEntryPost] = None
    ) -> JournalEntry:
        """Contabilizar un asiento"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            raise JournalEntryError("Asiento no encontrado")
        
        if not journal_entry.can_be_posted:
            raise JournalEntryError("El asiento no puede ser contabilizado en su estado actual")
        
        # Contabilizar
        success = journal_entry.post(posted_by_id)
        if not success:
            raise JournalEntryError("No se pudo contabilizar el asiento")
        
        # Actualizar notas si se proporcionan
        if post_data and post_data.reason:
            if journal_entry.notes:
                journal_entry.notes += f"\\n\\nContabilizado: {post_data.reason}"
            else:
                journal_entry.notes = f"Contabilizado: {post_data.reason}"
        
        await self.db.commit()
        await self.db.refresh(journal_entry)
        
        return journal_entry

    async def cancel_journal_entry(
        self, 
        entry_id: uuid.UUID, 
        cancelled_by_id: uuid.UUID,
        cancel_data: JournalEntryCancel
    ) -> JournalEntry:
        """Anular un asiento contable"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            raise JournalEntryError("Asiento no encontrado")
        
        if journal_entry.status == JournalEntryStatus.CANCELLED:
            raise JournalEntryError("El asiento ya está anulado")
        
        if journal_entry.status == JournalEntryStatus.POSTED:
            # Si está contabilizado, crear asiento de reversión
            await self._create_reversal_entry(
                journal_entry, 
                cancelled_by_id, 
                cancel_data.reason
            )
        
        # Anular el asiento original
        journal_entry.status = JournalEntryStatus.CANCELLED
        journal_entry.cancelled_by_id = cancelled_by_id
        journal_entry.cancelled_at = datetime.now()
        
        # Actualizar notas
        if journal_entry.notes:
            journal_entry.notes += f"\\n\\nAnulado: {cancel_data.reason}"
        else:
            journal_entry.notes = f"Anulado: {cancel_data.reason}"
        
        await self.db.commit()
        await self.db.refresh(journal_entry)
        
        return journal_entry    
    
    async def _create_reversal_entry(
        self, 
        original_entry: JournalEntry, 
        created_by_id: uuid.UUID,
        reason: str
    ) -> JournalEntry:
        """Crear asiento de reversión para anular uno contabilizado"""
        
        # Crear el asiento de reversión
        reversal_entry = JournalEntry(
            number=await self.generate_entry_number(JournalEntryType.REVERSAL),
            reference=f"REV-{original_entry.number}",
            description=f"REVERSIÓN - {original_entry.description}",
            entry_type=JournalEntryType.REVERSAL,
            entry_date=date.today(),
            status=JournalEntryStatus.DRAFT,
            created_by_id=created_by_id,
            notes=f"Reversión del asiento {original_entry.number}. Razón: {reason}"
        )
        
        self.db.add(reversal_entry)
        await self.db.flush()  # Para obtener el ID
        
        # Crear líneas inversas en memoria para evitar lazy loading
        reversal_lines = []
        total_debit = Decimal('0')
        total_credit = Decimal('0')
        
        for original_line in original_entry.lines:
            reversal_line = JournalEntryLine(
                journal_entry_id=reversal_entry.id,
                account_id=original_line.account_id,
                # Invertir débitos y créditos
                debit_amount=original_line.credit_amount,
                credit_amount=original_line.debit_amount,
                description=f"REV - {original_line.description}",
                reference=original_line.reference,
                third_party_id=original_line.third_party_id,
                cost_center_id=original_line.cost_center_id,
                line_number=original_line.line_number
            )
            reversal_lines.append(reversal_line)
            self.db.add(reversal_line)
            total_debit += reversal_line.debit_amount
            total_credit += reversal_line.credit_amount
        
        # Actualizar totales directamente
        reversal_entry.total_debit = total_debit
        reversal_entry.total_credit = total_credit
        
        # Aprobar y contabilizar automáticamente
        reversal_entry.approve(created_by_id)
        reversal_entry.post(created_by_id)
        
        return reversal_entry

    async def get_journal_entry_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> JournalEntryStatistics:
        """Obtener estadísticas de asientos contables"""
        
        conditions = []
        if start_date:
            conditions.append(JournalEntry.entry_date >= start_date)
        if end_date:
            conditions.append(JournalEntry.entry_date <= end_date)
          # Estadísticas por estado
        stats_query = select(
            JournalEntry.status,
            func.count(JournalEntry.id).label('count'),
            func.sum(JournalEntry.total_debit).label('total_amount')
        ).group_by(JournalEntry.status)
        
        if conditions:
            stats_query = stats_query.where(and_(*conditions))
        
        stats_result = await self.db.execute(stats_query)
        stats_by_status = {}
        total_amount_posted = Decimal('0')
        
        for row in stats_result:
            stats_by_status[row[0]] = {'count': int(row[1]), 'amount': row[2] or Decimal('0')}
            if row[0] == JournalEntryStatus.POSTED:
                total_amount_posted = row[2] or Decimal('0')
        
        # Estadísticas por tipo
        type_query = select(
            JournalEntry.entry_type,
            func.count(JournalEntry.id).label('count')
        ).group_by(JournalEntry.entry_type)
        
        if conditions:
            type_query = type_query.where(and_(*conditions))
        type_result = await self.db.execute(type_query)
        stats_by_type = {str(row[0]): int(row[1]) for row in type_result}
          # Estadísticas por mes - Usar alias para evitar problemas de GROUP BY
        month_truncated = func.date_trunc('month', JournalEntry.entry_date).label('month_truncated')
        month_query = select(
            month_truncated,
            func.count(JournalEntry.id).label('count')
        ).group_by(month_truncated)  # Usar el mismo alias en GROUP BY
        
        if conditions:
            month_query = month_query.where(and_(*conditions))
        
        month_query = month_query.order_by(month_truncated)  # Ordenar por mes para resultados consistentes
        month_result = await self.db.execute(month_query)
        stats_by_month = {str(row[0]): int(row[1]) for row in month_result}
          # Calcular estadísticas adicionales para el mes y año actual
        current_date = date.today()
        current_month_start = current_date.replace(day=1)
        current_year_start = current_date.replace(month=1, day=1)
        
        # Entradas de este mes
        month_query = select(func.count(JournalEntry.id)).where(
            JournalEntry.entry_date >= current_month_start
        )
        month_count_result = await self.db.execute(month_query)
        entries_this_month = month_count_result.scalar() or 0
        
        # Entradas de este año
        year_query = select(func.count(JournalEntry.id)).where(
            JournalEntry.entry_date >= current_year_start
        )
        year_count_result = await self.db.execute(year_query)
        entries_this_year = year_count_result.scalar() or 0
          # Calcular totales de débito y crédito
        total_debit_amount = Decimal(str(sum(stat['amount'] for stat in stats_by_status.values())))
        total_credit_amount = total_debit_amount  # En contabilidad siempre deben ser iguales
        
        return JournalEntryStatistics(
            total_entries=sum(stat['count'] for stat in stats_by_status.values()),
            draft_entries=stats_by_status.get(JournalEntryStatus.DRAFT, {'count': 0})['count'],
            approved_entries=stats_by_status.get(JournalEntryStatus.APPROVED, {'count': 0})['count'],
            posted_entries=stats_by_status.get(JournalEntryStatus.POSTED, {'count': 0})['count'],
            cancelled_entries=stats_by_status.get(JournalEntryStatus.CANCELLED, {'count': 0})['count'],
            total_debit_amount=total_debit_amount,
            total_credit_amount=total_credit_amount,
            entries_this_month=entries_this_month,
            entries_this_year=entries_this_year
        )

    async def search_journal_entries(self, filters: JournalEntryFilter) -> List[JournalEntry]:
        """Búsqueda avanzada de asientos contables"""
        
        entries, _ = await self.get_journal_entries(
            skip=0,
            limit=1000,  # Para búsquedas, permitir más resultados
            filters=filters
        )
        return entries

    async def generate_entry_number(self, entry_type: JournalEntryType = JournalEntryType.MANUAL) -> str:
        """Generar número de asiento automáticamente"""
        
        current_year = date.today().year
        
        # Prefijos por tipo
        prefixes = {
            JournalEntryType.MANUAL: "MAN",
            JournalEntryType.AUTOMATIC: "AUT",
            JournalEntryType.ADJUSTMENT: "AJU",
            JournalEntryType.OPENING: "APE",
            JournalEntryType.CLOSING: "CIE",
            JournalEntryType.REVERSAL: "REV"
        }
        
        prefix = prefixes.get(entry_type, "MAN")
        
        # Obtener el último número para este tipo y año
        last_entry_result = await self.db.execute(
            select(JournalEntry.number)
            .where(
                and_(
                    JournalEntry.entry_type == entry_type,
                    func.extract('year', JournalEntry.entry_date) == current_year
                )
            )
            .order_by(desc(JournalEntry.number))
            .limit(1)
        )
        
        last_number = last_entry_result.scalar_one_or_none()
        
        if last_number:
            # Extraer el número secuencial
            try:
                sequence = int(last_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1
        
        return f"{prefix}-{current_year}-{sequence:06d}"

    async def delete_journal_entry(self, entry_id: uuid.UUID) -> bool:
        """Eliminar un asiento contable (solo borradores)"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            return False
        
        if journal_entry.status != JournalEntryStatus.DRAFT:
            raise JournalEntryError("Solo se pueden eliminar asientos en borrador")
        
        await self.db.delete(journal_entry)
        await self.db.commit()
        
        return True

    async def validate_journal_entry(self, entry: JournalEntry) -> Tuple[bool, List[str], List[str]]:
        """Validar un asiento contable y retornar errores y advertencias"""
        
        errors = []
        warnings = []
        
        # Validar estructura básica
        if not entry.lines or len(entry.lines) < 2:
            errors.append("El asiento debe tener al menos 2 líneas")
        
        # Validar balance
        if not entry.is_balanced:
            errors.append(f"El asiento no está balanceado. Débitos: {entry.total_debit}, Créditos: {entry.total_credit}")
        
        # Validar que no todos los montos sean cero
        total_amount = sum(line.debit_amount + line.credit_amount for line in entry.lines)
        if total_amount == 0:
            errors.append("El asiento no puede tener todas las líneas en cero")
        
        # Validar cuentas
        for line in entry.lines:
            if not line.account.allows_movements:
                errors.append(f"La cuenta {line.account.code} no permite movimientos")
            
            if not line.account.is_active:
                warnings.append(f"La cuenta {line.account.code} está inactiva")
        
        is_valid = len(errors) == 0
        
        return is_valid, errors, warnings

    async def bulk_create_journal_entries(
        self, 
        entries_data: List[JournalEntryCreate],
        created_by_id: uuid.UUID
    ) -> List[JournalEntry]:
        """Crear múltiples asientos contables en lote"""
        
        created_entries = []
        
        try:
            for entry_data in entries_data:
                entry = await self.create_journal_entry(entry_data, created_by_id)
                created_entries.append(entry)
            
            return created_entries
            
        except Exception as e:
            # En caso de error, hacer rollback
            await self.db.rollback()
            raise JournalEntryError(f"Error en creación masiva: {str(e)}")
