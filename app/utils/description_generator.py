"""
Utilidades para generar descripciones automáticas en journal entries
"""

from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any
from app.models.journal_entry import TransactionOrigin, JournalEntryType


class JournalEntryDescriptionGenerator:
    """Generador de descripciones automáticas para asientos contables"""
    
    @staticmethod
    def generate_entry_description(
        entry_type: JournalEntryType,
        transaction_origin: Optional[TransactionOrigin] = None,
        entry_date: Optional[date] = None,
        reference: Optional[str] = None,
        lines_data: Optional[list] = None
    ) -> str:
        """
        Genera una descripción automática para el asiento contable
        
        Args:
            entry_type: Tipo de asiento
            transaction_origin: Origen de la transacción
            entry_date: Fecha del asiento
            reference: Referencia externa
            lines_data: Datos de las líneas para contexto adicional
            
        Returns:
            str: Descripción generada automáticamente
        """
        
        # Diccionario de traducciones para tipos de asiento
        entry_type_translations = {
            JournalEntryType.MANUAL: "Asiento manual",
            JournalEntryType.AUTOMATIC: "Asiento automático", 
            JournalEntryType.ADJUSTMENT: "Asiento de ajuste",
            JournalEntryType.OPENING: "Asiento de apertura",
            JournalEntryType.CLOSING: "Asiento de cierre",
            JournalEntryType.REVERSAL: "Asiento de reversión"
        }
        
        # Diccionario de traducciones para orígenes de transacción
        origin_translations = {
            TransactionOrigin.SALE: "venta",
            TransactionOrigin.PURCHASE: "compra",
            TransactionOrigin.ADJUSTMENT: "ajuste",
            TransactionOrigin.TRANSFER: "transferencia",
            TransactionOrigin.PAYMENT: "pago",
            TransactionOrigin.COLLECTION: "cobro",
            TransactionOrigin.OPENING: "apertura",
            TransactionOrigin.CLOSING: "cierre",
            TransactionOrigin.OTHER: "operación"
        }
        
        # Construir descripción base
        if transaction_origin and transaction_origin in origin_translations:
            base_description = f"Registro de {origin_translations[transaction_origin]}"
        else:
            base_description = entry_type_translations.get(entry_type, "Asiento contable")
        
        # Agregar fecha si está disponible
        if entry_date:
            base_description += f" del {entry_date.strftime('%d/%m/%Y')}"
        
        # Agregar referencia si está disponible
        if reference:
            base_description += f" - Ref: {reference}"
        
        # Agregar contexto adicional basado en las líneas
        if lines_data:
            context = JournalEntryDescriptionGenerator._extract_context_from_lines(lines_data)
            if context:
                base_description += f" - {context}"
        
        return base_description[:1000]  # Limitar a 1000 caracteres
    
    @staticmethod
    def generate_line_description(
        account_name: Optional[str] = None,
        account_code: Optional[str] = None,
        third_party_name: Optional[str] = None,
        product_name: Optional[str] = None,
        cost_center_name: Optional[str] = None,
        debit_amount: Optional[Decimal] = None,
        credit_amount: Optional[Decimal] = None,
        transaction_origin: Optional[TransactionOrigin] = None,
        payment_terms_name: Optional[str] = None,
        invoice_date: Optional[date] = None,
        due_date: Optional[date] = None,
        quantity: Optional[Decimal] = None,
        unit_price: Optional[Decimal] = None
    ) -> str:
        """
        Genera una descripción automática para una línea de asiento
        
        Args:
            account_name: Nombre de la cuenta
            account_code: Código de la cuenta
            third_party_name: Nombre del tercero
            product_name: Nombre del producto
            cost_center_name: Nombre del centro de costo
            debit_amount: Monto débito
            credit_amount: Monto crédito
            transaction_origin: Origen de la transacción
            payment_terms_name: Nombre de las condiciones de pago
            invoice_date: Fecha de factura
            due_date: Fecha de vencimiento
            quantity: Cantidad del producto
            unit_price: Precio unitario
            
        Returns:
            str: Descripción generada automáticamente
        """
        
        parts = []
        
        # Determinar el tipo de movimiento
        is_debit = debit_amount and debit_amount > 0
        amount = debit_amount if is_debit else credit_amount
        
        # Agregar información del producto si está disponible
        if product_name:
            product_info = product_name
            if quantity and unit_price:
                product_info += f" ({quantity} x ${unit_price:,.2f})"
            elif quantity:
                product_info += f" (Cant: {quantity})"
            parts.append(product_info)
        
        # Agregar información del tercero
        if third_party_name:
            if transaction_origin == TransactionOrigin.SALE:
                parts.append(f"Cliente: {third_party_name}")
            elif transaction_origin == TransactionOrigin.PURCHASE:
                parts.append(f"Proveedor: {third_party_name}")
            else:
                parts.append(f"Tercero: {third_party_name}")
        
        # Agregar información de la cuenta si no hay contexto más específico
        if not parts and account_name:
            account_info = account_name
            if account_code:
                account_info = f"{account_code} - {account_name}"
            parts.append(account_info)
        
        # Agregar información del centro de costo
        if cost_center_name:
            parts.append(f"CC: {cost_center_name}")
        
        # Agregar información de condiciones de pago
        if payment_terms_name:
            parts.append(f"Términos: {payment_terms_name}")
        
        # Agregar información de fechas
        if invoice_date and due_date:
            parts.append(f"Factura: {invoice_date.strftime('%d/%m/%Y')}, Vence: {due_date.strftime('%d/%m/%Y')}")
        elif invoice_date:
            parts.append(f"Factura: {invoice_date.strftime('%d/%m/%Y')}")
        elif due_date:
            parts.append(f"Vence: {due_date.strftime('%d/%m/%Y')}")
        
        # Construir descripción final
        if parts:
            description = " - ".join(parts)
        else:
            # Descripción genérica basada en el tipo de movimiento
            movement_type = "Débito" if is_debit else "Crédito"
            description = f"{movement_type}"
            if amount:
                description += f" por ${amount:,.2f}"
        
        return description[:500]  # Limitar a 500 caracteres
    
    @staticmethod
    def _extract_context_from_lines(lines_data: list) -> Optional[str]:
        """
        Extrae contexto adicional de las líneas del asiento
        
        Args:
            lines_data: Lista de datos de líneas
            
        Returns:
            Optional[str]: Contexto extraído o None
        """
        
        contexts = []
        
        # Buscar terceros únicos
        third_parties = set()
        for line in lines_data:
            if hasattr(line, 'third_party_name') and line.third_party_name:
                third_parties.add(line.third_party_name)
            elif isinstance(line, dict) and line.get('third_party_name'):
                third_parties.add(line['third_party_name'])
        
        if third_parties:
            if len(third_parties) == 1:
                contexts.append(f"Tercero: {list(third_parties)[0]}")
            else:
                contexts.append(f"Múltiples terceros ({len(third_parties)})")
        
        # Buscar productos únicos
        products = set()
        for line in lines_data:
            if hasattr(line, 'product_name') and line.product_name:
                products.add(line.product_name)
            elif isinstance(line, dict) and line.get('product_name'):
                products.add(line['product_name'])
        
        if products:
            if len(products) == 1:
                contexts.append(f"Producto: {list(products)[0]}")
            else:
                contexts.append(f"Múltiples productos ({len(products)})")
        
        # Calcular monto total
        total_amount = Decimal('0')
        for line in lines_data:
            if hasattr(line, 'debit_amount') and line.debit_amount:
                total_amount += line.debit_amount
            elif isinstance(line, dict) and line.get('debit_amount'):
                total_amount += Decimal(str(line['debit_amount']))
        
        if total_amount > 0:
            contexts.append(f"Total: ${total_amount:,.2f}")
        
        return " - ".join(contexts) if contexts else None
