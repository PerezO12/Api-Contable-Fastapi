# Gestión de Terceros

El módulo de gestión de terceros proporciona un sistema integral para administrar clientes, proveedores, empleados y otros terceros en el sistema contable. Este módulo implementa funcionalidades completas de CRUD, validaciones automáticas, y un sistema flexible de categorización que se integra perfectamente con los asientos contables.

## Características Principales

### ✅ **Gestión Integral de Terceros**
- Soporte para múltiples tipos: clientes, proveedores, empleados y otros
- Información comercial completa y personalizable
- Datos de contacto y ubicación detallados
- Configuración flexible de términos de pago y comerciales

### ✅ **Validación Automática de Documentos**
- Validación por tipo de documento (RUT, NIT, PASSPORT, etc.)
- Verificación automática según país de origen
- Formateo y normalización de números de documento
- Prevención de duplicados y conflictos

### ✅ **Sistema de Estados y Categorización**
- Estados flexibles (activo, inactivo, suspendido, etc.)
- Categorización por tipo de negocio
- Clasificación por importancia y riesgo
- Segmentación por características comerciales

### ✅ **Integración con Contabilidad**
- Asociación directa con asientos contables
- Tracking automático de saldos y movimientos
- Generación de estados de cuenta en tiempo real
- Análisis de comportamiento de pago

## Modelo de Datos

### **Estructura del Tercero**
```python
class ThirdParty(Base):
    __tablename__ = "third_parties"
    
    # Identificación básica
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Documentación legal
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Clasificación
    third_party_type: Mapped[str] = mapped_column(String(20), nullable=False)
    business_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Información comercial
    email: Mapped[Optional[str]] = mapped_column(String(254))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    website: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Ubicación
    address: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50), default="Colombia")
    
    # Términos comerciales
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100))
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    discount_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    
    # Estado y control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20))
    importance_level: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    
    # Relaciones
    journal_entry_lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine", back_populates="third_party", lazy="select"
    )
```

### **Tipos de Terceros Soportados**
```python
class ThirdPartyType(str, Enum):
    CUSTOMER = "CUSTOMER"       # Cliente
    SUPPLIER = "SUPPLIER"       # Proveedor
    EMPLOYEE = "EMPLOYEE"       # Empleado
    PARTNER = "PARTNER"         # Socio comercial
    GOVERNMENT = "GOVERNMENT"   # Entidad gubernamental
    BANK = "BANK"              # Institución bancaria
    OTHER = "OTHER"            # Otros
```

### **Tipos de Documento por País**
```python
DOCUMENT_TYPES_BY_COUNTRY = {
    "Colombia": ["NIT", "CC", "CE", "PASSPORT", "RUT"],
    "México": ["RFC", "CURP", "INE", "PASSPORT"],
    "Argentina": ["CUIT", "CUIL", "DNI", "PASSPORT"],
    "Chile": ["RUT", "PASSPORT"],
    "Perú": ["RUC", "DNI", "PASSPORT"],
    "España": ["NIF", "NIE", "CIF", "PASSPORT"],
    "Internacional": ["PASSPORT", "TAX_ID", "BUSINESS_ID"]
}
```

## Operaciones CRUD

### **1. Creación de Terceros**

#### **Validaciones Automáticas**
1. **Código único**: Verificación de que el código no exista
2. **Documento válido**: Validación según tipo y país
3. **Email válido**: Verificación de formato de email
4. **Teléfono válido**: Validación de formato de teléfono
5. **Límite de crédito**: Validación de rangos apropiados

#### **Proceso de Creación**
```python
async def create_third_party(data: ThirdPartyCreate) -> ThirdParty:
    # 1. Validar datos básicos
    validate_basic_data(data)
    
    # 2. Validar documento según país
    validate_document(data.document_type, data.document_number, data.country)
    
    # 3. Verificar código único
    await verify_unique_code(data.code)
    
    # 4. Crear registro
    third_party = ThirdParty(**data.dict())
    third_party.id = uuid.uuid4()
    third_party.created_at = datetime.utcnow()
    
    # 5. Guardar en base de datos
    db.add(third_party)
    await db.commit()
    
    return third_party
```

