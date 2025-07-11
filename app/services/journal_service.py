from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy import and_, or_, func, desc, asc, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.future import select

from app.models.journal import Journal, JournalType
from app.models.journal_entry import JournalEntry
from app.models.account import Account
from app.models.user import User
from app.schemas.journal import (
    JournalCreate, JournalUpdate, JournalFilter,
    JournalStats, JournalSequenceInfo,
    BankJournalConfigCreate, BankJournalConfigUpdate, 
    BankJournalConfigRead, BankJournalConfigValidation,
    JournalWithBankConfig, AccountRead
)
from app.utils.exceptions import (
    AccountingSystemException, AccountNotFoundError, AccountValidationError
)


class JournalNotFoundError(AccountingSystemException):
    """Exception for when a journal is not found"""
    def __init__(self, journal_id: str):
        message = f"Diario con ID {journal_id} no encontrado"
        super().__init__(message, "JOURNAL_NOT_FOUND", {"journal_id": journal_id})


class JournalValidationError(AccountingSystemException):
    """Exception for journal validation errors"""
    def __init__(self, field: str, value: Optional[str] = None, reason: str = "Invalid value"):
        message = f"Error de validación en diario - campo '{field}': {reason}"
        details = {"field": field, "value": value, "reason": reason}
        super().__init__(message, "JOURNAL_VALIDATION_ERROR", details)


class JournalDuplicateError(AccountingSystemException):
    """Exception for duplicate journal errors"""
    def __init__(self, field: str, value: str):
        message = f"Ya existe un diario con {field} '{value}'"
        super().__init__(message, "JOURNAL_DUPLICATE_ERROR", {"field": field, "value": value})


