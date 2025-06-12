# Estados de Cuenta de Terceros

El sistema de estados de cuenta permite generar automáticamente reportes detallados de movimientos, saldos y transacciones para cada tercero. Estos estados se generan en tiempo real utilizando los datos de asientos contables y proporcionan información completa para el seguimiento de relaciones comerciales.

## Características de los Estados de Cuenta

### ✅ **Generación en Tiempo Real**
- Cálculo automático de saldos actuales
- Inclusión de movimientos más recientes
- Actualización instantánea tras nuevos asientos
- Sincronización con cambios en la contabilidad

### ✅ **Filtrado Avanzado**
- Por rango de fechas personalizable
- Por tipo de movimiento (débitos, créditos, todos)
- Por estado de asiento (contabilizado, pendiente, cancelado)
- Por cuentas contables específicas

### ✅ **Formato Profesional**
- Layout optimizado para envío a terceros
- Información comercial completa
- Totales y subtotales automáticos
- Desglose detallado de movimientos

### ✅ **Múltiples Formatos de Salida**
- PDF para envío formal
- Excel para análisis detallado
- JSON para integración con sistemas
- HTML para visualización web

## Estructura del Estado de Cuenta

### **Encabezado del Estado**
```python
class StatementHeader:
    # Información del tercero
    third_party_id: UUID
    third_party_name: str
    third_party_code: str
    document_type: str
    document_number: str
    
    # Información comercial
    contact_email: str
    contact_phone: str
    address: str
    city: str
    country: str
    
    # Parámetros del reporte
    statement_date: datetime
    period_start: date
    period_end: date
    generated_by: str
    generation_time: datetime
    
    # Resumen de saldos
    opening_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
    closing_balance: Decimal
    
    # Información adicional
    payment_terms: str
    credit_limit: Decimal
    overdue_amount: Decimal
    days_overdue: int
```

### **Detalle de Movimientos**
```python
class StatementLine:
    # Información del asiento
    journal_entry_id: UUID
    entry_number: str
    entry_date: date
    entry_description: str
    entry_reference: str
    
    # Información de la línea
    line_id: UUID
    account_code: str
    account_name: str
    line_description: str
    
    # Montos
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Decimal
    
    # Estado
    entry_status: str
    posting_date: Optional[date]
    due_date: Optional[date]
    
    # Información adicional
    cost_center_name: Optional[str]
    document_reference: Optional[str]
    notes: Optional[str]
```

### **Resumen y Totales**
```python
class StatementSummary:
    # Resumen del período
    total_movements: int
    total_debits: Decimal
    total_credits: Decimal
    net_movement: Decimal
    
    # Análisis de antigüedad
    current_balance: Decimal
    overdue_0_30: Decimal
    overdue_31_60: Decimal
    overdue_61_90: Decimal
    overdue_over_90: Decimal
    
    # Métricas adicionales
    average_transaction_size: Decimal
    largest_transaction: Decimal
    transaction_frequency: float
    payment_behavior_score: int
```

## Generación de Estados de Cuenta

### **Proceso de Generación**
```python
async def generate_statement(
    third_party_id: UUID,
    start_date: date,
    end_date: date,
    include_pending: bool = False,
    format_type: str = "PDF"
) -> ThirdPartyStatement:
    
    # 1. Validar tercero y fechas
    third_party = await validate_third_party(third_party_id)
    validate_date_range(start_date, end_date)
    
    # 2. Obtener saldo inicial
    opening_balance = await calculate_opening_balance(third_party_id, start_date)
    
    # 3. Obtener movimientos del período
    movements = await get_period_movements(
        third_party_id, start_date, end_date, include_pending
    )
    
    # 4. Calcular saldos corrientes
    statement_lines = []
    running_balance = opening_balance
    
    for movement in movements:
        running_balance += (movement.debit_amount - movement.credit_amount)
        
        line = StatementLine(
            **movement.dict(),
            running_balance=running_balance
        )
        statement_lines.append(line)
    
    # 5. Generar resumen
    summary = calculate_statement_summary(statement_lines, third_party_id)
    
    # 6. Crear encabezado
    header = StatementHeader(
        third_party_id=third_party_id,
        third_party_name=third_party.name,
        # ...otros campos del tercero
        opening_balance=opening_balance,
        closing_balance=running_balance,
        # ...otros campos calculados
    )
    
    # 7. Ensamblar estado completo
    statement = ThirdPartyStatement(
        header=header,
        lines=statement_lines,
        summary=summary
    )
    
    # 8. Generar formato solicitado
    if format_type == "PDF":
        return await generate_pdf_statement(statement)
    elif format_type == "EXCEL":
        return await generate_excel_statement(statement)
    else:
        return statement
```