#### **Ejemplo de Creación**
```json
{
  "code": "PROV-001",
  "name": "Proveedor Ejemplo S.A.S.",
  "document_type": "NIT",
  "document_number": "900123456-1",
  "third_party_type": "SUPPLIER",
  "business_type": "Servicios Tecnológicos",
  "email": "contacto@proveedor.com",
  "phone": "+57 300 123 4567",
  "address": "Calle 123 #45-67",
  "city": "Bogotá",
  "country": "Colombia",
  "payment_terms": "30 días",
  "credit_limit": 10000000.00,
  "is_active": true
}
```

### **2. Consulta de Terceros**

#### **Filtros Disponibles**
- **Por tipo**: Clientes, proveedores, empleados, etc.
- **Por estado**: Activos, inactivos, suspendidos
- **Por país/ciudad**: Ubicación geográfica
- **Por términos comerciales**: Condiciones de pago
- **Por saldos**: Con saldo, sin saldo, en mora
- **Por importancia**: Alta, media, baja prioridad

#### **Búsqueda Avanzada**
```python
async def search_third_parties(filters: ThirdPartyFilters) -> List[ThirdParty]:
    query = select(ThirdParty)
    
    # Filtros básicos
    if filters.third_party_type:
        query = query.where(ThirdParty.third_party_type == filters.third_party_type)
    
    if filters.is_active is not None:
        query = query.where(ThirdParty.is_active == filters.is_active)
    
    # Búsqueda por texto
    if filters.search_text:
        search_filter = or_(
            ThirdParty.name.ilike(f"%{filters.search_text}%"),
            ThirdParty.code.ilike(f"%{filters.search_text}%"),
            ThirdParty.document_number.ilike(f"%{filters.search_text}%")
        )
        query = query.where(search_filter)
    
    # Filtros de saldo
    if filters.has_balance:
        query = query.join(JournalEntryLine).group_by(ThirdParty.id).having(
            func.sum(JournalEntryLine.debit - JournalEntryLine.credit) != 0
        )
    
    return await db.execute(query)
```

### **3. Actualización de Terceros**

#### **Campos Actualizables**
- Información comercial (nombre, contacto, dirección)
- Términos comerciales (condiciones de pago, límites)
- Estado y clasificación (activo/inactivo, nivel de riesgo)
- Datos de auditoría (actualizado por, fecha de actualización)

#### **Validaciones de Actualización**
1. **Cambios de documento**: Verificar que no genere duplicados
2. **Estado activo**: Validar que no haya movimientos pendientes
3. **Límites de crédito**: Verificar contra saldos actuales
4. **Historial**: Mantener registro de cambios importantes

#### **Proceso de Actualización**
```python
async def update_third_party(id: UUID, data: ThirdPartyUpdate, user_id: UUID) -> ThirdParty:
    # 1. Obtener tercero existente
    third_party = await get_third_party_by_id(id)
    
    # 2. Validar cambios
    if data.document_number and data.document_number != third_party.document_number:
        await validate_document_change(data.document_type, data.document_number, data.country)
    
    # 3. Aplicar cambios
    for field, value in data.dict(exclude_unset=True).items():
        setattr(third_party, field, value)
    
    # 4. Actualizar auditoría
    third_party.updated_at = datetime.utcnow()
    third_party.updated_by = user_id
    
    # 5. Guardar cambios
    await db.commit()
    
    return third_party
```

### **4. Eliminación de Terceros**

#### **Validaciones de Eliminación**
1. **Sin movimientos activos**: No debe tener asientos contables asociados
2. **Sin saldos pendientes**: Saldo actual debe ser cero
3. **Sin transacciones futuras**: No debe tener compromisos pendientes
4. **Autorización**: Requiere permisos específicos