class JournalService:
    """Servicio para gestión de diarios contables"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_journal(
        self, 
        journal_data: JournalCreate, 
        current_user_id: uuid.UUID
    ) -> Journal:
        """
        Crea un nuevo diario
        """
        # Verificar que no exista un diario con el mismo código
        existing_code = await self.db.execute(
            select(Journal).where(Journal.code == journal_data.code)
        )
        if existing_code.scalar_one_or_none():
            raise JournalDuplicateError("código", journal_data.code)

        # Verificar que no exista un diario con el mismo prefijo de secuencia
        existing_prefix = await self.db.execute(
            select(Journal).where(Journal.sequence_prefix == journal_data.sequence_prefix)
        )
        if existing_prefix.scalar_one_or_none():
            raise JournalDuplicateError("prefijo", journal_data.sequence_prefix)

        # Validar que la cuenta por defecto exista si se especifica
        if journal_data.default_account_id:
            account = await self.db.execute(
                select(Account).where(Account.id == journal_data.default_account_id)
            )
            if not account.scalar_one_or_none():
                raise JournalValidationError("default_account_id", str(journal_data.default_account_id), "La cuenta por defecto especificada no existe")

        # Crear el diario
        journal = Journal(
            **journal_data.model_dump(),            created_by_id=current_user_id,
            current_sequence_number=0,
            last_sequence_reset_year=datetime.now(timezone.utc).year
        )

        self.db.add(journal)
        await self.db.commit()
        await self.db.refresh(journal)

        return journal

    async def get_journal_by_id_with_count(self, journal_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Obtiene un diario por ID con conteo manual de journal entries"""
        # Obtener el journal básico
        result = await self.db.execute(
            select(Journal)
            .options(
                joinedload(Journal.default_account),
                joinedload(Journal.created_by),
                selectinload(Journal.bank_config)
            )
            .where(Journal.id == journal_id)
        )
        journal = result.scalar_one_or_none()
        
        if not journal:
            return None        
        # Calcular manualmente el total de journal entries
        count_result = await self.db.execute(
            select(func.count(JournalEntry.id)).where(JournalEntry.journal_id == journal_id)
        )
        total_entries = count_result.scalar() or 0
        
        return {
            'journal': journal,
            'total_journal_entries': total_entries
        }

    async def get_journal_by_id(self, journal_id: uuid.UUID) -> Optional[Journal]:
        """Obtiene un diario por ID (método simple sin conteo)"""
        result = await self.db.execute(
            select(Journal)
            .options(
                joinedload(Journal.default_account),
                joinedload(Journal.created_by),
                selectinload(Journal.bank_config)
            )
            .where(Journal.id == journal_id)
        )
        return result.scalar_one_or_none()

    async def get_journal_by_code(self, code: str) -> Optional[Journal]:
        """Obtiene un diario por código"""
        result = await self.db.execute(
            select(Journal).where(Journal.code == code)
        )
        return result.scalar_one_or_none()

    async def get_journals_list(
        self, 
        filters: JournalFilter,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "name",
        order_dir: str = "asc"
    ) -> List[Dict[str, Any]]:
        """
        Obtiene lista de diarios con conteo de asientos para JournalListItem        """
        # Query principal con joins para obtener información completa
        query = select(Journal).options(
            joinedload(Journal.default_account)
        )

        # Aplicar filtros
        conditions = []
        
        if filters.type is not None:
            conditions.append(Journal.type == filters.type)
            
        if filters.is_active is not None:
            conditions.append(Journal.is_active == filters.is_active)
            
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Journal.name.ilike(search_term),
                    Journal.code.ilike(search_term),
                    Journal.description.ilike(search_term)
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Aplicar ordenamiento
        order_column = getattr(Journal, order_by, Journal.name)
        if order_dir.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # Aplicar paginación
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        journals = result.scalars().all()
        
        # Convertir a lista de diccionarios con conteo manual de journal entries
        journals_list = []
        for journal in journals:
            # Calcular conteo de journal entries para cada journal
            count_result = await self.db.execute(
                select(func.count(JournalEntry.id)).where(JournalEntry.journal_id == journal.id)
            )
            total_entries = count_result.scalar() or 0
            
            journals_list.append({
                'id': journal.id,
                'name': journal.name,
                'code': journal.code,
                'type': journal.type,
                'sequence_prefix': journal.sequence_prefix,
                'is_active': journal.is_active,
                'current_sequence_number': journal.current_sequence_number,
                'total_journal_entries': total_entries,
                'created_at': journal.created_at,
                'default_account': journal.default_account
            })
        
        return journals_list

    async def get_journals(
        self, 
        filters: JournalFilter,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "name",
        order_dir: str = "asc"
    ) -> List[Journal]:
        """
        Obtiene lista de diarios con filtros y paginación
        """
        query = select(Journal).options(
            joinedload(Journal.default_account)
        )

        # Aplicar filtros
        conditions = []
        
        if filters.type is not None:
            conditions.append(Journal.type == filters.type)
            
        if filters.is_active is not None:
            conditions.append(Journal.is_active == filters.is_active)
            
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Journal.name.ilike(search_term),
                    Journal.code.ilike(search_term),
                    Journal.description.ilike(search_term)
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Aplicar ordenamiento
        order_column = getattr(Journal, order_by, Journal.name)
        if order_dir.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # Aplicar paginación
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_journals(self, filters: JournalFilter) -> int:
        """Cuenta el total de diarios que coinciden con los filtros"""
        query = select(func.count(Journal.id))

        conditions = []
        
        if filters.type is not None:
            conditions.append(Journal.type == filters.type)
            
        if filters.is_active is not None:
            conditions.append(Journal.is_active == filters.is_active)
            
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Journal.name.ilike(search_term),
                    Journal.code.ilike(search_term),
                    Journal.description.ilike(search_term)
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def update_journal(
        self, 
        journal_id: uuid.UUID, 
        journal_data: JournalUpdate
    ) -> Optional[Journal]:
        """
        Actualiza un diario existente
        """
        journal = await self.get_journal_by_id(journal_id)
        if not journal:
            raise JournalNotFoundError(str(journal_id))

        # Validar cuenta por defecto si se especifica
        if journal_data.default_account_id is not None:
            account = await self.db.execute(
                select(Account).where(Account.id == journal_data.default_account_id)
            )
            if not account.scalar_one_or_none():
                raise JournalValidationError("default_account_id", str(journal_data.default_account_id), "La cuenta por defecto especificada no existe")

        # Actualizar campos
        update_data = journal_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(journal, field, value)

        await self.db.commit()
        await self.db.refresh(journal)

        return journal

    async def delete_journal(self, journal_id: uuid.UUID) -> bool:
        """
        Elimina un diario
        """
        journal = await self.get_journal_by_id(journal_id)
        if not journal:
            raise JournalNotFoundError(str(journal_id))

        # Verificar que no tenga asientos contables asociados
        entries_count = await self.db.execute(
            select(func.count(JournalEntry.id)).where(JournalEntry.journal_id == journal_id)
        )
        count_result = entries_count.scalar()
        if count_result and count_result > 0:
            raise JournalValidationError("journal_entries", str(count_result), "No se puede eliminar un diario que tiene asientos contables asociados")

        await self.db.delete(journal)
        await self.db.commit()

        return True

    async def get_next_sequence_number(
        self, 
        journal_id: uuid.UUID,
        year: Optional[int] = None
    ) -> str:
        """
        Obtiene el siguiente número de secuencia para un diario
        """
        journal = await self.get_journal_by_id(journal_id)
        if not journal:
            raise JournalNotFoundError(str(journal_id))

        if year is None:
            year = datetime.now(timezone.utc).year

        return journal.get_next_sequence_number(year)

    async def reset_sequence(
        self, 
        journal_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> Journal:
        """
        Resetea la secuencia de numeración de un diario
        """
        journal = await self.get_journal_by_id(journal_id)
        if not journal:
            raise JournalNotFoundError(str(journal_id))

        current_year = datetime.now(timezone.utc).year
        journal.current_sequence_number = 0
        journal.last_sequence_reset_year = current_year

        await self.db.commit()
        await self.db.refresh(journal)

        return journal

    async def get_journal_stats(self, journal_id: uuid.UUID) -> JournalStats:
        """
        Obtiene estadísticas de un diario
        """
        journal = await self.get_journal_by_id(journal_id)
        if not journal:
            raise JournalNotFoundError(str(journal_id))

        current_year = datetime.now(timezone.utc).year
        current_month = datetime.now(timezone.utc).month

        # Total de asientos
        total_entries = await self.db.execute(
            select(func.count(JournalEntry.id))
            .where(JournalEntry.journal_id == journal_id)
        )
        total_entries = total_entries.scalar() or 0

        # Asientos del año actual
        entries_current_year = await self.db.execute(
            select(func.count(JournalEntry.id))
            .where(
                and_(
                    JournalEntry.journal_id == journal_id,
                    extract('year', JournalEntry.entry_date) == current_year
                )
            )
        )
        entries_current_year = entries_current_year.scalar() or 0

        # Asientos del mes actual
        entries_current_month = await self.db.execute(
            select(func.count(JournalEntry.id))
            .where(
                and_(
                    JournalEntry.journal_id == journal_id,
                    extract('year', JournalEntry.entry_date) == current_year,
                    extract('month', JournalEntry.entry_date) == current_month
                )
            )
        )
        entries_current_month = entries_current_month.scalar() or 0

        # Último asiento
        last_entry = await self.db.execute(
            select(JournalEntry.entry_date)
            .where(JournalEntry.journal_id == journal_id)
            .order_by(desc(JournalEntry.entry_date))
            .limit(1)
        )
        last_entry_date = last_entry.scalar_one_or_none()

        # Promedio por mes (cálculo básico)
        months_since_creation = 1  # Por defecto al menos 1 mes
        if journal.created_at:
            months_diff = (datetime.now(timezone.utc) - journal.created_at).days / 30
            months_since_creation = max(1, int(months_diff))

        avg_entries_per_month = total_entries / months_since_creation

        return JournalStats(
            id=journal.id,
            name=journal.name,
            code=journal.code,
            type=journal.type,
            total_entries=total_entries,
            total_entries_current_year=entries_current_year,
            total_entries_current_month=entries_current_month,
            last_entry_date=last_entry_date,
            avg_entries_per_month=round(avg_entries_per_month, 2)
        )

    async def get_journals_by_type(self, journal_type: JournalType) -> List[Journal]:
        """Obtiene todos los diarios activos de un tipo específico"""
        result = await self.db.execute(
            select(Journal)
            .where(
                and_(
                    Journal.type == journal_type,
                    Journal.is_active == True
                )
            )
            .order_by(Journal.name)
        )
        return list(result.scalars().all())

    async def get_default_journal_for_type(self, journal_type: JournalType) -> Optional[Journal]:
        """
        Obtiene el diario por defecto para un tipo específico
        (el primero activo de ese tipo)
        """
        result = await self.db.execute(
            select(Journal)
            .where(
                and_(
                    Journal.type == journal_type,
                    Journal.is_active == True
                )
            )
            .order_by(Journal.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_sequence_info(self, journal_id: uuid.UUID) -> JournalSequenceInfo:
        """
        Obtiene información de la secuencia de numeración de un diario
        """
        journal = await self.get_journal_by_id(journal_id)
        if not journal:
            raise JournalNotFoundError(str(journal_id))

        next_number = journal.get_next_sequence_number()

        return JournalSequenceInfo(
            id=journal.id,
            name=journal.name,
            code=journal.code,
            sequence_prefix=journal.sequence_prefix,
            current_sequence_number=journal.current_sequence_number,
            next_sequence_number=next_number,
            include_year_in_sequence=journal.include_year_in_sequence,
            reset_sequence_yearly=journal.reset_sequence_yearly,
            last_sequence_reset_year=journal.last_sequence_reset_year
        )

    # Métodos para configuración bancaria

    async def create_bank_config(
        self, 
        journal_id: uuid.UUID, 
        config_data: "BankJournalConfigCreate"
    ) -> "JournalWithBankConfig":
        """
        Crear configuración bancaria para un diario
        """
        # Verificar que el diario existe y es tipo BANK
        journal = await self.get_journal_by_id(journal_id)
        if not journal:
            raise JournalNotFoundError(str(journal_id))
        
        if not journal.is_bank_journal():
            raise JournalValidationError(
                "type", 
                journal.type.value, 
                "Solo los diarios tipo BANK pueden tener configuración bancaria"
            )
        
        # Verificar que no existe configuración previa
        if journal.bank_config:
            raise JournalValidationError(
                "bank_config", 
                "already_exists", 
                "El diario ya tiene configuración bancaria"
            )
        
        # Crear la configuración
        from app.models.bank_journal_config import BankJournalConfig
        
        config = BankJournalConfig(
            journal_id=journal_id,
            **config_data.model_dump()
        )
        
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        # Recargar el diario con la configuración
        journal_with_config = await self._get_journal_with_bank_config(journal_id)
        return journal_with_config

    async def get_bank_config(self, journal_id: uuid.UUID) -> Optional["BankJournalConfigRead"]:
        """
        Obtener configuración bancaria de un diario
        """
        from app.models.bank_journal_config import BankJournalConfig
        from app.schemas.journal import BankJournalConfigRead
        
        stmt = (
            select(BankJournalConfig)
            .options(
                selectinload(BankJournalConfig.bank_account),
                selectinload(BankJournalConfig.transit_account),
                selectinload(BankJournalConfig.profit_account),
                selectinload(BankJournalConfig.loss_account),
                selectinload(BankJournalConfig.inbound_receipt_account),
                selectinload(BankJournalConfig.outbound_pending_account)
            )
            .filter(BankJournalConfig.journal_id == journal_id)
        )
        
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if config:
            # Convertir manualmente los datos para evitar problemas de UUID
            config_data = {
                'journal_id': str(config.journal_id),
                'bank_account_number': config.bank_account_number,
                'bank_account_id': str(config.bank_account_id) if config.bank_account_id else None,
                'transit_account_id': str(config.transit_account_id) if config.transit_account_id else None,
                'profit_account_id': str(config.profit_account_id) if config.profit_account_id else None,
                'loss_account_id': str(config.loss_account_id) if config.loss_account_id else None,
                'dedicated_payment_sequence': config.dedicated_payment_sequence,
                'allow_inbound_payments': config.allow_inbound_payments,
                'inbound_payment_mode': config.inbound_payment_mode,
                'inbound_receipt_account_id': str(config.inbound_receipt_account_id) if config.inbound_receipt_account_id else None,
                'allow_outbound_payments': config.allow_outbound_payments,
                'outbound_payment_mode': config.outbound_payment_mode,
                'outbound_payment_method': config.outbound_payment_method,
                'outbound_payment_name': config.outbound_payment_name,
                'outbound_pending_account_id': str(config.outbound_pending_account_id) if config.outbound_pending_account_id else None,
                'currency_code': config.currency_code,
                'allow_currency_exchange': config.allow_currency_exchange,
                'auto_reconcile': config.auto_reconcile,
                'description': config.description,
                # Convertir cuentas relacionadas
                'bank_account': AccountRead(
                    id=str(config.bank_account.id),
                    code=config.bank_account.code,
                    name=config.bank_account.name,
                    account_type=config.bank_account.account_type
                ) if config.bank_account else None,
                'transit_account': AccountRead(
                    id=str(config.transit_account.id),
                    code=config.transit_account.code,
                    name=config.transit_account.name,
                    account_type=config.transit_account.account_type
                ) if config.transit_account else None,
                'profit_account': AccountRead(
                    id=str(config.profit_account.id),
                    code=config.profit_account.code,
                    name=config.profit_account.name,
                    account_type=config.profit_account.account_type
                ) if config.profit_account else None,
                'loss_account': AccountRead(
                    id=str(config.loss_account.id),
                    code=config.loss_account.code,
                    name=config.loss_account.name,
                    account_type=config.loss_account.account_type
                ) if config.loss_account else None,
                'inbound_receipt_account': AccountRead(
                    id=str(config.inbound_receipt_account.id),
                    code=config.inbound_receipt_account.code,
                    name=config.inbound_receipt_account.name,
                    account_type=config.inbound_receipt_account.account_type
                ) if config.inbound_receipt_account else None,
                'outbound_pending_account': AccountRead(
                    id=str(config.outbound_pending_account.id),
                    code=config.outbound_pending_account.code,
                    name=config.outbound_pending_account.name,
                    account_type=config.outbound_pending_account.account_type
                ) if config.outbound_pending_account else None,
            }
            
            return BankJournalConfigRead(**config_data)
        return None

    async def update_bank_config(
        self, 
        journal_id: uuid.UUID, 
        config_data: "BankJournalConfigUpdate"
    ) -> Optional["BankJournalConfigRead"]:
        """
        Actualizar configuración bancaria de un diario
        """
        from app.models.bank_journal_config import BankJournalConfig
        from app.schemas.journal import BankJournalConfigRead
        
        # Verificar que existe la configuración
        stmt = select(BankJournalConfig).filter(BankJournalConfig.journal_id == journal_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            raise JournalNotFoundError(str(journal_id))
        
        # Actualizar campos modificados
        update_data = config_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return await self.get_bank_config(journal_id)

    async def delete_bank_config(self, journal_id: uuid.UUID) -> None:
        """
        Eliminar configuración bancaria de un diario
        """
        from app.models.bank_journal_config import BankJournalConfig
        
        stmt = select(BankJournalConfig).filter(BankJournalConfig.journal_id == journal_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            raise JournalNotFoundError(str(journal_id))
        
        await self.db.delete(config)
        await self.db.commit()

    async def validate_bank_config(self, journal_id: uuid.UUID) -> "BankJournalConfigValidation":
        """
        Validar configuración bancaria de un diario
        """
        from app.schemas.journal import BankJournalConfigValidation
        
        journal = await self.get_journal_by_id(journal_id)
        if not journal:
            raise JournalNotFoundError(str(journal_id))
        
        if not journal.is_bank_journal():
            return BankJournalConfigValidation(
                is_valid=False,
                errors=["Este diario no es de tipo bancario"],
                warnings=[]
            )
        
        config = journal.get_bank_config()
        if not config:
            return BankJournalConfigValidation(
                is_valid=False,
                errors=["El diario bancario no tiene configuración"],
                warnings=[]
            )
        
        errors = config.validate_configuration()
        warnings = []
        
        # Agregar warnings adicionales si es necesario
        if config.allow_currency_exchange and config.currency_code == "COP":
            warnings.append("El intercambio de monedas está habilitado con moneda base COP")
        
        return BankJournalConfigValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def _get_journal_with_bank_config(self, journal_id: uuid.UUID) -> "JournalWithBankConfig":
        """
        Obtener diario con configuración bancaria cargada
        """
        from app.schemas.journal import JournalWithBankConfig
        
        stmt = (
            select(Journal)
            .options(selectinload(Journal.bank_config))
            .filter(Journal.id == journal_id)
        )
        
        result = await self.db.execute(stmt)
        journal = result.scalar_one_or_none()
        
        if not journal:
            raise JournalNotFoundError(str(journal_id))
        
        return JournalWithBankConfig.model_validate(journal, from_attributes=True)
