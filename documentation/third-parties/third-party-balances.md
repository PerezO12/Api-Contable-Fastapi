# Balances y Análisis de Antigüedad

El sistema de análisis de balances y antigüedad proporciona herramientas avanzadas para el seguimiento y gestión de saldos de terceros. Incluye análisis detallado de vencimientos, identificación de riesgos crediticios, y herramientas para optimizar la gestión de cobranza y pagos.

## Características del Análisis de Balances

### ✅ **Análisis de Antigüedad Automático**
- Categorización por períodos de vencimiento
- Cálculo automático de días vencidos
- Alertas de morosidad y riesgo
- Tendencias de comportamiento de pago

### ✅ **Gestión de Cobranza Inteligente**
- Priorización automática de casos
- Scoring de comportamiento crediticio
- Recomendaciones de acciones
- Seguimiento de gestiones realizadas

### ✅ **Análisis Predictivo**
- Proyecciones de flujo de caja
- Identificación de patrones de pago
- Estimación de pérdidas esperadas
- Alertas tempranas de deterioro

### ✅ **Reportes Ejecutivos**
- Dashboard de cartera por edades
- KPIs de gestión de cobranza
- Análisis comparativo de terceros
- Métricas de efectividad

## Modelo de Análisis de Antigüedad

### **Estructura de Buckets de Edad**
```python
class AgingBucket:
    """Representa un rango de antigüedad de saldos"""
    
    name: str                    # Nombre del bucket (ej: "0-30 días")
    min_days: int               # Días mínimos del rango
    max_days: int               # Días máximos del rango
    risk_level: str             # Nivel de riesgo (LOW, MEDIUM, HIGH, CRITICAL)
    collection_priority: int    # Prioridad de cobranza (1-5)
    provision_percentage: float # Porcentaje de provisión sugerido
    
    # Métricas del bucket
    amount: Decimal            # Monto total en el bucket
    percentage: float          # Porcentaje del total
    account_count: int         # Número de cuentas en el bucket
    average_amount: Decimal    # Monto promedio por cuenta

# Configuración estándar de buckets
STANDARD_AGING_BUCKETS = [
    AgingBucket("Corriente", 0, 30, "LOW", 1, 0.0),
    AgingBucket("31-60 días", 31, 60, "MEDIUM", 2, 2.0),
    AgingBucket("61-90 días", 61, 90, "MEDIUM", 3, 5.0),
    AgingBucket("91-120 días", 91, 120, "HIGH", 4, 10.0),
    AgingBucket("121-180 días", 121, 180, "HIGH", 4, 25.0),
    AgingBucket("Más de 180 días", 181, 9999, "CRITICAL", 5, 50.0)
]
```

### **Análisis Individual de Tercero**
```python
class ThirdPartyAgingAnalysis:
    # Identificación
    third_party_id: UUID
    third_party_name: str
    third_party_type: str
    analysis_date: date
    
    # Información comercial
    credit_limit: Decimal
    payment_terms: str
    account_manager: str
    
    # Saldos por antigüedad
    aging_buckets: List[AgingBucket]
    total_balance: Decimal
    overdue_balance: Decimal
    current_balance: Decimal
    
    # Métricas de riesgo
    risk_score: int             # 1-100 (100 = máximo riesgo)
    payment_behavior_score: int # 1-100 (100 = excelente pagador)
    days_sales_outstanding: int # DSO promedio
    
    # Tendencias
    balance_trend: str          # INCREASING, DECREASING, STABLE
    payment_trend: str          # IMPROVING, DETERIORATING, STABLE
    last_payment_date: Optional[date]
    average_payment_delay: int
    
    # Recomendaciones
    collection_priority: int    # 1-5
    recommended_actions: List[str]
    risk_flags: List[str]
    
    # Histórico
    historical_data: List[dict] # Últimos 12 meses
```

## Cálculo de Antigüedad de Saldos