### **Cálculo de Saldo Inicial**
```python
async def calculate_opening_balance(third_party_id: UUID, start_date: date) -> Decimal:
    """Calcula el saldo al inicio del período"""
    
    result = await db.execute(
        select(
            func.sum(JournalEntryLine.debit - JournalEntryLine.credit)
        ).select_from(
            JournalEntryLine.join(JournalEntry)
        ).where(
            and_(
                JournalEntryLine.third_party_id == third_party_id,
                JournalEntry.entry_date < start_date,
                JournalEntry.status == "POSTED"
            )
        )
    )
    
    balance = result.scalar() or Decimal('0.00')
    return balance
```

### **Obtención de Movimientos**
```python
async def get_period_movements(
    third_party_id: UUID,
    start_date: date,
    end_date: date,
    include_pending: bool = False
) -> List[StatementLine]:
    """Obtiene todos los movimientos del tercero en el período"""
    
    query = select(
        JournalEntryLine.id.label('line_id'),
        JournalEntry.id.label('journal_entry_id'),
        JournalEntry.entry_number,
        JournalEntry.entry_date,
        JournalEntry.description.label('entry_description'),
        JournalEntry.reference.label('entry_reference'),
        JournalEntry.status.label('entry_status'),
        JournalEntry.posting_date,
        Account.code.label('account_code'),
        Account.name.label('account_name'),
        JournalEntryLine.description.label('line_description'),
        JournalEntryLine.debit.label('debit_amount'),
        JournalEntryLine.credit.label('credit_amount'),
        JournalEntryLine.document_reference,
        CostCenter.name.label('cost_center_name')
    ).select_from(
        JournalEntryLine
        .join(JournalEntry)
        .join(Account)
        .outerjoin(CostCenter)
    ).where(
        and_(
            JournalEntryLine.third_party_id == third_party_id,
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date
        )
    ).order_by(JournalEntry.entry_date, JournalEntry.entry_number)
    
    # Filtrar por estado si es necesario
    if not include_pending:
        query = query.where(JournalEntry.status == "POSTED")
    
    result = await db.execute(query)
    return [StatementLine(**row._asdict()) for row in result.fetchall()]
```

## Análisis de Antigüedad de Saldos

