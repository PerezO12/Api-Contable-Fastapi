import uuid
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_, or_, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus, JournalEntryType, TransactionOrigin
from app.models.account import Account
from app.models.payment_terms import PaymentTerms
from app.models.product import Product, ProductStatus, ProductType
from app.schemas.journal_entry import (
    JournalEntryCreate, 
    JournalEntryUpdate, 
    JournalEntryRead, 
    JournalEntryLineCreate,
    JournalEntryFilter,
    JournalEntryStatistics, 
    JournalEntrySummary,
    JournalEntryPost,JournalEntryCancel, 
    BulkJournalEntryDelete, 
    BulkJournalEntryDeleteResult, 
    JournalEntryDeleteValidation, 
    JournalEntryResetToDraft, 
    JournalEntryResetToDraftValidation,
    BulkJournalEntryResetToDraft, 
    BulkJournalEntryResetToDraftResult,
    BulkJournalEntryApprove, 
    JournalEntryApproveValidation, 
    BulkJournalEntryApproveResult,
    BulkJournalEntryPost, 
    JournalEntryPostValidation, 
    BulkJournalEntryPostResult,
    BulkJournalEntryCancel, 
    JournalEntryCancelValidation, 
    BulkJournalEntryCancelResult,
    BulkJournalEntryReverse, 
    JournalEntryReverseValidation, 
    BulkJournalEntryReverseResult
)
from app.utils.exceptions import JournalEntryError, AccountNotFoundError, BalanceError
from app.utils.description_generator import JournalEntryDescriptionGenerator


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
        
        # Validación de productos en batch para optimizar rendimiento
        product_ids = [line.product_id for line in entry_data.lines if line.product_id]
        products_dict = {}
        if product_ids:
            products_result = await self.db.execute(
                select(Product).where(Product.id.in_(product_ids))
            )
            products_dict = {product.id: product for product in products_result.scalars().all()}
            
            # Validar que todos los productos existen
            missing_products = set(product_ids) - set(products_dict.keys())
            if missing_products:
                raise JournalEntryError(f"Productos no encontrados: {list(missing_products)}")
            
            # Validar que todos los productos están activos
            inactive_products = [
                f"{product.code} - {product.name}" 
                for product in products_dict.values() 
                if product.status != ProductStatus.ACTIVE
            ]
            if inactive_products:
                raise JournalEntryError(f"Los siguientes productos no están activos: {', '.join(inactive_products)}")
        
        # Validación de payment terms en batch para optimizar rendimiento
        payment_terms_ids = [getattr(line, 'payment_terms_id', None) for line in entry_data.lines if getattr(line, 'payment_terms_id', None)]
        payment_terms_dict = {}
        if payment_terms_ids:
            payment_terms_result = await self.db.execute(
                select(PaymentTerms)
                .options(selectinload(PaymentTerms.payment_schedules))
                .where(PaymentTerms.id.in_(payment_terms_ids))
            )
            payment_terms_dict = {pt.id: pt for pt in payment_terms_result.scalars().all()}
            
            # Validar que todas las condiciones de pago existen
            missing_payment_terms = set(payment_terms_ids) - set(payment_terms_dict.keys())
            if missing_payment_terms:
                raise JournalEntryError(f"Condiciones de pago no encontradas: {list(missing_payment_terms)}")
            
            # Validar que todas las condiciones de pago están activas
            inactive_payment_terms = [
                f"{pt.code} - {pt.name}" 
                for pt in payment_terms_dict.values() 
                if not pt.is_active
            ]
            if inactive_payment_terms:
                raise JournalEntryError(f"Las siguientes condiciones de pago no están activas: {', '.join(inactive_payment_terms)}")
        
        # Validaciones de coherencia de negocio para transaction_origin
        if entry_data.transaction_origin:
            # Si hay productos, validar coherencia entre transaction_origin y tipo de asiento
            if product_ids:
                sales_origins = [TransactionOrigin.SALE, TransactionOrigin.COLLECTION]
                purchase_origins = [TransactionOrigin.PURCHASE, TransactionOrigin.PAYMENT]
                
                if entry_data.transaction_origin in sales_origins:
                    # Para ventas, verificar que hay al menos una línea de ingreso
                    has_revenue_line = any(line.credit_amount > 0 for line in entry_data.lines)
                    if not has_revenue_line:
                        raise JournalEntryError("Los asientos de ventas deben incluir al menos una línea de crédito (ingreso)")
                
                elif entry_data.transaction_origin in purchase_origins:
                    # Para compras, verificar que hay al menos una línea de gasto o activo
                    has_expense_line = any(line.debit_amount > 0 for line in entry_data.lines)
                    if not has_expense_line:
                        raise JournalEntryError("Los asientos de compras deben incluir al menos una línea de débito (gasto o activo)")
        
        # Generar número de asiento
        entry_number = await self.generate_entry_number(entry_data.entry_type)
        
        # Generar descripción automática si no se proporciona
        entry_description = entry_data.description
        if not entry_description:
            entry_description = JournalEntryDescriptionGenerator.generate_entry_description(
                entry_type=entry_data.entry_type,
                transaction_origin=entry_data.transaction_origin,
                entry_date=entry_data.entry_date,
                reference=entry_data.reference,
                lines_data=entry_data.lines
            )
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
            
            # Validaciones específicas de productos
            if line_data.product_id:
                product = products_dict.get(line_data.product_id)
                if not product:
                    raise JournalEntryError(f"Producto no encontrado en línea {line_number}")
                
                # Validar cantidad para productos físicos
                if product.product_type in [ProductType.PRODUCT, ProductType.BOTH]:
                    if not line_data.quantity or line_data.quantity <= 0:
                        raise JournalEntryError(f"La cantidad debe ser mayor a 0 para productos físicos en línea {line_number}")
                
                # Validar coherencia de precios si se proporcionan
                if line_data.unit_price and line_data.quantity:
                    calculated_total = line_data.unit_price * line_data.quantity
                    # Aplicar descuentos si existen
                    if line_data.discount_amount:
                        calculated_total -= line_data.discount_amount
                    elif line_data.discount_percentage:
                        calculated_total *= (1 - line_data.discount_percentage / 100)
                    
                    # Verificar coherencia con el monto de la línea (con tolerancia para redondeo)
                    line_amount = line_data.debit_amount or line_data.credit_amount
                    if abs(calculated_total - line_amount) > Decimal('0.01'):
                        raise JournalEntryError(
                            f"El monto calculado ({calculated_total}) no coincide con el monto de la línea ({line_amount}) en línea {line_number}"
                        )
            
            # Obtener payment_terms_id y validar lógica de fechas
            payment_terms_id = getattr(line_data, 'payment_terms_id', None)
            due_date = getattr(line_data, 'due_date', None)
            invoice_date = getattr(line_data, 'invoice_date', None)
            
            # Generar descripción automática si no se proporciona
            line_description = line_data.description
            if not line_description:
                # Obtener información adicional para la descripción
                account = accounts_dict.get(line_data.account_id)
                product = products_dict.get(line_data.product_id) if line_data.product_id else None
                payment_terms = payment_terms_dict.get(payment_terms_id) if payment_terms_id else None
                
                line_description = JournalEntryDescriptionGenerator.generate_line_description(
                    account_name=account.name if account else None,
                    account_code=account.code if account else None,
                    third_party_name=None,  # Se cargará más tarde desde la relación
                    product_name=product.name if product else None,
                    cost_center_name=None,  # Se cargará más tarde desde la relación
                    debit_amount=line_data.debit_amount,
                    credit_amount=line_data.credit_amount,
                    transaction_origin=entry_data.transaction_origin,
                    payment_terms_name=payment_terms.name if payment_terms else None,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    quantity=line_data.quantity,
                    unit_price=line_data.unit_price
                )
            
            journal_line = JournalEntryLine(
                account_id=line_data.account_id,
                debit_amount=line_data.debit_amount,
                credit_amount=line_data.credit_amount,
                description=line_description,
                reference=line_data.reference,
                third_party_id=line_data.third_party_id,
                cost_center_id=line_data.cost_center_id,
                invoice_date=invoice_date,
                due_date=due_date,
                payment_terms_id=payment_terms_id,
                line_number=line_number,
                # Nuevos campos de producto
                product_id=line_data.product_id,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_percentage=line_data.discount_percentage,
                discount_amount=line_data.discount_amount,
                tax_percentage=line_data.tax_percentage,
                tax_amount=line_data.tax_amount
            )
            
            # Si hay payment_terms_id pero no due_date, calcular automáticamente la fecha de vencimiento
            if payment_terms_id and not due_date:
                payment_terms = payment_terms_dict.get(payment_terms_id)
                if payment_terms and payment_terms.payment_schedules:
                    # Usar la fecha de la línea o la del asiento como base
                    base_date = invoice_date if invoice_date else entry_data.entry_date
                    if isinstance(base_date, datetime):
                        base_date = base_date.date()
                    
                    # Obtener el último pago (mayor número de días)
                    last_schedule = max(payment_terms.payment_schedules, key=lambda x: x.days)
                    
                    # Calcular la fecha de vencimiento
                    base_datetime = datetime.combine(base_date, datetime.min.time())
                    due_datetime = last_schedule.calculate_payment_date(base_datetime)
                    
                    # Establecer la fecha de vencimiento calculada
                    journal_line.due_date = due_datetime.date()
            
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
            description=entry_description,
            entry_type=entry_data.entry_type,
            entry_date=entry_data.entry_date,
            status=JournalEntryStatus.DRAFT,
            created_by_id=created_by_id,
            notes=entry_data.notes,
            total_debit=total_debit,
            total_credit=total_credit,
            transaction_origin=entry_data.transaction_origin
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
            .options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.third_party),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.cost_center),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.payment_terms).selectinload(PaymentTerms.payment_schedules),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.product)
            )
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
            selectinload(JournalEntry.lines).selectinload(JournalEntryLine.third_party),
            selectinload(JournalEntry.lines).selectinload(JournalEntryLine.cost_center),
            selectinload(JournalEntry.lines).selectinload(JournalEntryLine.payment_terms).selectinload(PaymentTerms.payment_schedules),
            selectinload(JournalEntry.lines).selectinload(JournalEntryLine.product),
            selectinload(JournalEntry.created_by),
            selectinload(JournalEntry.posted_by)
        )
        
        # Aplicar filtros
        conditions = []
        
        if filters:
            if filters.status:
                conditions.append(JournalEntry.status.in_(filters.status))
            
            if filters.entry_type:
                conditions.append(JournalEntry.entry_type.in_(filters.entry_type))
            
            if filters.start_date:
                conditions.append(JournalEntry.entry_date >= filters.start_date)
            
            if filters.end_date:
                conditions.append(JournalEntry.entry_date <= filters.end_date)
            
            if filters.search_text:
                search_filter = or_(
                    JournalEntry.number.ilike(f"%{filters.search_text}%"),
                    JournalEntry.description.ilike(f"%{filters.search_text}%"),
                    JournalEntry.reference.ilike(f"%{filters.search_text}%")
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
            
            if filters.transaction_origin:
                conditions.append(JournalEntry.transaction_origin.in_(filters.transaction_origin))
        
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
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.third_party),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.cost_center),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.payment_terms).selectinload(PaymentTerms.payment_schedules),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.product),
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
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.third_party),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.cost_center),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.payment_terms).selectinload(PaymentTerms.payment_schedules),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.product),
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
        """Actualizar un asiento contable con todos los campos incluyendo líneas"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            return None
        
        # Verificar que se puede modificar
        if journal_entry.status not in [JournalEntryStatus.DRAFT, JournalEntryStatus.PENDING]:
            raise JournalEntryError("El asiento no puede ser modificado en su estado actual")
        
        # Actualizar campos básicos
        update_data = entry_data.model_dump(exclude_unset=True, exclude={'lines'})
        for field, value in update_data.items():
            if hasattr(journal_entry, field):
                setattr(journal_entry, field, value)
        
        # Si se proporcionan líneas, reemplazar completamente las líneas existentes
        if entry_data.lines is not None:
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
            
            # Validación de productos en batch
            product_ids = [line.product_id for line in entry_data.lines if line.product_id]
            products_dict = {}
            if product_ids:
                products_result = await self.db.execute(
                    select(Product).where(Product.id.in_(product_ids))
                )
                products_dict = {product.id: product for product in products_result.scalars().all()}
                
                # Validar que todos los productos existen
                missing_products = set(product_ids) - set(products_dict.keys())
                if missing_products:
                    raise JournalEntryError(f"Productos no encontrados: {list(missing_products)}")
                
                # Validar que todos los productos están activos
                inactive_products = [
                    f"{product.code} - {product.name}" 
                    for product in products_dict.values() 
                    if product.status != ProductStatus.ACTIVE
                ]
                if inactive_products:
                    raise JournalEntryError(f"Los siguientes productos no están activos: {', '.join(inactive_products)}")
            
            # Validación de payment terms en batch
            payment_terms_ids = [getattr(line, 'payment_terms_id', None) for line in entry_data.lines if getattr(line, 'payment_terms_id', None)]
            payment_terms_dict = {}
            if payment_terms_ids:
                payment_terms_result = await self.db.execute(
                    select(PaymentTerms)
                    .options(selectinload(PaymentTerms.payment_schedules))
                    .where(PaymentTerms.id.in_(payment_terms_ids))
                )
                payment_terms_dict = {pt.id: pt for pt in payment_terms_result.scalars().all()}
                
                # Validar que todas las condiciones de pago existen
                missing_payment_terms = set(payment_terms_ids) - set(payment_terms_dict.keys())
                if missing_payment_terms:
                    raise JournalEntryError(f"Condiciones de pago no encontradas: {list(missing_payment_terms)}")
                
                # Validar que todas las condiciones de pago están activas
                inactive_payment_terms = [
                    f"{pt.code} - {pt.name}" 
                    for pt in payment_terms_dict.values() 
                    if not pt.is_active
                ]
                if inactive_payment_terms:
                    raise JournalEntryError(f"Las siguientes condiciones de pago no están activas: {', '.join(inactive_payment_terms)}")
            
            # Eliminar líneas existentes
            await self.db.execute(
                delete(JournalEntryLine).where(JournalEntryLine.journal_entry_id == entry_id)
            )
            
            # Crear nuevas líneas
            journal_lines = []
            total_debit = Decimal('0')
            total_credit = Decimal('0')
            
            for line_number, line_data in enumerate(entry_data.lines, 1):
                # Validaciones de línea (mismas que en create)
                if line_data.debit_amount < 0 or line_data.credit_amount < 0:
                    raise JournalEntryError(f"Los montos no pueden ser negativos en línea {line_number}")
                
                if (line_data.debit_amount > 0 and line_data.credit_amount > 0) or \
                   (line_data.debit_amount == 0 and line_data.credit_amount == 0):
                    raise JournalEntryError(f"Línea {line_number}: debe tener monto en débito O crédito, no ambos o ninguno")
                
                # Validaciones específicas de productos
                if line_data.product_id:
                    product = products_dict.get(line_data.product_id)
                    if not product:
                        raise JournalEntryError(f"Producto no encontrado en línea {line_number}")
                    
                    # Validar cantidad para productos físicos
                    if product.product_type in [ProductType.PRODUCT, ProductType.BOTH]:
                        if not line_data.quantity or line_data.quantity <= 0:
                            raise JournalEntryError(f"La cantidad debe ser mayor a 0 para productos físicos en línea {line_number}")
                    
                    # Validar coherencia de precios si se proporcionan
                    if line_data.unit_price and line_data.quantity:
                        calculated_total = line_data.unit_price * line_data.quantity
                        # Aplicar descuentos si existen
                        if line_data.discount_amount:
                            calculated_total -= line_data.discount_amount
                        elif line_data.discount_percentage:
                            calculated_total *= (1 - line_data.discount_percentage / 100)
                        
                        # Verificar coherencia con el monto de la línea (con tolerancia para redondeo)
                        line_amount = line_data.debit_amount or line_data.credit_amount
                        if abs(calculated_total - line_amount) > Decimal('0.01'):
                            raise JournalEntryError(
                                f"El monto calculado ({calculated_total}) no coincide con el monto de la línea ({line_amount}) en línea {line_number}"
                            )
                
                # Obtener payment_terms_id y validar lógica de fechas
                payment_terms_id = getattr(line_data, 'payment_terms_id', None)
                due_date = getattr(line_data, 'due_date', None)
                invoice_date = getattr(line_data, 'invoice_date', None)
                
                # Generar descripción automática si no se proporciona
                line_description = line_data.description
                if not line_description:
                    # Obtener información adicional para la descripción
                    account = accounts_dict.get(line_data.account_id)
                    product = products_dict.get(line_data.product_id) if line_data.product_id else None
                    payment_terms = payment_terms_dict.get(payment_terms_id) if payment_terms_id else None
                    
                    line_description = JournalEntryDescriptionGenerator.generate_line_description(
                        account_name=account.name if account else None,
                        account_code=account.code if account else None,
                        third_party_name=None,  # Se cargará más tarde desde la relación
                        product_name=product.name if product else None,
                        cost_center_name=None,  # Se cargará más tarde desde la relación
                        debit_amount=line_data.debit_amount,
                        credit_amount=line_data.credit_amount,
                        transaction_origin=journal_entry.transaction_origin or entry_data.transaction_origin,
                        payment_terms_name=payment_terms.name if payment_terms else None,
                        invoice_date=invoice_date,
                        due_date=due_date,
                        quantity=line_data.quantity,
                        unit_price=line_data.unit_price
                    )
                
                journal_line = JournalEntryLine(
                    journal_entry_id=entry_id,
                    account_id=line_data.account_id,
                    debit_amount=line_data.debit_amount,
                    credit_amount=line_data.credit_amount,
                    description=line_description,
                    reference=line_data.reference,
                    third_party_id=line_data.third_party_id,
                    cost_center_id=line_data.cost_center_id,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    payment_terms_id=payment_terms_id,
                    line_number=line_number,
                    # Campos de producto
                    product_id=line_data.product_id,
                    quantity=line_data.quantity,
                    unit_price=line_data.unit_price,
                    discount_percentage=line_data.discount_percentage,
                    discount_amount=line_data.discount_amount,
                    tax_percentage=line_data.tax_percentage,
                    tax_amount=line_data.tax_amount
                )
                
                journal_lines.append(journal_line)
                total_debit += line_data.debit_amount
                total_credit += line_data.credit_amount
            
            # Actualizar totales en el journal entry
            journal_entry.total_debit = total_debit
            journal_entry.total_credit = total_credit
            
            # Agregar las líneas a la base de datos
            self.db.add_all(journal_lines)
            
            # Regenerar descripción automática si no se proporciona y hay líneas nuevas
            if not entry_data.description and not journal_entry.description:
                journal_entry.description = JournalEntryDescriptionGenerator.generate_entry_description(
                    entry_type=journal_entry.entry_type,
                    transaction_origin=journal_entry.transaction_origin,
                    entry_date=journal_entry.entry_date,
                    reference=journal_entry.reference,
                    lines_data=entry_data.lines
                )
        
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
        
        # Validar el asiento antes de aprobar (versión asíncrona para evitar lazy loading)
        # Ensure lines are loaded to avoid lazy loading issues
        _ = len(journal_entry.lines)  # Force load the relationship
        
        # Force load account relationships in lines to avoid lazy loading during validation
        for line in journal_entry.lines:
            if line.account:
                _ = line.account.code  # Force load account properties
                _ = line.account.name
                _ = line.account.can_receive_movements
                _ = line.account.requires_third_party
                _ = line.account.requires_cost_center
        
        errors = []
        
        # Validar que tenga al menos 2 líneas
        if len(journal_entry.lines) < 2:
            errors.append("El asiento debe tener al menos 2 líneas")
        
        # Validar balance (manual check to avoid properties in async context)
        if journal_entry.total_debit != journal_entry.total_credit:
            errors.append(f"El asiento no está balanceado. Débitos: {journal_entry.total_debit}, Créditos: {journal_entry.total_credit}")
        
        # Validar líneas individuales
        for i, line in enumerate(journal_entry.lines, 1):
            line_errors = line.validate_line()
            for error in line_errors:
                errors.append(f"Línea {i}: {error}")
        
        # Validar que no todas las líneas sean cero
        total_amount = Decimal(str(sum(line.debit_amount + line.credit_amount for line in journal_entry.lines)))
        if total_amount == 0:
            errors.append("El asiento no puede tener todas las líneas en cero")
        
        if errors:
            raise JournalEntryError(f"El asiento no puede ser aprobado: {'; '.join(errors)}")
        
        # Aprobar usando lógica asíncrona directa
        journal_entry.status = JournalEntryStatus.APPROVED
        journal_entry.approved_by_id = approved_by_id
        journal_entry.approved_at = datetime.now(timezone.utc)
        
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
        
        # Ensure lines are loaded to avoid lazy loading issues
        _ = len(journal_entry.lines)  # Force load the relationship
        
        # Force load account relationships in lines to avoid lazy loading during validation
        for line in journal_entry.lines:
            if line.account:
                _ = line.account.code  # Force load account properties
                _ = line.account.name
                _ = line.account.can_receive_movements
                _ = line.account.requires_third_party
                _ = line.account.requires_cost_center
        
        # Verificar si puede ser contabilizado (reemplazando can_be_posted para evitar lazy loading)
        if journal_entry.status != JournalEntryStatus.APPROVED:
            raise JournalEntryError("Solo se pueden contabilizar asientos aprobados")
        
        # Verificar balance (manual check to avoid properties in async context)
        if journal_entry.total_debit != journal_entry.total_credit:
            raise JournalEntryError("El asiento no está balanceado")
            
        if len(journal_entry.lines) < 2:
            raise JournalEntryError("El asiento debe tener al menos 2 líneas")
        
        # Verificar que todas las líneas sean válidas
        for line in journal_entry.lines:
            line_errors = line.validate_line()
            if line_errors:
                raise JournalEntryError(f"Línea inválida: {'; '.join(line_errors)}")
        
        # Validaciones específicas de productos antes de contabilizar
        for line in journal_entry.lines:
            if line.product_id:
                # Force load product if not already loaded
                if not line.product:
                    product_result = await self.db.execute(
                        select(Product).where(Product.id == line.product_id)
                    )
                    product = product_result.scalar_one_or_none()
                    if not product:
                        raise JournalEntryError(f"Producto no encontrado para línea {line.line_number}")
                    line.product = product
                
                # Verificar que el producto sigue activo
                if line.product.status != ProductStatus.ACTIVE:
                    raise JournalEntryError(f"El producto {line.product.code} - {line.product.name} no está activo")
                
                # Validar stock disponible para productos de inventario (solo para ventas/salidas)
                if (line.product.product_type in [ProductType.PRODUCT, ProductType.BOTH] and 
                    journal_entry.transaction_origin == TransactionOrigin.SALE and
                    line.quantity and line.quantity > 0):
                    
                    if line.product.manage_inventory and line.product.current_stock is not None:
                        if line.product.current_stock < line.quantity:
                            raise JournalEntryError(
                                f"Stock insuficiente para producto {line.product.code}. "
                                f"Stock actual: {line.product.current_stock}, Cantidad requerida: {line.quantity}"
                            )
        
        # Contabilizar usando lógica asíncrona directa
        journal_entry.status = JournalEntryStatus.POSTED
        journal_entry.posted_by_id = posted_by_id
        journal_entry.posted_at = datetime.now(timezone.utc)
        
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
            # Ensure lines are loaded to avoid lazy loading issues
            _ = len(journal_entry.lines)  # Force load the relationship
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
        
        # Flush to ensure lines are persisted before validation
        await self.db.flush()
        await self.db.refresh(reversal_entry)
        
        # Aprobar y contabilizar automáticamente usando lógica asíncrona
        # En lugar de usar los métodos síncronos del modelo, actualizamos directamente
        reversal_entry.status = JournalEntryStatus.APPROVED
        reversal_entry.approved_by_id = created_by_id
        reversal_entry.approved_at = datetime.now(timezone.utc)
        
        # Contabilizar directamente
        reversal_entry.status = JournalEntryStatus.POSTED
        reversal_entry.posted_by_id = created_by_id
        reversal_entry.posted_at = datetime.now(timezone.utc)
        
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

    async def validate_journal_entry_for_deletion(self, entry_id: uuid.UUID) -> JournalEntryDeleteValidation:
        """Validar si un asiento puede ser eliminado"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            return JournalEntryDeleteValidation(
                journal_entry_id=entry_id,
                journal_entry_number="N/A",
                journal_entry_description="N/A",
                status=JournalEntryStatus.DRAFT,
                can_delete=False,
                errors=["Asiento no encontrado"]
            )
        
        errors = []
        warnings = []
        can_delete = True
        
        # Solo se pueden eliminar asientos en estado DRAFT
        if journal_entry.status != JournalEntryStatus.DRAFT:
            errors.append(f"Solo se pueden eliminar asientos en estado borrador. Estado actual: {journal_entry.status}")
            can_delete = False
        
        # Verificar si el asiento tiene referencias o dependencias (si aplica en el futuro)
        # Por ejemplo, si está referenciado en reportes o tiene documentos adjuntos
        
        # Advertencias adicionales
        if journal_entry.entry_type == JournalEntryType.OPENING:
            warnings.append("Eliminar asientos de apertura puede afectar los saldos iniciales")
        
        if journal_entry.entry_type == JournalEntryType.CLOSING:
            warnings.append("Eliminar asientos de cierre puede afectar el balance del período")
        
        # Verificar si tiene líneas con importes significativos
        total_amount = journal_entry.total_debit
        if total_amount > Decimal('10000'):  # Umbral configurable
            warnings.append(f"El asiento tiene un monto significativo: {total_amount}")
        
        return JournalEntryDeleteValidation(
            journal_entry_id=entry_id,
            journal_entry_number=journal_entry.number,
            journal_entry_description=journal_entry.description,
            status=journal_entry.status,
            can_delete=can_delete,
            errors=errors,
            warnings=warnings
        )    
    async def bulk_delete_journal_entries(
        self, 
        entry_ids: List[uuid.UUID],
        force_delete: bool = False,
        reason: Optional[str] = None
    ) -> BulkJournalEntryDeleteResult:        
        """Eliminar múltiples asientos contables en lote"""
        
        total_requested = len(entry_ids)
        deleted_entries = []
        failed_entries = []
        global_errors = []
        global_warnings = []
        
        try:
            # Validar cada asiento individualmente
            for entry_id in entry_ids:
                validation = await self.validate_journal_entry_for_deletion(entry_id)
                
                # Si puede ser eliminado o se fuerza la eliminación
                should_delete = validation.can_delete and (force_delete or not validation.warnings)
                
                # Si force_delete es true, permitir eliminar incluso con errores (excepto críticos)
                if not should_delete and force_delete and validation.errors:
                    critical_errors = [e for e in validation.errors if 
                                     "no encontrado" in e.lower()]
                    should_delete = len(critical_errors) == 0
                
                if should_delete:
                    try:
                        # Obtener el asiento para eliminarlo
                        journal_entry = await self.get_journal_entry_by_id(entry_id)
                        if journal_entry:
                            await self.db.delete(journal_entry)
                            deleted_entries.append(validation)
                            
                            # Log de auditoría
                            if reason:
                                global_warnings.append(f"Asiento {validation.journal_entry_number} eliminado: {reason}")
                        else:
                            validation.can_delete = False
                            validation.errors.append("Asiento no encontrado durante eliminación")
                            failed_entries.append(validation)
                    except Exception as e:
                        validation.can_delete = False
                        validation.errors.append(f"Error durante eliminación: {str(e)}")
                        failed_entries.append(validation)
                else:
                    failed_entries.append(validation)
            
            # Confirmar transacción si hay eliminaciones exitosas
            if deleted_entries:
                await self.db.commit()
            
            return BulkJournalEntryDeleteResult(
                total_requested=total_requested,
                total_deleted=len(deleted_entries),
                total_failed=len(failed_entries),
                deleted_entries=deleted_entries,
                failed_entries=failed_entries,
                errors=global_errors,
                warnings=global_warnings
            )            
        except Exception as e:
            await self.db.rollback()
            raise JournalEntryError(f"Error en eliminación masiva: {str(e)}")

    async def bulk_operation(
        self, 
        operation: str, 
        entry_ids: List[uuid.UUID],
        operation_data: Optional[dict] = None
    ) -> dict:
        """Operaciones masivas en asientos contables"""
        
        if operation == "delete":
            force_delete = operation_data.get("force_delete", False) if operation_data else False
            reason = operation_data.get("reason") if operation_data else None
            result = await self.bulk_delete_journal_entries(
                entry_ids=entry_ids,
                force_delete=force_delete,
                reason=reason
            )
            
            return {
                "operation": "delete",
                "result": result.model_dump()
            }
            
        elif operation == "approve":
            force_approve = operation_data.get("force_approve", False) if operation_data else False
            reason = operation_data.get("reason") if operation_data else None
            approved_by_id = operation_data.get("approved_by_id") if operation_data else None
            
            if not approved_by_id:
                raise JournalEntryError("Se requiere el ID del usuario que aprueba")
            
            approved_by_id = uuid.UUID(approved_by_id)
            
            result = await self.bulk_approve_journal_entries(
                entry_ids=entry_ids,
                approved_by_id=approved_by_id,
                force_approve=force_approve,
                reason=reason
            )
            
            return {
                "operation": "approve",
                "result": result.model_dump()
            }
        
        elif operation == "cancel":
            cancelled_count = 0
            failed_count = 0
            errors = []
            
            cancel_reason = operation_data.get("reason", "Cancelación masiva") if operation_data else "Cancelación masiva"
            cancelled_by_id = operation_data.get("cancelled_by_id") if operation_data else None
            
            if not cancelled_by_id:
                raise JournalEntryError("Se requiere el ID del usuario que cancela")
            
            cancelled_by_id = uuid.UUID(cancelled_by_id)
            
            for entry_id in entry_ids:
                try:
                    from app.schemas.journal_entry import JournalEntryCancel
                    cancel_data = JournalEntryCancel(reason=cancel_reason)
                    await self.cancel_journal_entry(entry_id, cancelled_by_id, cancel_data)
                    cancelled_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error cancelando {entry_id}: {str(e)}")
            
            return {
                "operation": "cancel",
                "cancelled_count": cancelled_count,
                "failed_count": failed_count,
                "errors": errors
            }
        
        elif operation == "reset_to_draft":
            force_reset = operation_data.get("force_reset", False) if operation_data else False
            reason = operation_data.get("reason", "Restablecimiento masivo a borrador") if operation_data else "Restablecimiento masivo a borrador"
            reset_by_id = operation_data.get("reset_by_id") if operation_data else None
            
            if not reset_by_id:
                raise JournalEntryError("Se requiere el ID del usuario que restablece")
            
            reset_by_id = uuid.UUID(reset_by_id)
            
            result = await self.bulk_reset_journal_entries_to_draft(
                entry_ids=entry_ids,
                reset_by_id=reset_by_id,
                force_reset=force_reset,
                reason=reason
            )
            
            return {
                "operation": "reset_to_draft",
                "result": result.model_dump()
            }
        
        else:
            raise JournalEntryError(f"Operación no soportada: {operation}")

    async def reset_journal_entry_to_draft(
        self, 
        entry_id: uuid.UUID, 
        reset_by_id: uuid.UUID,
        reset_data: JournalEntryResetToDraft
    ) -> JournalEntry:
        """Restablecer un asiento contable a borrador"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            raise JournalEntryError("Asiento no encontrado")
        
        # COMENTADO: Permitir restablecer cualquier transacción sin importar el estado
        # Manual check to avoid sync property in async context
        # if journal_entry.status not in [JournalEntryStatus.APPROVED, JournalEntryStatus.PENDING]:
        #     raise JournalEntryError(
        #         f"El asiento no puede ser restablecido a borrador desde el estado {journal_entry.status}. "
        #         f"Solo se pueden restablecer asientos aprobados o pendientes."
        #     )
        
        # COMENTADO: Validaciones adicionales de negocio
        # if journal_entry.status == JournalEntryStatus.POSTED:
        #     raise JournalEntryError("No se puede restablecer a borrador un asiento contabilizado")
        
        # if journal_entry.status == JournalEntryStatus.CANCELLED:
        #     raise JournalEntryError("No se puede restablecer a borrador un asiento cancelado")
        
        # Verificar permisos especiales si es necesario
        # Por ejemplo, si el asiento es de apertura o cierre
        if journal_entry.entry_type in [JournalEntryType.OPENING, JournalEntryType.CLOSING]:
            # Solo administradores pueden restablecer asientos especiales
            # Esta validación se podría hacer en el controlador según los permisos del usuario
            pass
        
        # Restablecer a borrador
        success = journal_entry.reset_to_draft(reset_by_id)
        if not success:
            raise JournalEntryError("No se pudo restablecer el asiento a borrador")
        
        # Agregar razón en las notas
        if reset_data.reason:
            if journal_entry.notes:
                journal_entry.notes += f"\\n\\nRazón del restablecimiento: {reset_data.reason}"
            else:
                journal_entry.notes = f"Restablecido a borrador. Razón: {reset_data.reason}"
        
        await self.db.commit()
        await self.db.refresh(journal_entry)
        
        return journal_entry

    async def _reset_journal_entry_to_draft_no_commit(
        self, 
        entry_id: uuid.UUID, 
        reset_by_id: uuid.UUID,
        reset_data: JournalEntryResetToDraft
    ) -> JournalEntry:
        """Restablecer un asiento contable a borrador sin hacer commit (para operaciones en lote)"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            raise JournalEntryError("Asiento no encontrado")
        
        # Manual check to avoid sync property in async context
        if journal_entry.status not in [JournalEntryStatus.APPROVED, JournalEntryStatus.PENDING]:
            raise JournalEntryError(
                f"El asiento no puede ser restablecido a borrador desde el estado {journal_entry.status}. "
                f"Solo se pueden restablecer asientos aprobados o pendientes."
            )
        
        # Validaciones adicionales de negocio
        if journal_entry.status == JournalEntryStatus.POSTED:
            raise JournalEntryError("No se puede restablecer a borrador un asiento contabilizado")
        
        if journal_entry.status == JournalEntryStatus.CANCELLED:
            raise JournalEntryError("No se puede restablecer a borrador un asiento cancelado")
        
        # Verificar permisos especiales si es necesario
        # Por ejemplo, si el asiento es de apertura o cierre
        if journal_entry.entry_type in [JournalEntryType.OPENING, JournalEntryType.CLOSING]:
            # Solo administradores pueden restablecer asientos especiales
            # Esta validación se podría hacer en el controlador según los permisos del usuario
            pass
        
        # Restablecer a borrador
        success = journal_entry.reset_to_draft(reset_by_id)
        if not success:
            raise JournalEntryError("No se pudo restablecer el asiento a borrador")
        
        # Agregar razón en las notas
        if reset_data.reason:
            if journal_entry.notes:
                journal_entry.notes += f"\\n\\nRazón del restablecimiento: {reset_data.reason}"
            else:
                journal_entry.notes = f"Restablecido a borrador. Razón: {reset_data.reason}"
        
        return journal_entry

    async def validate_journal_entry_for_reset_to_draft(
        self, 
        entry_id: uuid.UUID
    ) -> JournalEntryResetToDraftValidation:
        """Validar si un asiento puede ser restablecido a borrador"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            return JournalEntryResetToDraftValidation(
                journal_entry_id=entry_id,
                journal_entry_number="UNKNOWN",
                journal_entry_description="Asiento no encontrado",
                current_status=JournalEntryStatus.DRAFT,
                can_reset=False,
                errors=["Asiento no encontrado"]
            )
        
        # Manual validation to avoid calling property in async context
        can_reset = journal_entry.status in [JournalEntryStatus.APPROVED, JournalEntryStatus.PENDING]
        errors = []
        warnings = []
        
        # Validaciones específicas
        if journal_entry.status == JournalEntryStatus.DRAFT:
            errors.append("El asiento ya está en borrador")
        elif journal_entry.status == JournalEntryStatus.POSTED:
            errors.append("No se puede restablecer a borrador un asiento contabilizado")
        elif journal_entry.status == JournalEntryStatus.CANCELLED:
            errors.append("No se puede restablecer a borrador un asiento cancelado")
        elif journal_entry.status not in [JournalEntryStatus.APPROVED, JournalEntryStatus.PENDING]:
            errors.append(f"Estado actual '{journal_entry.status}' no permite restablecimiento")
        
        # Advertencias específicas
        if journal_entry.entry_type == JournalEntryType.OPENING:
            warnings.append("Asiento de apertura: requiere permisos especiales")
        
        if journal_entry.entry_type == JournalEntryType.CLOSING:
            warnings.append("Asiento de cierre: requiere permisos especiales")
        
        if journal_entry.entry_type == JournalEntryType.AUTOMATIC:
            warnings.append("Asiento automático: podría afectar procesos automáticos")
        
        # Verificar si el asiento fue aprobado recientemente
        if journal_entry.approved_at:
            time_since_approval = datetime.now(timezone.utc) - journal_entry.approved_at
            if time_since_approval.total_seconds() < 3600:  # Menos de 1 hora
                warnings.append("Asiento aprobado recientemente (menos de 1 hora)")
        
        # Verificar si tiene una referencia externa importante
        if journal_entry.external_reference:
            warnings.append("Asiento con referencia externa: verificar impacto")
        
        # Verificar montos significativos
        if journal_entry.total_debit > Decimal('50000'):  # Umbral configurable
            warnings.append(f"Asiento con monto significativo: {journal_entry.total_debit}")
        
        # Si hay errores, no se puede restablecer
        if errors:
            can_reset = False
        
        return JournalEntryResetToDraftValidation(
            journal_entry_id=entry_id,
            journal_entry_number=journal_entry.number,
            journal_entry_description=journal_entry.description,
            current_status=journal_entry.status,
            can_reset=can_reset,
            errors=errors,            
            warnings=warnings
        )

    async def bulk_reset_journal_entries_to_draft(
        self, 
        entry_ids: List[uuid.UUID],
        reset_by_id: uuid.UUID,
        force_reset: bool = False,
        reason: str = "Restablecimiento masivo"
    ) -> BulkJournalEntryResetToDraftResult:
        """Restablecer múltiples asientos contables a borrador en lote"""
        
        
        total_requested = len(entry_ids)
        reset_entries = []
        failed_entries = []
        global_errors = []
        global_warnings = []
        
        try:
            # Validar cada asiento individualmente
            for entry_id in entry_ids:                
                validation = await self.validate_journal_entry_for_reset_to_draft(entry_id)
                
                
                # Si puede ser restablecido (errores pueden ser ignorados con force_reset)
                should_reset = validation.can_reset
                if not should_reset and force_reset and validation.errors:
                    # Solo el error de "no encontrado" es realmente crítico
                    # Con force_reset se debe poder resetear incluso asientos contabilizados
                    critical_errors = [e for e in validation.errors if 
                                     "no encontrado" in e.lower()]
                    # Permitir forzar contabilizados, cancelados y otros estados
                    should_reset = len(critical_errors) == 0
                
                if should_reset:
                    try:
                        # Crear objeto de reset
                        reset_data = JournalEntryResetToDraft(reason=reason)
                        
                        # Elegir método según si es forzado o no
                        if force_reset and not validation.can_reset:
                            # Usar método forzado para casos especiales (como cancelados)
                            await self._reset_journal_entry_to_draft_forced(entry_id, reset_by_id, reset_data)
                            force_note = " (FORZADO)"
                        else:
                            # Usar método normal
                            await self._reset_journal_entry_to_draft_no_commit(entry_id, reset_by_id, reset_data)
                            force_note = ""
                        
                        reset_entries.append(validation)
                        
                        # Log de auditoría
                        global_warnings.append(f"Asiento {validation.journal_entry_number} restablecido a borrador{force_note}")
                        
                    except Exception as e:
                        validation.can_reset = False
                        validation.errors.append(f"Error durante restablecimiento: {str(e)}")
                        failed_entries.append(validation)
                else:
                    failed_entries.append(validation)
            
            # Hacer commit de todos los cambios si hay entradas exitosas
            if reset_entries:
                await self.db.commit()
            
            result = BulkJournalEntryResetToDraftResult(
                total_requested=total_requested,
                total_reset=len(reset_entries),
                total_failed=len(failed_entries),
                reset_entries=reset_entries,
                failed_entries=failed_entries,
                errors=global_errors,
                warnings=global_warnings
            )
            
            return result
            
        except Exception as e:
            await self.db.rollback()
            raise JournalEntryError(f"Error en restablecimiento masivo: {str(e)}")

    async def validate_journal_entry_for_approve(
        self, 
        entry_id: uuid.UUID
    ) -> JournalEntryApproveValidation:
        """Validar si un asiento puede ser aprobado"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            return JournalEntryApproveValidation(
                journal_entry_id=entry_id,
                journal_entry_number="UNKNOWN",
                journal_entry_description="Asiento no encontrado",
                current_status=JournalEntryStatus.DRAFT,
                can_approve=False,
                errors=["Asiento no encontrado"]
            )
        
        can_approve = journal_entry.status == JournalEntryStatus.DRAFT
        errors = []
        warnings = []
        
        # Validaciones específicas para aprobación
        if journal_entry.status == JournalEntryStatus.APPROVED:
            errors.append("El asiento ya está aprobado")
        elif journal_entry.status == JournalEntryStatus.POSTED:
            errors.append("El asiento ya está contabilizado")
        elif journal_entry.status == JournalEntryStatus.CANCELLED:
            errors.append("No se puede aprobar un asiento cancelado")
        elif journal_entry.status != JournalEntryStatus.DRAFT:
            errors.append(f"Estado actual '{journal_entry.status}' no permite aprobación")
        
        # Validaciones de integridad del asiento
        # Ensure lines are loaded to avoid lazy loading issues
        _ = len(journal_entry.lines)  # Force load the relationship
        
        # Force load account relationships in lines to avoid lazy loading during validation
        for line in journal_entry.lines:
            if line.account:
                _ = line.account.code  # Force load account properties
                _ = line.account.name
                _ = line.account.can_receive_movements
                _ = line.account.requires_third_party
                _ = line.account.requires_cost_center
        
        entry_errors = journal_entry.validate_entry()
        if entry_errors:
            errors.extend([f"Error de validación: {error}" for error in entry_errors])
            can_approve = False
        
        # Advertencias específicas
        if journal_entry.entry_type == JournalEntryType.OPENING:
            warnings.append("Asiento de apertura: verificar impacto en saldos iniciales")
        
        if journal_entry.entry_type == JournalEntryType.CLOSING:
            warnings.append("Asiento de cierre: verificar impacto en balance del período")
        
        if journal_entry.total_debit > Decimal('100000'):  # Umbral configurable
            warnings.append(f"Asiento con monto muy alto: {journal_entry.total_debit}")
        
        # Si hay errores, no se puede aprobar
        if errors:
            can_approve = False
        
        return JournalEntryApproveValidation(
            journal_entry_id=entry_id,
            journal_entry_number=journal_entry.number,
            journal_entry_description=journal_entry.description,
            current_status=journal_entry.status,
            can_approve=can_approve,
            errors=errors,
            warnings=warnings
        )

    async def bulk_approve_journal_entries(
        self, 
        entry_ids: List[uuid.UUID],
        approved_by_id: uuid.UUID,
        force_approve: bool = False,
        reason: Optional[str] = None
    ) -> BulkJournalEntryApproveResult:
        """Aprobar múltiples asientos contables en lote"""
        
        total_requested = len(entry_ids)
        approved_entries = []
        failed_entries = []
        global_errors = []
        global_warnings = []
        
        try:
            # Validar cada asiento individualmente
            for entry_id in entry_ids:
                validation = await self.validate_journal_entry_for_approve(entry_id)
                
                # Si puede ser aprobado o se fuerza la aprobación
                should_approve = validation.can_approve and (force_approve or not validation.warnings)
                
                # Si force_approve es true, permitir aprobar incluso con errores (excepto críticos)
                if not should_approve and force_approve and validation.errors:
                    critical_errors = [e for e in validation.errors if 
                                     "no encontrado" in e.lower()]
                    should_approve = len(critical_errors) == 0
                
                if should_approve:
                    try:
                        # Aprobar el asiento
                        await self.approve_journal_entry(entry_id, approved_by_id)
                        approved_entries.append(validation)
                        
                        # Log de auditoría
                        if reason:
                            global_warnings.append(f"Asiento {validation.journal_entry_number} aprobado: {reason}")
                        
                    except Exception as e:
                        validation.can_approve = False
                        validation.errors.append(f"Error durante aprobación: {str(e)}")
                        failed_entries.append(validation)
                else:
                    failed_entries.append(validation)
            
            return BulkJournalEntryApproveResult(
                total_requested=total_requested,
                total_approved=len(approved_entries),
                total_failed=len(failed_entries),
                approved_entries=approved_entries,
                failed_entries=failed_entries,
                errors=global_errors,
                warnings=global_warnings
            )
            
        except Exception as e:
            await self.db.rollback()
            raise JournalEntryError(f"Error en aprobación masiva: {str(e)}")

    async def validate_journal_entry_for_post(
        self, 
        entry_id: uuid.UUID
    ) -> JournalEntryPostValidation:
        """Validar si un asiento puede ser contabilizado"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            return JournalEntryPostValidation(
                journal_entry_id=entry_id,
                journal_entry_number="UNKNOWN",
                journal_entry_description="Asiento no encontrado",
                current_status=JournalEntryStatus.DRAFT,
                can_post=False,
                errors=["Asiento no encontrado"]
            )
        
        # Ensure lines are loaded to avoid lazy loading issues
        _ = len(journal_entry.lines)  # Force load the relationship
        
        # Manual validation to avoid calling can_be_posted property in async context
        can_post = (
            journal_entry.status == JournalEntryStatus.APPROVED and
            journal_entry.total_debit == journal_entry.total_credit and
            len(journal_entry.lines) >= 2
        )
        errors = []
        warnings = []
        
        # Validaciones específicas para contabilización
        if journal_entry.status == JournalEntryStatus.DRAFT:
            errors.append("El asiento debe estar aprobado antes de contabilizar")
        elif journal_entry.status == JournalEntryStatus.POSTED:
            errors.append("El asiento ya está contabilizado")
        elif journal_entry.status == JournalEntryStatus.CANCELLED:
            errors.append("No se puede contabilizar un asiento cancelado")
        elif journal_entry.status != JournalEntryStatus.APPROVED:
            errors.append(f"Estado actual '{journal_entry.status}' no permite contabilización")
        
        # Validaciones adicionales (manual check to avoid properties in async context)
        if journal_entry.total_debit != journal_entry.total_credit:
            errors.append("El asiento no está balanceado")
        
        if len(journal_entry.lines) < 2:
            errors.append("El asiento debe tener al menos 2 líneas")
        
        # Verificar que las cuentas permiten movimientos
        for line in journal_entry.lines:
            if not line.account.allows_movements:
                errors.append(f"La cuenta {line.account.code} - {line.account.name} no permite movimientos")
        
        # Advertencias específicas
        if journal_entry.entry_type == JournalEntryType.OPENING:
            warnings.append("Asiento de apertura: afectará saldos iniciales")
        
        if journal_entry.entry_type == JournalEntryType.CLOSING:
            warnings.append("Asiento de cierre: afectará balance del período")
        
        # Verificar periodo contable
        current_date = date.today()
        entry_date = journal_entry.entry_date.date() if isinstance(journal_entry.entry_date, datetime) else journal_entry.entry_date
        
        if entry_date > current_date:
            warnings.append("Fecha del asiento es futura")
        
        if (current_date - entry_date).days > 30:  # Más de 30 días
            warnings.append("Asiento con fecha antigua (más de 30 días)")
        
        # Si hay errores, no se puede contabilizar
        if errors:
            can_post = False
        
        return JournalEntryPostValidation(
            journal_entry_id=entry_id,
            journal_entry_number=journal_entry.number,
            journal_entry_description=journal_entry.description,
            current_status=journal_entry.status,
            can_post=can_post,
            errors=errors,
            warnings=warnings
        )

    async def bulk_post_journal_entries(
        self, 
        entry_ids: List[uuid.UUID],
        posted_by_id: uuid.UUID,
        force_post: bool = False,
        reason: Optional[str] = None
    ) -> BulkJournalEntryPostResult:
        """Contabilizar múltiples asientos contables en lote"""
        
        total_requested = len(entry_ids)
        posted_entries = []
        failed_entries = []
        global_errors = []
        global_warnings = []
        
        try:
            # Validar cada asiento individualmente
            for entry_id in entry_ids:
                validation = await self.validate_journal_entry_for_post(entry_id)
                
                # Si puede ser contabilizado o se fuerza la contabilización
                should_post = validation.can_post and (force_post or not validation.warnings)
                
                # Si force_post es true, permitir contabilizar incluso con errores (excepto críticos)
                if not should_post and force_post and validation.errors:
                    critical_errors = [e for e in validation.errors if 
                                     "no encontrado" in e.lower()]
                    should_post = len(critical_errors) == 0
                
                if should_post:
                    try:
                        # Crear objeto de post si hay razón
                        post_data = JournalEntryPost(reason=reason) if reason else None
                        
                        # Contabilizar el asiento
                        await self.post_journal_entry(entry_id, posted_by_id, post_data)
                        posted_entries.append(validation)
                        
                        # Log de auditoría
                        global_warnings.append(f"Asiento {validation.journal_entry_number} contabilizado")
                        
                    except Exception as e:
                        validation.can_post = False
                        validation.errors.append(f"Error durante contabilización: {str(e)}")
                        failed_entries.append(validation)
                else:
                    failed_entries.append(validation)
            
            return BulkJournalEntryPostResult(
                total_requested=total_requested,
                total_posted=len(posted_entries),
                total_failed=len(failed_entries),
                posted_entries=posted_entries,
                failed_entries=failed_entries,
                errors=global_errors,
                warnings=global_warnings
            )
            
        except Exception as e:
            await self.db.rollback()
            raise JournalEntryError(f"Error en contabilización masiva: {str(e)}")

    async def validate_journal_entry_for_cancel(
        self, 
        entry_id: uuid.UUID
    ) -> JournalEntryCancelValidation:
        """Validar si un asiento puede ser cancelado"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            return JournalEntryCancelValidation(
                journal_entry_id=entry_id,
                journal_entry_number="UNKNOWN",
                journal_entry_description="Asiento no encontrado",
                current_status=JournalEntryStatus.DRAFT,
                can_cancel=False,
                errors=["Asiento no encontrado"]
            )
        
        can_cancel = journal_entry.status != JournalEntryStatus.CANCELLED
        errors = []
        warnings = []
        
        # Validaciones específicas para cancelación
        if journal_entry.status == JournalEntryStatus.CANCELLED:
            errors.append("El asiento ya está cancelado")
            can_cancel = False
        
        # Advertencias para diferentes estados
        if journal_entry.status == JournalEntryStatus.POSTED:
            warnings.append("Asiento contabilizado: se creará asiento de reversión automáticamente")
        
        if journal_entry.entry_type == JournalEntryType.OPENING:
            warnings.append("Asiento de apertura: la cancelación afectará saldos iniciales")
        
        if journal_entry.entry_type == JournalEntryType.CLOSING:
            warnings.append("Asiento de cierre: la cancelación afectará balance del período")
        
        if journal_entry.entry_type == JournalEntryType.AUTOMATIC:
            warnings.append("Asiento automático: verificar impacto en procesos automáticos")
        
        # Verificar periodo contable para asientos contabilizados
        if journal_entry.status == JournalEntryStatus.POSTED and journal_entry.posted_at:
            days_since_posted = (datetime.now(timezone.utc) - journal_entry.posted_at).days
            if days_since_posted > 7:  # Más de 7 días contabilizado
                warnings.append(f"Asiento contabilizado hace {days_since_posted} días")
        
        return JournalEntryCancelValidation(
            journal_entry_id=entry_id,
            journal_entry_number=journal_entry.number,
            journal_entry_description=journal_entry.description,
            current_status=journal_entry.status,
            can_cancel=can_cancel,
            errors=errors,
            warnings=warnings
        )

    async def bulk_cancel_journal_entries(
        self, 
        entry_ids: List[uuid.UUID],
        cancelled_by_id: uuid.UUID,
        force_cancel: bool = False,
        reason: str = "Cancelación masiva"
    ) -> BulkJournalEntryCancelResult:
        """Cancelar múltiples asientos contables en lote"""
        
        total_requested = len(entry_ids)
        cancelled_entries = []
        failed_entries = []
        global_errors = []
        global_warnings = []
        
        try:
            # Validar cada asiento individualmente
            for entry_id in entry_ids:
                validation = await self.validate_journal_entry_for_cancel(entry_id)
                
                # Si puede ser cancelado o se fuerza la cancelación 
                should_cancel = validation.can_cancel and (force_cancel or not validation.warnings)
                
                # Si force_cancel es true, permitir cancelar incluso con errores (excepto críticos)
                if not should_cancel and force_cancel and validation.errors:
                    critical_errors = [e for e in validation.errors if 
                                     "no encontrado" in e.lower()]
                    should_cancel = len(critical_errors) == 0
                
                if should_cancel:
                    try:
                        # Crear objeto de cancelación
                        cancel_data = JournalEntryCancel(reason=reason)
                        
                        # Cancelar el asiento
                        await self.cancel_journal_entry(entry_id, cancelled_by_id, cancel_data)
                        cancelled_entries.append(validation)
                        
                        # Log de auditoría
                        global_warnings.append(f"Asiento {validation.journal_entry_number} cancelado")
                        
                    except Exception as e:
                        validation.can_cancel = False
                        validation.errors.append(f"Error durante cancelación: {str(e)}")
                        failed_entries.append(validation)
                else:
                    failed_entries.append(validation)
            
            return BulkJournalEntryCancelResult(
                total_requested=total_requested,
                total_cancelled=len(cancelled_entries),
                total_failed=len(failed_entries),
                cancelled_entries=cancelled_entries,
                failed_entries=failed_entries,
                errors=global_errors,
                warnings=global_warnings
            )
            
        except Exception as e:
            await self.db.rollback()
            raise JournalEntryError(f"Error en cancelación masiva: {str(e)}")

    async def validate_journal_entry_for_reverse(
        self, 
        entry_id: uuid.UUID
    ) -> JournalEntryReverseValidation:
        """Validar si un asiento puede ser revertido"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            return JournalEntryReverseValidation(
                journal_entry_id=entry_id,
                journal_entry_number="UNKNOWN",
                journal_entry_description="Asiento no encontrado",
                current_status=JournalEntryStatus.DRAFT,
                can_reverse=False,
                errors=["Asiento no encontrado"]
            )
        
        can_reverse = journal_entry.status == JournalEntryStatus.POSTED
        errors = []
        warnings = []
        
        # Validaciones específicas para reversión
        if journal_entry.status != JournalEntryStatus.POSTED:
            errors.append("Solo se pueden revertir asientos contabilizados")
            can_reverse = False
        
        if journal_entry.status == JournalEntryStatus.CANCELLED:
            errors.append("No se puede revertir un asiento cancelado")
            can_reverse = False
        
        if journal_entry.entry_type == JournalEntryType.REVERSAL:
            errors.append("No se puede revertir un asiento de reversión")
            can_reverse = False
        
        # Advertencias específicas
        if journal_entry.entry_type == JournalEntryType.OPENING:
            warnings.append("Asiento de apertura: la reversión afectará saldos iniciales")
        
        if journal_entry.entry_type == JournalEntryType.CLOSING:
            warnings.append("Asiento de cierre: la reversión afectará balance del período")
        
        # Verificar antigüedad del asiento
        if journal_entry.posted_at:
            days_since_posted = (datetime.now(timezone.utc) - journal_entry.posted_at).days
            if days_since_posted > 30:  # Más de 30 días
                warnings.append(f"Asiento contabilizado hace {days_since_posted} días")
        
        # Verificar si ya existe una reversión
        # Buscar asientos de reversión que referencien este asiento
        reversal_check = await self.db.execute(
            select(JournalEntry).where(
                and_(
                    JournalEntry.entry_type == JournalEntryType.REVERSAL,
                    JournalEntry.reference.like(f"REV-{journal_entry.number}")
                )
            )
        )
        existing_reversal = reversal_check.scalar_one_or_none()
        
        if existing_reversal:
            warnings.append(f"Ya existe una reversión: {existing_reversal.number}")
        
        return JournalEntryReverseValidation(
            journal_entry_id=entry_id,
            journal_entry_number=journal_entry.number,
            journal_entry_description=journal_entry.description,
            current_status=journal_entry.status,
            can_reverse=can_reverse,
            errors=errors,
            warnings=warnings
        )

    async def bulk_reverse_journal_entries(
        self, 
        entry_ids: List[uuid.UUID],
        created_by_id: uuid.UUID,
        force_reverse: bool = False,
        reason: str = "Reversión masiva"
    ) -> BulkJournalEntryReverseResult:
        """Revertir múltiples asientos contables en lote"""
        
        total_requested = len(entry_ids)
        reversed_entries = []
        failed_entries = []
        created_reversal_entries = []
        global_errors = []
        global_warnings = []
        
        try:
            # Validar cada asiento individualmente
            for entry_id in entry_ids:
                validation = await self.validate_journal_entry_for_reverse(entry_id)
                
                # Si puede ser revertido o se fuerza la reversión
                should_reverse = validation.can_reverse and (force_reverse or not validation.warnings)
                
                # Si force_reverse es true, permitir revertir incluso con errores (excepto críticos)
                if not should_reverse and force_reverse and validation.errors:
                    critical_errors = [e for e in validation.errors if 
                                     "no encontrado" in e.lower()]
                    should_reverse = len(critical_errors) == 0
                
                if should_reverse:
                    try:
                        # Obtener el asiento original
                        original_entry = await self.get_journal_entry_by_id(entry_id)
                        if original_entry:
                            # Ensure lines are loaded to avoid lazy loading issues
                            _ = len(original_entry.lines)  # Force load the relationship
                            # Crear asiento de reversión
                            reversal_entry = await self._create_reversal_entry(
                                original_entry, 
                                created_by_id, 
                                reason
                            )
                            
                            reversed_entries.append(validation)
                            created_reversal_entries.append(reversal_entry.number)
                            
                            # Log de auditoría
                            global_warnings.append(
                                f"Asiento {validation.journal_entry_number} revertido. "
                                f"Reversión: {reversal_entry.number}"
                            )
                        else:
                            validation.can_reverse = False
                            validation.errors.append("Asiento no encontrado durante reversión")
                            failed_entries.append(validation)
                        
                    except Exception as e:
                        validation.can_reverse = False
                        validation.errors.append(f"Error durante reversión: {str(e)}")
                        failed_entries.append(validation)
                else:
                    failed_entries.append(validation)
            
            return BulkJournalEntryReverseResult(
                total_requested=total_requested,
                total_reversed=len(reversed_entries),
                total_failed=len(failed_entries),
                reversed_entries=reversed_entries,
                failed_entries=failed_entries,
                created_reversal_entries=created_reversal_entries,
                errors=global_errors,
                warnings=global_warnings
            )
            
        except Exception as e:
            await self.db.rollback()
            raise JournalEntryError(f"Error en reversión masiva: {str(e)}")
    
    async def _reset_journal_entry_to_draft_forced(
        self, 
        entry_id: uuid.UUID, 
        reset_by_id: uuid.UUID,
        reset_data: JournalEntryResetToDraft
    ) -> JournalEntry:
        """Restablecer un asiento contable a borrador forzadamente, ignorando validaciones de negocio"""
        
        journal_entry = await self.get_journal_entry_by_id(entry_id)
        
        if not journal_entry:
            raise JournalEntryError("Asiento no encontrado")
        
        # Solo validaciones críticas que no se pueden forzar
        # Con force_reset, incluso los asientos POSTED se pueden resetear
        
        # Para forzado, permitir todos los estados excepto casos imposibles
        try:
            # Forzar el restablecimiento directamente en el modelo
            if journal_entry.status == JournalEntryStatus.POSTED:
                # NUEVO: Permitir resetear asientos contabilizados con force
                # Esto revierte el estado sin crear asientos de reversión
                journal_entry.status = JournalEntryStatus.DRAFT
                journal_entry.posted_by_id = None
                journal_entry.posted_at = None
                # Nota: En un entorno real, esto podría requerir auditoría adicional
            elif journal_entry.status == JournalEntryStatus.CANCELLED:
                # Restaurar manualmente desde cancelado
                journal_entry.status = JournalEntryStatus.DRAFT
                journal_entry.cancelled_by_id = None
                journal_entry.cancelled_at = None
            elif journal_entry.status in [JournalEntryStatus.APPROVED, JournalEntryStatus.PENDING]:
                # Usar el método normal del modelo
                success = journal_entry.reset_to_draft(reset_by_id)
                if not success:
                    raise JournalEntryError("No se pudo restablecer el asiento a borrador")
            elif journal_entry.status == JournalEntryStatus.DRAFT:
                # Ya está en borrador, no hacer nada
                pass
            else:
                raise JournalEntryError(f"Estado {journal_entry.status} no soportado para restablecimiento forzado")
            
            # Agregar razón en las notas con marca de forzado
            force_note = f"RESTABLECIMIENTO FORZADO - {reset_data.reason}"
            if journal_entry.notes:
                journal_entry.notes += f"\\n\\n{force_note}"
            else:
                journal_entry.notes = force_note
            
            return journal_entry
            
        except Exception as e:
            raise JournalEntryError(f"Error en restablecimiento forzado: {str(e)}")