### **Proceso de Análisis Completo**
```python
async def perform_aging_analysis(
    third_party_id: UUID,
    as_of_date: date = None,
    include_future: bool = False
) -> ThirdPartyAgingAnalysis:
    """Realiza análisis completo de antigüedad para un tercero"""
    
    if as_of_date is None:
        as_of_date = date.today()
    
    # 1. Obtener información básica del tercero
    third_party = await get_third_party_by_id(third_party_id)
    
    # 2. Obtener todos los movimientos pendientes
    pending_movements = await get_pending_movements(third_party_id, as_of_date, include_future)
    
    # 3. Calcular antigüedad para cada movimiento
    aged_movements = []
    for movement in pending_movements:
        days_overdue = calculate_days_overdue(movement, as_of_date)
        aged_movements.append({
            **movement,
            'days_overdue': days_overdue,
            'bucket': classify_aging_bucket(days_overdue)
        })
    
    # 4. Agrupar por buckets de antigüedad
    aging_buckets = group_by_aging_buckets(aged_movements)
    
    # 5. Calcular métricas de riesgo
    risk_metrics = await calculate_risk_metrics(third_party_id, aged_movements)
    
    # 6. Analizar tendencias históricas
    trends = await analyze_payment_trends(third_party_id, as_of_date)
    
    # 7. Generar recomendaciones
    recommendations = generate_collection_recommendations(aging_buckets, risk_metrics, trends)
    
    # 8. Ensamblar análisis completo
    return ThirdPartyAgingAnalysis(
        third_party_id=third_party_id,
        third_party_name=third_party.name,
        analysis_date=as_of_date,
        aging_buckets=aging_buckets,
        **risk_metrics,
        **trends,
        recommended_actions=recommendations
    )

async def get_pending_movements(
    third_party_id: UUID,
    as_of_date: date,
    include_future: bool = False
) -> List[dict]:
    """Obtiene movimientos pendientes de pago/cobro"""
    
    query = select(
        JournalEntry.entry_number,
        JournalEntry.entry_date,
        JournalEntry.description,
        JournalEntry.reference,
        JournalEntryLine.due_date,
        JournalEntryLine.debit,
        JournalEntryLine.credit,
        Account.code.label('account_code'),
        Account.name.label('account_name')
    ).select_from(
        JournalEntryLine
        .join(JournalEntry)
        .join(Account)
    ).where(
        and_(
            JournalEntryLine.third_party_id == third_party_id,
            JournalEntry.status == "POSTED"
        )
    )
    
    # Filtrar por fecha si no se incluyen futuros
    if not include_future:
        query = query.where(JournalEntry.entry_date <= as_of_date)
    
    # Obtener solo movimientos con saldo pendiente
    subquery = select(
        JournalEntryLine.id,
        func.sum(JournalEntryLine.debit - JournalEntryLine.credit).label('net_amount')
    ).where(
        JournalEntryLine.third_party_id == third_party_id
    ).group_by(
        JournalEntryLine.id
    ).having(
        func.sum(JournalEntryLine.debit - JournalEntryLine.credit) != 0
    ).subquery()
    
    query = query.join(subquery, JournalEntryLine.id == subquery.c.id)
    
    result = await db.execute(query)
    return [dict(row._asdict()) for row in result.fetchall()]

def calculate_days_overdue(movement: dict, as_of_date: date) -> int:
    """Calcula días de vencimiento para un movimiento"""
    
    due_date = movement.get('due_date')
    if not due_date:
        # Si no hay fecha de vencimiento, usar términos de pago
        payment_terms = movement.get('payment_terms', '30')
        try:
            days_term = int(payment_terms.split()[0])
            due_date = movement['entry_date'] + timedelta(days=days_term)
        except:
            due_date = movement['entry_date'] + timedelta(days=30)
    
    days_overdue = (as_of_date - due_date).days
    return max(0, days_overdue)  # No puede ser negativo

def classify_aging_bucket(days_overdue: int) -> str:
    """Clasifica un movimiento en un bucket de antigüedad"""
    
    for bucket in STANDARD_AGING_BUCKETS:
        if bucket.min_days <= days_overdue <= bucket.max_days:
            return bucket.name
    
    return "Más de 180 días"  # Default para casos extremos
```