### **Categorización por Vencimiento**
```python
async def calculate_aging_analysis(third_party_id: UUID, as_of_date: date = None) -> AgingAnalysis:
    """Analiza la antigüedad de los saldos del tercero"""
    
    if as_of_date is None:
        as_of_date = date.today()
    
    # Obtener todos los movimientos no pagados
    unpaid_movements = await get_unpaid_movements(third_party_id, as_of_date)
    
    aging_buckets = {
        "current": Decimal('0.00'),        # 0-30 días
        "overdue_30": Decimal('0.00'),     # 31-60 días
        "overdue_60": Decimal('0.00'),     # 61-90 días
        "overdue_90": Decimal('0.00'),     # 91-120 días
        "overdue_120": Decimal('0.00')     # Más de 120 días
    }
    
    for movement in unpaid_movements:
        days_overdue = (as_of_date - movement.due_date).days
        balance = movement.debit_amount - movement.credit_amount
        
        if days_overdue <= 0:
            aging_buckets["current"] += balance
        elif days_overdue <= 30:
            aging_buckets["overdue_30"] += balance
        elif days_overdue <= 60:
            aging_buckets["overdue_60"] += balance
        elif days_overdue <= 90:
            aging_buckets["overdue_90"] += balance
        else:
            aging_buckets["overdue_120"] += balance
    
    total_balance = sum(aging_buckets.values())
    
    return AgingAnalysis(
        third_party_id=third_party_id,
        as_of_date=as_of_date,
        total_balance=total_balance,
        **aging_buckets,
        # Calcular porcentajes
        current_percentage=aging_buckets["current"] / total_balance * 100 if total_balance else 0,
        overdue_percentage=(total_balance - aging_buckets["current"]) / total_balance * 100 if total_balance else 0
    )
```

### **Identificación de Vencimientos**
```python
async def get_upcoming_due_dates(
    third_party_id: UUID,
    days_ahead: int = 30
) -> List[UpcomingDue]:
    """Identifica facturas que vencen en los próximos días"""
    
    future_date = date.today() + timedelta(days=days_ahead)
    
    query = select(
        JournalEntry.entry_number,
        JournalEntry.entry_date,
        JournalEntry.description,
        JournalEntryLine.due_date,
        func.sum(JournalEntryLine.debit - JournalEntryLine.credit).label('amount_due')
    ).select_from(
        JournalEntryLine.join(JournalEntry)
    ).where(
        and_(
            JournalEntryLine.third_party_id == third_party_id,
            JournalEntryLine.due_date.between(date.today(), future_date),
            JournalEntry.status == "POSTED"
        )
    ).group_by(
        JournalEntry.entry_number,
        JournalEntry.entry_date,
        JournalEntry.description,
        JournalEntryLine.due_date
    ).having(
        func.sum(JournalEntryLine.debit - JournalEntryLine.credit) > 0
    ).order_by(JournalEntryLine.due_date)
    
    result = await db.execute(query)
    return [UpcomingDue(**row._asdict()) for row in result.fetchall()]
```

## Formatos de Estados de Cuenta

### **Formato PDF**
```python
async def generate_pdf_statement(statement: ThirdPartyStatement) -> bytes:
    """Genera estado de cuenta en formato PDF"""
    
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Encabezado de la empresa
    company_header = Paragraph(
        f"<b>ESTADO DE CUENTA</b><br/>"
        f"Período: {statement.header.period_start} - {statement.header.period_end}",
        styles['Title']
    )
    story.append(company_header)
    
    # Información del tercero
    third_party_info = [
        ['Tercero:', statement.header.third_party_name],
        ['Código:', statement.header.third_party_code],
        ['Documento:', f"{statement.header.document_type} {statement.header.document_number}"],
        ['Email:', statement.header.contact_email],
        ['Teléfono:', statement.header.contact_phone]
    ]
    
    info_table = Table(third_party_info)
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(info_table)
    
    # Resumen de saldos
    balance_summary = [
        ['Saldo Inicial:', f"${statement.header.opening_balance:,.2f}"],
        ['Total Débitos:', f"${statement.header.total_debits:,.2f}"],
        ['Total Créditos:', f"${statement.header.total_credits:,.2f}"],
        ['Saldo Final:', f"${statement.header.closing_balance:,.2f}"]
    ]
    
    balance_table = Table(balance_summary)
    balance_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(balance_table)
    
    # Detalle de movimientos
    movement_headers = [
        'Fecha', 'Asiento', 'Descripción', 'Cuenta', 'Débito', 'Crédito', 'Saldo'
    ]
    
    movement_data = [movement_headers]
    for line in statement.lines:
        movement_data.append([
            line.entry_date.strftime('%Y-%m-%d'),
            line.entry_number,
            line.line_description[:40],
            f"{line.account_code} - {line.account_name}"[:30],
            f"${line.debit_amount:,.2f}" if line.debit_amount else "",
            f"${line.credit_amount:,.2f}" if line.credit_amount else "",
            f"${line.running_balance:,.2f}"
        ])
    
    movement_table = Table(movement_data)
    movement_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT')
    ]))
    story.append(movement_table)
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
```