#### **Eliminación Lógica vs Física**
```python
async def delete_third_party(id: UUID, force_delete: bool = False) -> bool:
    third_party = await get_third_party_by_id(id)
    
    # Verificar restricciones
    has_movements = await check_journal_entries(id)
    has_balance = await get_current_balance(id)
    
    if has_movements or has_balance != 0:
        if not force_delete:
            raise ValueError("No se puede eliminar tercero con movimientos o saldo")
        else:
            # Eliminación lógica
            third_party.is_active = False
            third_party.deleted_at = datetime.utcnow()
            await db.commit()
            return True
    else:
        # Eliminación física
        await db.delete(third_party)
        await db.commit()
        return True
```

## Validaciones Específicas

### **Validación de Documentos**

#### **NIT (Colombia)**
```python
def validate_nit(nit: str) -> bool:
    # Remover espacios y guiones
    nit_clean = re.sub(r'[^0-9]', '', nit)
    
    if len(nit_clean) < 9 or len(nit_clean) > 10:
        return False
    
    # Algoritmo de validación NIT
    multipliers = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47]
    total = 0
    
    for i, digit in enumerate(nit_clean[:-1]):
        total += int(digit) * multipliers[len(nit_clean) - 2 - i]
    
    remainder = total % 11
    check_digit = 11 - remainder if remainder >= 2 else remainder
    
    return check_digit == int(nit_clean[-1])
```

#### **RUT (Chile)**
```python
def validate_rut(rut: str) -> bool:
    # Formato: 12.345.678-9 o 12345678-9
    rut_clean = re.sub(r'[^0-9kK-]', '', rut.upper())
    
    if '-' not in rut_clean:
        return False
    
    number, check_digit = rut_clean.split('-')
    
    # Algoritmo de validación RUT
    multiplier = 2
    total = 0
    
    for digit in reversed(number):
        total += int(digit) * multiplier
        multiplier = multiplier + 1 if multiplier < 7 else 2
    
    remainder = total % 11
    expected_digit = str(11 - remainder) if remainder < 2 else 'K' if remainder == 10 else str(11 - remainder)
    
    return check_digit == expected_digit
```

### **Validación de Emails**
```python
import re

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_business_email(email: str, company_domains: List[str] = None) -> bool:
    if not validate_email(email):
        return False
    
    # Verificar si es un dominio comercial válido
    domain = email.split('@')[1].lower()
    
    # Evitar dominios genéricos para terceros comerciales
    generic_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
    
    if company_domains:
        return domain in company_domains
    
    return domain not in generic_domains
```

### **Validación de Teléfonos**
```python
import phonenumbers

def validate_phone(phone: str, country_code: str = "CO") -> bool:
    try:
        parsed_number = phonenumbers.parse(phone, country_code)
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.NumberParseException:
        return False

def format_phone(phone: str, country_code: str = "CO") -> str:
    try:
        parsed_number = phonenumbers.parse(phone, country_code)
        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except phonenumbers.NumberParseException:
        return phone
```

## Configuración y Personalización

### **Configuración por País**
```python
COUNTRY_SETTINGS = {
    "Colombia": {
        "default_document_type": "NIT",
        "required_fields": ["document_number", "city"],
        "tax_id_format": "NIT",
        "phone_country_code": "CO",
        "currency": "COP"
    },
    "México": {
        "default_document_type": "RFC",
        "required_fields": ["document_number", "rfc"],
        "tax_id_format": "RFC",
        "phone_country_code": "MX",
        "currency": "MXN"
    }
}
```

### **Configuración de Tipos de Negocio**
```python
BUSINESS_TYPES = {
    "SUPPLIER": [
        "Servicios Profesionales",
        "Tecnología",
        "Construcción",
        "Manufactura",
        "Transporte",
        "Consultoría",
        "Mantenimiento"
    ],
    "CUSTOMER": [
        "Corporativo",
        "PYME",
        "Gobierno",
        "Individual",
        "Distribuidor",
        "Mayorista",
        "Detallista"
    ]
}
```

### **Configuración de Términos de Pago**
```python
PAYMENT_TERMS = [
    "Contado",
    "8 días",
    "15 días",
    "30 días",
    "45 días",
    "60 días",
    "90 días",
    "Personalizado"
]

PAYMENT_METHODS = [
    "Transferencia bancaria",
    "Cheque",
    "Efectivo",
    "Tarjeta de crédito",
    "Débito automático",
    "Crédito documentario"
]
```