### **Agrupación por Buckets**
```python
def group_by_aging_buckets(aged_movements: List[dict]) -> List[AgingBucket]:
    """Agrupa movimientos por buckets de antigüedad"""
    
    bucket_totals = {}
    
    # Inicializar buckets
    for bucket_config in STANDARD_AGING_BUCKETS:
        bucket_totals[bucket_config.name] = {
            'config': bucket_config,
            'amount': Decimal('0.00'),
            'movements': [],
            'account_count': 0
        }
    
    # Agrupar movimientos
    for movement in aged_movements:
        bucket_name = movement['bucket']
        net_amount = movement['debit'] - movement['credit']
        
        bucket_totals[bucket_name]['amount'] += net_amount
        bucket_totals[bucket_name]['movements'].append(movement)
        bucket_totals[bucket_name]['account_count'] += 1
    
    # Calcular totales y porcentajes
    total_amount = sum(bucket['amount'] for bucket in bucket_totals.values())
    
    result_buckets = []
    for bucket_name, bucket_data in bucket_totals.items():
        config = bucket_data['config']
        amount = bucket_data['amount']
        
        aging_bucket = AgingBucket(
            name=config.name,
            min_days=config.min_days,
            max_days=config.max_days,
            risk_level=config.risk_level,
            collection_priority=config.collection_priority,
            provision_percentage=config.provision_percentage,
            amount=amount,
            percentage=float(amount / total_amount * 100) if total_amount else 0,
            account_count=bucket_data['account_count'],
            average_amount=amount / bucket_data['account_count'] if bucket_data['account_count'] else Decimal('0.00')
        )
        
        result_buckets.append(aging_bucket)
    
    return sorted(result_buckets, key=lambda x: x.min_days)
```

## Cálculo de Métricas de Riesgo

### **Score de Comportamiento de Pago**
```python
async def calculate_payment_behavior_score(third_party_id: UUID) -> int:
    """Calcula score de comportamiento de pago (1-100)"""
    
    # Obtener histórico de pagos últimos 12 meses
    payments_history = await get_payments_history(third_party_id, months=12)
    
    if not payments_history:
        return 50  # Score neutro para terceros sin historial
    
    score_components = {
        'payment_punctuality': 0,    # 40% del score
        'payment_consistency': 0,    # 30% del score
        'amount_accuracy': 0,        # 20% del score
        'relationship_length': 0     # 10% del score
    }
    
    # 1. Puntualidad de pagos (40%)
    total_payments = len(payments_history)
    on_time_payments = sum(1 for p in payments_history if p['days_delay'] <= 5)
    punctuality_ratio = on_time_payments / total_payments
    score_components['payment_punctuality'] = punctuality_ratio * 40
    
    # 2. Consistencia de pagos (30%)
    delays = [p['days_delay'] for p in payments_history]
    delay_std = statistics.stdev(delays) if len(delays) > 1 else 0
    consistency_score = max(0, 30 - (delay_std / 5))  # Penalizar alta variabilidad
    score_components['payment_consistency'] = min(30, consistency_score)
    
    # 3. Precisión en montos (20%)
    amount_errors = sum(1 for p in payments_history if abs(p['amount_variance']) > 0.01)
    accuracy_ratio = 1 - (amount_errors / total_payments)
    score_components['amount_accuracy'] = accuracy_ratio * 20
    
    # 4. Antigüedad de la relación (10%)
    relationship_months = await get_relationship_length_months(third_party_id)
    relationship_score = min(10, relationship_months / 12 * 10)  # Máximo a los 12 meses
    score_components['relationship_length'] = relationship_score
    
    # Score final (1-100)
    final_score = sum(score_components.values())
    return int(min(100, max(1, final_score)))

async def calculate_risk_score(third_party_id: UUID, aging_buckets: List[AgingBucket]) -> int:
    """Calcula score de riesgo crediticio (1-100, donde 100 es máximo riesgo)"""
    
    risk_factors = {
        'overdue_percentage': 0,     # 35% del score
        'concentration_risk': 0,     # 25% del score
        'payment_behavior': 0,       # 25% del score
        'external_factors': 0        # 15% del score
    }
    
    # 1. Porcentaje vencido (35%)
    total_balance = sum(bucket.amount for bucket in aging_buckets)
    overdue_balance = sum(bucket.amount for bucket in aging_buckets if bucket.min_days > 30)
    overdue_percentage = float(overdue_balance / total_balance) if total_balance else 0
    risk_factors['overdue_percentage'] = overdue_percentage * 35
    
    # 2. Riesgo de concentración (25%)
    # Evaluamos si el saldo es muy alto vs límite de crédito
    third_party = await get_third_party_by_id(third_party_id)
    if third_party.credit_limit and third_party.credit_limit > 0:
        concentration_ratio = float(total_balance / third_party.credit_limit)
        concentration_risk = min(25, concentration_ratio * 25)
    else:
        concentration_risk = 10  # Riesgo medio sin límite definido
    risk_factors['concentration_risk'] = concentration_risk
    
    # 3. Comportamiento de pago histórico (25%)
    payment_score = await calculate_payment_behavior_score(third_party_id)
    # Invertir score (100 - payment_score) para que sea riesgo
    behavior_risk = (100 - payment_score) / 100 * 25
    risk_factors['payment_behavior'] = behavior_risk
    
    # 4. Factores externos (15%)
    external_risk = await assess_external_risk_factors(third_party_id)
    risk_factors['external_factors'] = external_risk
    
    # Score final de riesgo
    final_risk_score = sum(risk_factors.values())
    return int(min(100, max(1, final_risk_score)))
```