### **Formato Excel**
```python
async def generate_excel_statement(statement: ThirdPartyStatement) -> bytes:
    """Genera estado de cuenta en formato Excel"""
    
    import pandas as pd
    from io import BytesIO
    
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Hoja de resumen
        summary_data = {
            'Concepto': [
                'Tercero', 'Código', 'Documento', 'Email',
                'Saldo Inicial', 'Total Débitos', 'Total Créditos', 'Saldo Final'
            ],
            'Valor': [
                statement.header.third_party_name,
                statement.header.third_party_code,
                f"{statement.header.document_type} {statement.header.document_number}",
                statement.header.contact_email,
                float(statement.header.opening_balance),
                float(statement.header.total_debits),
                float(statement.header.total_credits),
                float(statement.header.closing_balance)
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        # Hoja de movimientos
        movements_data = []
        for line in statement.lines:
            movements_data.append({
                'Fecha': line.entry_date,
                'Asiento': line.entry_number,
                'Descripción': line.line_description,
                'Cuenta': f"{line.account_code} - {line.account_name}",
                'Débito': float(line.debit_amount) if line.debit_amount else 0,
                'Crédito': float(line.credit_amount) if line.credit_amount else 0,
                'Saldo': float(line.running_balance),
                'Estado': line.entry_status,
                'Centro de Costo': line.cost_center_name or '',
                'Referencia': line.document_reference or ''
            })
        
        movements_df = pd.DataFrame(movements_data)
        movements_df.to_excel(writer, sheet_name='Movimientos', index=False)
        
        # Hoja de análisis de antigüedad
        aging = await calculate_aging_analysis(statement.header.third_party_id)
        aging_data = {
            'Rango': ['Corriente (0-30)', '31-60 días', '61-90 días', '91-120 días', 'Más de 120 días'],
            'Saldo': [
                float(aging.current),
                float(aging.overdue_30),
                float(aging.overdue_60),
                float(aging.overdue_90),
                float(aging.overdue_120)
            ],
            'Porcentaje': [
                aging.current_percentage,
                float(aging.overdue_30) / float(aging.total_balance) * 100 if aging.total_balance else 0,
                float(aging.overdue_60) / float(aging.total_balance) * 100 if aging.total_balance else 0,
                float(aging.overdue_90) / float(aging.total_balance) * 100 if aging.total_balance else 0,
                float(aging.overdue_120) / float(aging.total_balance) * 100 if aging.total_balance else 0
            ]
        }
        
        aging_df = pd.DataFrame(aging_data)
        aging_df.to_excel(writer, sheet_name='Antigüedad', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()
```

## API de Estados de Cuenta

### **Endpoints Principales**

#### **Generar Estado de Cuenta**
```http
GET /api/v1/third-parties/{id}/statement
Parameters:
  - start_date: date (formato YYYY-MM-DD)
  - end_date: date (formato YYYY-MM-DD)
  - include_pending: boolean (incluir asientos pendientes)
  - format: string (PDF, EXCEL, JSON)
  - language: string (es, en)

Response:
{
  "statement_id": "uuid",
  "third_party_id": "uuid",
  "period_start": "2024-01-01",
  "period_end": "2024-03-31",
  "format": "PDF",
  "file_url": "/downloads/statements/uuid.pdf",
  "generated_at": "2024-04-01T10:30:00Z"
}
```