## Integración con Asientos Contables

### **Asociación Automática**
```python
async def create_journal_entry_with_third_party(
    entry_data: JournalEntryCreate,
    third_party_id: UUID
) -> JournalEntry:
    # Validar que el tercero existe y está activo
    third_party = await validate_third_party(third_party_id)
    
    # Crear asiento con asociación
    for line in entry_data.lines:
        line.third_party_id = third_party_id
    
    # Crear el asiento normalmente
    journal_entry = await create_journal_entry(entry_data)
    
    # Actualizar saldos del tercero
    await update_third_party_balance(third_party_id)
    
    return journal_entry
```

### **Tracking de Saldos**
```python
async def get_third_party_balance(third_party_id: UUID) -> ThirdPartyBalance:
    result = await db.execute(
        select(
            func.sum(JournalEntryLine.debit).label('total_debit'),
            func.sum(JournalEntryLine.credit).label('total_credit')
        ).where(JournalEntryLine.third_party_id == third_party_id)
    )
    
    row = result.first()
    total_debit = row.total_debit or 0
    total_credit = row.total_credit or 0
    
    return ThirdPartyBalance(
        third_party_id=third_party_id,
        total_debit=total_debit,
        total_credit=total_credit,
        current_balance=total_debit - total_credit,
        last_movement=await get_last_movement_date(third_party_id)
    )
```

## Casos de Uso Comunes

### **Caso 1: Registro de Nuevo Proveedor**
```python
# Datos del proveedor
proveedor_data = {
    "code": "PROV-TEC-001",
    "name": "Tecnología y Soluciones S.A.S.",
    "document_type": "NIT",
    "document_number": "900555666-1",
    "third_party_type": "SUPPLIER",
    "business_type": "Tecnología",
    "email": "facturacion@tecnosol.com",
    "phone": "+57 301 555 6666",
    "address": "Carrera 15 #93-47",
    "city": "Bogotá",
    "country": "Colombia",
    "payment_terms": "30 días",
    "credit_limit": 50000000.00
}

# Crear proveedor
proveedor = await create_third_party(proveedor_data)
```

### **Caso 2: Búsqueda de Clientes con Saldo**
```python
# Filtros de búsqueda
filters = ThirdPartyFilters(
    third_party_type="CUSTOMER",
    is_active=True,
    has_balance=True,
    country="Colombia"
)

# Ejecutar búsqueda
clientes_con_saldo = await search_third_parties(filters)

# Obtener detalles de saldos
for cliente in clientes_con_saldo:
    balance = await get_third_party_balance(cliente.id)
    print(f"{cliente.name}: {balance.current_balance}")
```

### **Caso 3: Actualización Masiva de Términos**
```python
# Actualizar términos de pago para todos los proveedores pequeños
small_suppliers = await search_third_parties(
    ThirdPartyFilters(
        third_party_type="SUPPLIER",
        business_type="PYME"
    )
)

for supplier in small_suppliers:
    await update_third_party(
        supplier.id,
        ThirdPartyUpdate(payment_terms="15 días"),
        user_id
    )
```

## Beneficios del Sistema

### **Para Administradores**
- **Centralización**: Toda la información de terceros en un solo lugar
- **Validación Automática**: Prevención de errores en datos críticos
- **Flexibilidad**: Configuración adaptable a diferentes países y necesidades
- **Integración**: Conexión directa con la contabilidad

### **Para Usuarios Finales**
- **Facilidad de Uso**: Interfaz intuitiva y búsquedas eficientes
- **Información Completa**: Acceso a todo el historial y estado actual
- **Automatización**: Procesos automáticos para tareas repetitivas
- **Confiabilidad**: Datos validados y consistentes

### **Para la Organización**
- **Mejor Relación con Terceros**: Información organizada y accesible
- **Control Financiero**: Seguimiento automático de saldos y términos
- **Cumplimiento**: Validaciones que aseguran cumplimiento normativo
- **Eficiencia**: Reducción de tiempo en gestión administrativa

---

*Documentación de gestión de terceros - Sprint 2*