### **Análisis de Tendencias**
```python
async def analyze_payment_trends(third_party_id: UUID, as_of_date: date) -> dict:
    """Analiza tendencias de comportamiento de pago"""
    
    # Obtener datos históricos (últimos 6 meses)
    historical_data = []
    for i in range(6):
        analysis_date = as_of_date - timedelta(days=30 * i)
        month_data = await get_monthly_aging_snapshot(third_party_id, analysis_date)
        historical_data.append(month_data)
    
    historical_data.reverse()  # Orden cronológico
    
    # Analizar tendencia de saldo total
    balances = [data['total_balance'] for data in historical_data]
    balance_trend = calculate_trend(balances)
    
    # Analizar tendencia de morosidad
    overdue_percentages = [data['overdue_percentage'] for data in historical_data]
    payment_trend = calculate_trend(overdue_percentages, inverse=True)
    
    # Calcular DSO promedio
    dso_values = [data['days_sales_outstanding'] for data in historical_data if data['days_sales_outstanding']]
    average_dso = statistics.mean(dso_values) if dso_values else 0
    
    # Última fecha de pago
    last_payment = await get_last_payment_date(third_party_id)
    
    # Promedio de días de retraso
    recent_delays = await get_recent_payment_delays(third_party_id, days=90)
    avg_delay = statistics.mean(recent_delays) if recent_delays else 0
    
    return {
        'balance_trend': balance_trend,
        'payment_trend': payment_trend,
        'last_payment_date': last_payment,
        'average_payment_delay': int(avg_delay),
        'days_sales_outstanding': int(average_dso),
        'historical_data': historical_data
    }

def calculate_trend(values: List[float], inverse: bool = False) -> str:
    """Calcula tendencia de una serie de valores"""
    
    if len(values) < 2:
        return "STABLE"
    
    # Calcular pendiente usando regresión lineal simple
    x = list(range(len(values)))
    n = len(values)
    
    sum_x = sum(x)
    sum_y = sum(values)
    sum_xy = sum(x[i] * values[i] for i in range(n))
    sum_x2 = sum(x[i] ** 2 for i in range(n))
    
    # Pendiente
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    
    # Aplicar inversión si es necesario (para métricas donde menor es mejor)
    if inverse:
        slope = -slope
    
    # Clasificar tendencia
    if slope > 0.1:
        return "INCREASING"
    elif slope < -0.1:
        return "DECREASING"
    else:
        return "STABLE"
```