#### **Análisis de Antigüedad**
```http
GET /api/v1/third-parties/{id}/aging-analysis
Parameters:
  - as_of_date: date (fecha de corte)
  - include_details: boolean (incluir detalle por documento)

Response:
{
  "third_party_id": "uuid",
  "as_of_date": "2024-04-01",
  "total_balance": 150000.00,
  "current": 80000.00,
  "overdue_30": 40000.00,
  "overdue_60": 20000.00,
  "overdue_90": 10000.00,
  "overdue_120": 0.00,
  "current_percentage": 53.33,
  "overdue_percentage": 46.67
}
```

#### **Próximos Vencimientos**
```http
GET /api/v1/third-parties/{id}/upcoming-dues
Parameters:
  - days_ahead: integer (días hacia adelante, default 30)
  - min_amount: decimal (monto mínimo)

Response:
[
  {
    "entry_number": "AST-001",
    "entry_date": "2024-03-01",
    "due_date": "2024-04-15",
    "description": "Factura servicios marzo",
    "amount_due": 75000.00,
    "days_until_due": 14
  }
]
```

### **Descarga de Archivos**
```http
GET /api/v1/downloads/statements/{statement_id}
Headers:
  - Authorization: Bearer {token}

Response: Binary file (PDF/Excel)
```

## Casos de Uso Prácticos

### **Caso 1: Estado de Cuenta Mensual**
```python
# Generar estado de cuenta del mes anterior
last_month_start = date.today().replace(day=1) - timedelta(days=1)
last_month_start = last_month_start.replace(day=1)
last_month_end = date.today().replace(day=1) - timedelta(days=1)

statement = await generate_statement(
    third_party_id=customer_id,
    start_date=last_month_start,
    end_date=last_month_end,
    format_type="PDF"
)

# Enviar por email
await send_statement_email(customer_id, statement.file_path)
```

### **Caso 2: Análisis de Cartera Vencida**
```python
# Obtener todos los clientes con saldo vencido
overdue_customers = await get_customers_with_overdue_balance()

for customer in overdue_customers:
    aging = await calculate_aging_analysis(customer.id)
    
    if aging.overdue_percentage > 30:
        # Cliente con alta morosidad
        await create_collection_alert(customer.id, aging)
        
        # Generar estado de cuenta detallado
        statement = await generate_statement(
            customer.id,
            start_date=date.today() - timedelta(days=365),
            end_date=date.today(),
            format_type="EXCEL"
        )
```

### **Caso 3: Seguimiento de Proveedores**
```python
# Revisar estados de cuenta de proveedores principales
key_suppliers = await get_key_suppliers()

for supplier in key_suppliers:
    statement = await generate_statement(
        supplier.id,
        start_date=date.today() - timedelta(days=90),
        end_date=date.today()
    )
    
    # Verificar saldos a favor del proveedor
    if statement.header.closing_balance > 0:
        upcoming = await get_upcoming_due_dates(supplier.id, 15)
        if upcoming:
            await notify_accounts_payable(supplier.id, upcoming)
```

## Beneficios de los Estados de Cuenta

### **Para la Organización**
- **Transparencia**: Información clara y detallada para terceros
- **Control**: Seguimiento automático de saldos y vencimientos
- **Eficiencia**: Automatización de procesos manuales
- **Profesionalismo**: Documentos con formato empresarial

### **Para Terceros**
- **Claridad**: Estado completo de la relación comercial
- **Detalle**: Información específica de cada transacción
- **Trazabilidad**: Seguimiento histórico de movimientos
- **Confianza**: Información verificable y consistente

### **Para Gestión Financiera**
- **Análisis**: Herramientas para evaluar comportamiento de pago
- **Predicción**: Identificación de tendencias y patrones
- **Control de Riesgo**: Alertas tempranas de problemas
- **Optimización**: Mejora en términos y condiciones comerciales

---

*Documentación de estados de cuenta de terceros - Sprint 2*