## Generación de Recomendaciones

### **Sistema de Recomendaciones Automáticas**
```python
def generate_collection_recommendations(
    aging_buckets: List[AgingBucket],
    risk_metrics: dict,
    trends: dict
) -> List[str]:
    """Genera recomendaciones automáticas de cobranza"""
    
    recommendations = []
    
    total_balance = sum(bucket.amount for bucket in aging_buckets)
    overdue_balance = sum(bucket.amount for bucket in aging_buckets if bucket.min_days > 30)
    overdue_percentage = float(overdue_balance / total_balance) if total_balance else 0
    
    # Recomendaciones basadas en antigüedad
    if overdue_percentage > 0.5:
        recommendations.append("URGENTE: Más del 50% del saldo está vencido. Contactar inmediatamente.")
    elif overdue_percentage > 0.3:
        recommendations.append("ALTA PRIORIDAD: Iniciar gestión de cobranza activa.")
    elif overdue_percentage > 0.1:
        recommendations.append("Monitorear de cerca y enviar recordatorios de pago.")
    
    # Recomendaciones basadas en montos
    critical_bucket = next((b for b in aging_buckets if b.name == "Más de 180 días"), None)
    if critical_bucket and critical_bucket.amount > 0:
        recommendations.append("Evaluar provisión para cuentas incobrables.")
        recommendations.append("Considerar acciones legales para recuperación.")
    
    # Recomendaciones basadas en tendencias
    if trends['balance_trend'] == "INCREASING":
        recommendations.append("Saldo en crecimiento: Revisar límite de crédito.")
    
    if trends['payment_trend'] == "DETERIORATING":
        recommendations.append("Comportamiento de pago deteriorándose: Incrementar seguimiento.")
    
    if trends['average_payment_delay'] > 15:
        recommendations.append("Retrasos promedio altos: Renegociar términos de pago.")
    
    # Recomendaciones basadas en score de riesgo
    risk_score = risk_metrics.get('risk_score', 50)
    if risk_score > 80:
        recommendations.append("RIESGO CRÍTICO: Suspender nuevos créditos.")
        recommendations.append("Requerir garantías adicionales para futuras transacciones.")
    elif risk_score > 60:
        recommendations.append("RIESGO ALTO: Reducir límite de crédito.")
        recommendations.append("Incrementar frecuencia de seguimiento.")
    
    # Recomendaciones de acciones específicas
    if not trends['last_payment_date'] or (date.today() - trends['last_payment_date']).days > 60:
        recommendations.append("Sin pagos recientes: Contacto directo para verificar situación.")
    
    return recommendations

def determine_collection_priority(aging_analysis: ThirdPartyAgingAnalysis) -> int:
    """Determina prioridad de cobranza (1-5, donde 5 es máxima prioridad)"""
    
    priority_score = 0
    
    # Factor 1: Porcentaje vencido
    overdue_percentage = float(aging_analysis.overdue_balance / aging_analysis.total_balance) if aging_analysis.total_balance else 0
    if overdue_percentage > 0.7:
        priority_score += 3
    elif overdue_percentage > 0.4:
        priority_score += 2
    elif overdue_percentage > 0.2:
        priority_score += 1
    
    # Factor 2: Monto total
    if aging_analysis.total_balance > 10000000:  # $10M
        priority_score += 2
    elif aging_analysis.total_balance > 5000000:  # $5M
        priority_score += 1
    
    # Factor 3: Score de riesgo
    if aging_analysis.risk_score > 80:
        priority_score += 2
    elif aging_analysis.risk_score > 60:
        priority_score += 1
    
    # Factor 4: Tendencias
    if aging_analysis.balance_trend == "INCREASING" and aging_analysis.payment_trend == "DETERIORATING":
        priority_score += 1
    
    return min(5, max(1, priority_score))
```

## Reportes de Análisis de Balances

### **Reporte de Cartera por Edades**
```python
async def generate_aging_report(
    third_party_type: str = None,
    as_of_date: date = None,
    include_zero_balances: bool = False
) -> AgingReport:
    """Genera reporte consolidado de cartera por edades"""
    
    if as_of_date is None:
        as_of_date = date.today()
    
    # Obtener todos los terceros con saldo
    query = select(ThirdParty).where(ThirdParty.is_active == True)
    if third_party_type:
        query = query.where(ThirdParty.third_party_type == third_party_type)
    
    third_parties = await db.execute(query)
    
    consolidated_buckets = {}
    detailed_analysis = []
    
    for tp in third_parties:
        # Realizar análisis individual
        analysis = await perform_aging_analysis(tp.id, as_of_date)
        
        # Filtrar saldos cero si es necesario
        if not include_zero_balances and analysis.total_balance == 0:
            continue
        
        detailed_analysis.append(analysis)
        
        # Consolidar buckets
        for bucket in analysis.aging_buckets:
            bucket_name = bucket.name
            if bucket_name not in consolidated_buckets:
                consolidated_buckets[bucket_name] = {
                    'amount': Decimal('0.00'),
                    'account_count': 0,
                    'config': bucket
                }
            
            consolidated_buckets[bucket_name]['amount'] += bucket.amount
            consolidated_buckets[bucket_name]['account_count'] += bucket.account_count
    
    # Calcular totales generales
    total_amount = sum(bucket['amount'] for bucket in consolidated_buckets.values())
    
    # Preparar buckets consolidados
    consolidated_aging = []
    for bucket_name, bucket_data in consolidated_buckets.items():
        config = bucket_data['config']
        amount = bucket_data['amount']
        
        consolidated_aging.append(AgingBucket(
            name=config.name,
            min_days=config.min_days,
            max_days=config.max_days,
            risk_level=config.risk_level,
            collection_priority=config.collection_priority,
            provision_percentage=config.provision_percentage,
            amount=amount,
            percentage=float(amount / total_amount * 100) if total_amount else 0,
            account_count=bucket_data['account_count'],
            average_amount=amount / bucket_data['account_count'] if bucket_data['account_count'] else Decimal('0.00')
        ))
    
    return AgingReport(
        report_date=as_of_date,
        third_party_type=third_party_type,
        total_amount=total_amount,
        total_accounts=len(detailed_analysis),
        consolidated_aging=sorted(consolidated_aging, key=lambda x: x.min_days),
        detailed_analysis=sorted(detailed_analysis, key=lambda x: x.risk_score, reverse=True)
    )
```

### **API de Análisis de Balances**

#### **Análisis Individual**
```http
GET /api/v1/third-parties/{id}/aging-analysis
Parameters:
  - as_of_date: date (fecha de corte)
  - include_future: boolean (incluir vencimientos futuros)
  - detailed: boolean (incluir análisis detallado)

Response:
{
  "third_party_id": "uuid",
  "third_party_name": "Cliente Ejemplo",
  "analysis_date": "2024-04-01",
  "total_balance": 150000.00,
  "overdue_balance": 80000.00,
  "current_balance": 70000.00,
  "aging_buckets": [
    {
      "name": "Corriente",
      "min_days": 0,
      "max_days": 30,
      "amount": 70000.00,
      "percentage": 46.67,
      "risk_level": "LOW"
    },
    {
      "name": "31-60 días",
      "min_days": 31,
      "max_days": 60,
      "amount": 50000.00,
      "percentage": 33.33,
      "risk_level": "MEDIUM"
    }
  ],
  "risk_score": 65,
  "payment_behavior_score": 75,
  "collection_priority": 3,
  "recommended_actions": [
    "ALTA PRIORIDAD: Iniciar gestión de cobranza activa.",
    "Monitorear de cerca y enviar recordatorios de pago."
  ]
}
```

#### **Reporte Consolidado**
```http
GET /api/v1/reports/aging-analysis
Parameters:
  - third_party_type: string (CUSTOMER, SUPPLIER)
  - as_of_date: date
  - include_zero_balances: boolean
  - format: string (JSON, PDF, EXCEL)

Response:
{
  "report_date": "2024-04-01",
  "third_party_type": "CUSTOMER",
  "total_amount": 5000000.00,
  "total_accounts": 150,
  "consolidated_aging": [...],
  "summary_metrics": {
    "average_days_overdue": 35,
    "total_at_risk": 1500000.00,
    "provision_required": 125000.00,
    "collection_efficiency": 78.5
  }
}
```

#### **Alertas de Cobranza**
```http
GET /api/v1/collection/alerts
Parameters:
  - priority_level: integer (1-5)
  - risk_threshold: integer (score mínimo)
  - days_overdue_min: integer

Response:
[
  {
    "third_party_id": "uuid",
    "third_party_name": "Cliente Riesgo",
    "alert_level": "CRITICAL",
    "total_overdue": 250000.00,
    "days_overdue": 120,
    "risk_score": 85,
    "recommended_action": "Contactar inmediatamente",
    "last_contact_date": "2024-03-15"
  }
]
```

## Casos de Uso Prácticos

### **Caso 1: Reporte Semanal de Cartera**
```python
# Generar reporte de cartera de clientes
aging_report = await generate_aging_report(
    third_party_type="CUSTOMER",
    as_of_date=date.today(),
    include_zero_balances=False
)

# Identificar casos críticos
critical_cases = [
    analysis for analysis in aging_report.detailed_analysis
    if analysis.risk_score > 80 or analysis.collection_priority >= 4
]

# Enviar alertas al equipo de cobranza
for case in critical_cases:
    await send_collection_alert(case)
```

### **Caso 2: Análisis de Proveedores por Pagar**
```python
# Obtener proveedores con saldos a favor
supplier_balances = await generate_aging_report(
    third_party_type="SUPPLIER"
)

# Identificar pagos próximos a vencer
upcoming_payments = []
for analysis in supplier_balances.detailed_analysis:
    if analysis.total_balance > 0:  # Saldo a favor del proveedor
        upcoming = await get_upcoming_due_dates(analysis.third_party_id, 15)
        if upcoming:
            upcoming_payments.extend(upcoming)

# Priorizar pagos
upcoming_payments.sort(key=lambda x: x.due_date)
```

### **Caso 3: Optimización de Términos Comerciales**
```python
# Analizar comportamiento de pago por términos
payment_terms_analysis = {}

for analysis in all_customer_analysis:
    third_party = await get_third_party_by_id(analysis.third_party_id)
    terms = third_party.payment_terms
    
    if terms not in payment_terms_analysis:
        payment_terms_analysis[terms] = []
    
    payment_terms_analysis[terms].append({
        'payment_score': analysis.payment_behavior_score,
        'average_delay': analysis.average_payment_delay,
        'risk_score': analysis.risk_score
    })

# Identificar términos óptimos
for terms, customers in payment_terms_analysis.items():
    avg_score = statistics.mean([c['payment_score'] for c in customers])
    avg_delay = statistics.mean([c['average_delay'] for c in customers])
    
    print(f"Términos {terms}: Score promedio {avg_score}, Retraso promedio {avg_delay} días")
```

## Beneficios del Análisis de Balances

### **Para Gestión Financiera**
- **Visibilidad Completa**: Estado real de la cartera en tiempo real
- **Gestión Proactiva**: Identificación temprana de riesgos
- **Optimización**: Mejora en términos y políticas de crédito
- **Automatización**: Reducción de trabajo manual en seguimiento

### **Para Cobranza**
- **Priorización**: Enfoque en casos más críticos
- **Eficiencia**: Herramientas automáticas de análisis
- **Seguimiento**: Métricas de efectividad de gestión
- **Predicción**: Identificación de patrones de comportamiento

### **Para la Organización**
- **Flujo de Caja**: Mejor predictibilidad de ingresos
- **Reducción de Riesgo**: Control proactivo de morosidad
- **Relaciones Comerciales**: Mejor gestión de terceros
- **Cumplimiento**: Provisiones adecuadas y oportunas

---

*Documentación de análisis de balances y antigüedad - Sprint 2*
