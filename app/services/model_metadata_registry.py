"""
Registry de Metadatos de Modelos para Importación Genérica
Contiene las definiciones de metadatos para todos los modelos importables
"""
from typing import Dict, List, Optional, Any
from app.schemas.generic_import import ModelMetadata, FieldMetadata, FieldType, ValidationRule


class ModelNotFoundError(Exception):
    """Exception for when a model is not found"""
    pass


class ModelMetadataRegistry:
    """
    Registro centralizado de metadatos de modelos para importación genérica
    """
    
    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._initialize_default_models()
    
    def _initialize_default_models(self):
        """Inicializa los metadatos de los modelos por defecto"""
          # Modelo Third Party (Clientes/Proveedores/Empleados)
        third_party_metadata = ModelMetadata(
            model_name="third_party",
            display_name="Tercero",
            description="Clientes, proveedores y empleados",
            table_name="third_parties",
            fields=[                FieldMetadata(
                    internal_name="code",
                    display_label="Código",
                    field_type=FieldType.STRING,
                    is_required=False,
                    is_unique=True,
                    max_length=20,
                    description="Código único del tercero (se genera automáticamente si no se proporciona)"
                ),
                FieldMetadata(
                    internal_name="name",
                    display_label="Nombre Completo",
                    field_type=FieldType.STRING,
                    is_required=True,
                    is_unique=True,
                    max_length=255,
                    description="Nombre completo del tercero"
                ),                FieldMetadata(
                    internal_name="document_number",
                    display_label="Número de Documento",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=50,
                    description="Cédula, NIT o documento de identificación (se genera automáticamente si no se proporciona)"
                ),
                FieldMetadata(
                    internal_name="document_type",
                    display_label="Tipo de Documento",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=10,
                    default_value="other",
                    description="CC, NIT, CE, etc. (por defecto: other)",
                    choices=[
                        {"value": "rut", "label": "RUT"},
                        {"value": "nit", "label": "NIT"},
                        {"value": "cuit", "label": "CUIT"},
                        {"value": "rfc", "label": "RFC"},
                        {"value": "passport", "label": "Pasaporte"},
                        {"value": "dni", "label": "DNI/Cédula"},
                        {"value": "other", "label": "Otro"}
                    ]
                ),
                FieldMetadata(
                    internal_name="email",
                    display_label="Correo Electrónico",
                    field_type=FieldType.EMAIL,
                    max_length=255,
                    description="Dirección de correo electrónico"
                ),
                FieldMetadata(
                    internal_name="phone",
                    display_label="Teléfono",
                    field_type=FieldType.PHONE,
                    max_length=20,
                    description="Número de teléfono"
                ),
                FieldMetadata(
                    internal_name="address",
                    display_label="Dirección",
                    field_type=FieldType.STRING,
                    max_length=500,
                    description="Dirección física"
                ),
                FieldMetadata(
                    internal_name="city",
                    display_label="Ciudad",
                    field_type=FieldType.STRING,
                    max_length=100,
                    description="Ciudad de residencia"
                ),                FieldMetadata(
                    internal_name="third_party_type",
                    display_label="Tipo de Tercero",
                    field_type=FieldType.STRING,
                    is_required=False,
                    default_value="customer",
                    description="customer, supplier, employee (por defecto: customer)",
                    choices=[
                        {"value": "customer", "label": "Cliente"},
                        {"value": "supplier", "label": "Proveedor"},
                        {"value": "employee", "label": "Empleado"},
                        {"value": "shareholder", "label": "Accionista"},
                        {"value": "bank", "label": "Banco"},
                        {"value": "government", "label": "Gobierno"},
                        {"value": "other", "label": "Otro"}
                    ]
                ),FieldMetadata(
                    internal_name="is_active",
                    display_label="Activo",
                    field_type=FieldType.BOOLEAN,
                    default_value="true",
                    description="Si el tercero está activo"
                ),
                FieldMetadata(
                    internal_name="is_tax_withholding_agent",
                    display_label="Agente de Retención",
                    field_type=FieldType.BOOLEAN,
                    default_value="false",
                    description="Si el tercero es agente de retención de impuestos"
                )
            ],
            business_key_fields=["name"],  # Usar nombre como clave de negocio única
            import_permissions=["can_create_third_parties", "can_update_third_parties"]
        )
        
        # Modelo Product
        product_metadata = ModelMetadata(
            model_name="product",
            display_name="Producto",
            description="Productos y servicios",
            table_name="products",
            fields=[
                FieldMetadata(
                    internal_name="code",
                    display_label="Código",
                    field_type=FieldType.STRING,
                    is_required=False,  # No obligatorio, se genera automáticamente
                    is_unique=True,
                    max_length=50,
                    description="Código único del producto (se genera automáticamente si no se proporciona)"
                ),
                FieldMetadata(
                    internal_name="name",
                    display_label="Nombre",
                    field_type=FieldType.STRING,
                    is_required=True,  # ÚNICO campo obligatorio
                    is_unique=True,    # Único y case sensitive
                    max_length=200,
                    description="Nombre único del producto (case sensitive)"
                ),
                FieldMetadata(
                    internal_name="description",
                    display_label="Descripción",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=1000,
                    description="Descripción detallada del producto"
                ),
                FieldMetadata(
                    internal_name="product_type",
                    display_label="Tipo de Producto",
                    field_type=FieldType.STRING,
                    is_required=False,  # No obligatorio, tiene valor por defecto
                    default_value="product",
                    description="Tipo de producto",
                    choices=[
                        {"value": "product", "label": "Producto físico"},
                        {"value": "service", "label": "Servicio"},
                        {"value": "both", "label": "Ambos"}
                    ]
                ),
                FieldMetadata(
                    internal_name="status",
                    display_label="Estado",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    default_value="active",
                    description="Estado del producto",
                    choices=[
                        {"value": "active", "label": "Activo"},
                        {"value": "inactive", "label": "Inactivo"},
                        {"value": "discontinued", "label": "Descontinuado"}
                    ]
                ),
                FieldMetadata(
                    internal_name="measurement_unit",
                    display_label="Unidad de Medida",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    default_value="unit",
                    description="Unidad de medida principal",
                    choices=[
                        {"value": "unit", "label": "Unidad"},
                        {"value": "kg", "label": "Kilogramo"},
                        {"value": "gram", "label": "Gramo"},
                        {"value": "liter", "label": "Litro"},
                        {"value": "meter", "label": "Metro"},
                        {"value": "cm", "label": "Centímetro"},
                        {"value": "m2", "label": "Metro cuadrado"},
                        {"value": "m3", "label": "Metro cúbico"},
                        {"value": "hour", "label": "Hora"},
                        {"value": "day", "label": "Día"},
                        {"value": "month", "label": "Mes"},
                        {"value": "year", "label": "Año"},
                        {"value": "dozen", "label": "Docena"},
                        {"value": "pack", "label": "Paquete"},
                        {"value": "box", "label": "Caja"}
                    ]
                ),
                FieldMetadata(
                    internal_name="category",
                    display_label="Categoría",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=100,
                    description="Categoría del producto"
                ),
                FieldMetadata(
                    internal_name="subcategory",
                    display_label="Subcategoría",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=100,
                    description="Subcategoría del producto"
                ),
                FieldMetadata(
                    internal_name="brand",
                    display_label="Marca",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=100,
                    description="Marca del producto"
                ),
                FieldMetadata(
                    internal_name="weight",
                    display_label="Peso (kg)",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    description="Peso en kilogramos"
                ),
                FieldMetadata(
                    internal_name="dimensions",
                    display_label="Dimensiones",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=100,
                    description="Dimensiones (LxAxA)"
                ),
                FieldMetadata(
                    internal_name="purchase_price",
                    display_label="Precio de Compra",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    default_value="0.00",
                    description="Precio de compra del producto"
                ),
                FieldMetadata(
                    internal_name="sale_price",
                    display_label="Precio de Venta",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    default_value="0.00",
                    description="Precio de venta del producto"
                ),
                FieldMetadata(
                    internal_name="min_sale_price",
                    display_label="Precio Mínimo de Venta",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    default_value="0.00",
                    description="Precio mínimo de venta permitido"
                ),
                FieldMetadata(
                    internal_name="suggested_price",
                    display_label="Precio Sugerido",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    default_value="0.00",
                    description="Precio sugerido de venta"
                ),
                FieldMetadata(
                    internal_name="tax_category",
                    display_label="Categoría de Impuesto",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    default_value="EXEMPT",
                    description="Categoría fiscal del producto",
                    choices=[
                        {"value": "EXEMPT", "label": "Exento"},
                        {"value": "ZERO_RATE", "label": "Tasa Cero"},
                        {"value": "REDUCED_RATE", "label": "Tasa Reducida"},
                        {"value": "STANDARD_RATE", "label": "Tasa Estándar"},
                        {"value": "SUPER_REDUCED_RATE", "label": "Tasa Súper Reducida"}
                    ]
                ),
                FieldMetadata(
                    internal_name="tax_rate",
                    display_label="Tasa de Impuesto (%)",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    max_value=100,
                    default_value="0.00",
                    description="Porcentaje de impuesto aplicable"
                ),
                FieldMetadata(
                    internal_name="manage_inventory",
                    display_label="Maneja Inventario",
                    field_type=FieldType.BOOLEAN,
                    is_required=False,  # Opcional
                    default_value="false",
                    description="Indica si se maneja inventario para este producto"
                ),
                FieldMetadata(
                    internal_name="current_stock",
                    display_label="Stock Actual",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    default_value="0.00",
                    description="Stock actual del producto"
                ),
                FieldMetadata(
                    internal_name="min_stock",
                    display_label="Stock Mínimo",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    default_value="0.00",
                    description="Stock mínimo requerido"
                ),
                FieldMetadata(
                    internal_name="max_stock",
                    display_label="Stock Máximo",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    default_value="0.00",
                    description="Stock máximo permitido"
                ),
                FieldMetadata(
                    internal_name="reorder_point",
                    display_label="Punto de Reorden",
                    field_type=FieldType.DECIMAL,
                    is_required=False,  # Opcional
                    min_value=0,
                    default_value="0.00",
                    description="Punto de reorden del producto"
                ),
                FieldMetadata(
                    internal_name="barcode",
                    display_label="Código de Barras",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=50,
                    description="Código de barras del producto"
                ),
                FieldMetadata(
                    internal_name="sku",
                    display_label="SKU",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=50,
                    description="Stock Keeping Unit"
                ),
                FieldMetadata(
                    internal_name="internal_reference",
                    display_label="Referencia Interna",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=50,
                    description="Referencia interna del producto"
                ),
                FieldMetadata(
                    internal_name="supplier_reference",
                    display_label="Referencia del Proveedor",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=50,
                    description="Referencia del proveedor"
                ),
                FieldMetadata(
                    internal_name="notes",
                    display_label="Notas",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    description="Notas adicionales sobre el producto"
                ),
                FieldMetadata(
                    internal_name="external_reference",
                    display_label="Referencia Externa",
                    field_type=FieldType.STRING,
                    is_required=False,  # Opcional
                    max_length=100,
                    description="Referencia externa del producto"
                )
            ],
            business_key_fields=["name"],  # Cambio: ahora el nombre es la clave de negocio
            import_permissions=["can_create_products", "can_update_products"]
        )
        
        # Modelo Account (Cuentas Contables)
        account_metadata = ModelMetadata(
            model_name="account",
            display_name="Cuenta Contable",
            description="Plan de cuentas contables",
            table_name="accounts",
            fields=[
                FieldMetadata(
                    internal_name="code",
                    display_label="Código",
                    field_type=FieldType.STRING,
                    is_required=True,
                    is_unique=True,
                    max_length=20,
                    description="Código de la cuenta contable"
                ),
                FieldMetadata(
                    internal_name="name",
                    display_label="Nombre",
                    field_type=FieldType.STRING,
                    is_required=True,
                    max_length=255,
                    description="Nombre de la cuenta"
                ),
                FieldMetadata(
                    internal_name="account_type",
                    display_label="Tipo de Cuenta",
                    field_type=FieldType.STRING,
                    is_required=True,
                    description="Tipo de cuenta contable",
                    choices=[
                        {"value": "activo", "label": "Activo"},
                        {"value": "pasivo", "label": "Pasivo"},
                        {"value": "patrimonio", "label": "Patrimonio"},
                        {"value": "ingreso", "label": "Ingreso"},
                        {"value": "gasto", "label": "Gasto"},
                        {"value": "costos", "label": "Costos"}
                    ]
                ),
                FieldMetadata(
                    internal_name="category",
                    display_label="Categoría",
                    field_type=FieldType.STRING,
                    is_required=False,
                    description="Categoría específica de la cuenta",
                    choices=[
                        {"value": "activo_corriente", "label": "Activo Corriente"},
                        {"value": "activo_no_corriente", "label": "Activo No Corriente"},
                        {"value": "pasivo_corriente", "label": "Pasivo Corriente"},
                        {"value": "pasivo_no_corriente", "label": "Pasivo No Corriente"},
                        {"value": "capital", "label": "Capital"},
                        {"value": "reservas", "label": "Reservas"},
                        {"value": "resultados", "label": "Resultados"},
                        {"value": "ingresos_operacionales", "label": "Ingresos Operacionales"},
                        {"value": "ingresos_no_operacionales", "label": "Ingresos No Operacionales"},
                        {"value": "gastos_operacionales", "label": "Gastos Operacionales"},
                        {"value": "gastos_no_operacionales", "label": "Gastos No Operacionales"},
                        {"value": "costo_ventas", "label": "Costo de Ventas"},
                        {"value": "costos_produccion", "label": "Costos de Producción"}
                    ]
                ),
                FieldMetadata(
                    internal_name="cash_flow_category",
                    display_label="Categoría de Flujo de Efectivo",
                    field_type=FieldType.STRING,
                    is_required=False,
                    description="Categoría para clasificación en flujo de efectivo",
                    choices=[
                        {"value": "operating", "label": "Actividades de Operación"},
                        {"value": "investing", "label": "Actividades de Inversión"},
                        {"value": "financing", "label": "Actividades de Financiamiento"},
                        {"value": "cash", "label": "Efectivo y Equivalentes"}
                    ]
                ),
                FieldMetadata(
                    internal_name="parent_account_code",
                    display_label="Cuenta Padre",
                    field_type=FieldType.MANY_TO_ONE,
                    related_model="account",
                    search_field="code",
                    description="Código de la cuenta padre"
                ),
                FieldMetadata(
                    internal_name="level",
                    display_label="Nivel",
                    field_type=FieldType.INTEGER,
                    min_value=1,
                    max_value=10,
                    description="Nivel jerárquico de la cuenta"
                ),
                FieldMetadata(
                    internal_name="allows_movements",
                    display_label="Permite Movimientos",
                    field_type=FieldType.BOOLEAN,
                    default_value="true",
                    description="Si la cuenta permite movimientos contables"
                ),
                FieldMetadata(
                    internal_name="requires_third_party",
                    display_label="Requiere Tercero",
                    field_type=FieldType.BOOLEAN,
                    default_value="false",
                    description="Si la cuenta requiere especificar un tercero"
                ),
                FieldMetadata(
                    internal_name="requires_cost_center",
                    display_label="Requiere Centro de Costo",
                    field_type=FieldType.BOOLEAN,
                    default_value="false",
                    description="Si la cuenta requiere especificar un centro de costo"
                ),
                FieldMetadata(
                    internal_name="allows_reconciliation",
                    display_label="Permite Conciliación",
                    field_type=FieldType.BOOLEAN,
                    default_value="false",
                    description="Si la cuenta permite conciliación bancaria o de terceros"
                ),
                FieldMetadata(
                    internal_name="description",
                    display_label="Descripción",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=1000,
                    description="Descripción detallada de la cuenta"
                ),
                FieldMetadata(
                    internal_name="notes",
                    display_label="Notas",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=1000,
                    description="Notas adicionales sobre la cuenta"
                ),
                FieldMetadata(
                    internal_name="is_active",
                    display_label="Activa",
                    field_type=FieldType.BOOLEAN,
                    default_value="true",
                    description="Si la cuenta está activa"
                )
            ],
            business_key_fields=["code"],
            import_permissions=["can_create_accounts", "can_update_accounts"]
        )
        
        # Modelo Invoice - Definición completa con todos los campos disponibles
        invoice_metadata = ModelMetadata(
            model_name="invoice",
            display_name="Factura",
            description="Facturas de venta y compra con líneas de detalle",
            table_name="invoices",
            fields=[
                # === CAMPOS BÁSICOS DE IDENTIFICACIÓN ===
                FieldMetadata(
                    internal_name="number",
                    display_label="Número de Factura",
                    field_type=FieldType.STRING,
                    is_required=True,
                    is_unique=True,
                    max_length=50,
                    description="Número único de la factura (auto-generado si no se especifica)"
                ),
                FieldMetadata(
                    internal_name="internal_reference",
                    display_label="Referencia Interna",
                    field_type=FieldType.STRING,
                    max_length=100,
                    description="Referencia interna de la empresa"
                ),
                FieldMetadata(
                    internal_name="external_reference",
                    display_label="Referencia Externa",
                    field_type=FieldType.STRING,
                    max_length=100,
                    description="Referencia externa o número de factura del proveedor"
                ),
                
                # === TIPO Y ESTADO ===
                FieldMetadata(
                    internal_name="invoice_type",
                    display_label="Tipo de Factura",
                    field_type=FieldType.STRING,
                    is_required=True,
                    choices=[
                        {"value": "CUSTOMER_INVOICE", "label": "Factura de Cliente"},
                        {"value": "SUPPLIER_INVOICE", "label": "Factura de Proveedor"},
                        {"value": "CREDIT_NOTE", "label": "Nota de Crédito"},
                        {"value": "DEBIT_NOTE", "label": "Nota de Débito"}
                    ],
                    description="Tipo de documento de facturación"
                ),
                FieldMetadata(
                    internal_name="status",
                    display_label="Estado",
                    field_type=FieldType.STRING,
                    default_value="DRAFT",
                    choices=[
                        {"value": "DRAFT", "label": "Borrador"},
                        {"value": "PENDING", "label": "Pendiente"},
                        {"value": "APPROVED", "label": "Aprobada"},
                        {"value": "POSTED", "label": "Contabilizada"},
                        {"value": "PAID", "label": "Pagada"},
                        {"value": "PARTIALLY_PAID", "label": "Pagada Parcialmente"},
                        {"value": "OVERDUE", "label": "Vencida"},
                        {"value": "CANCELLED", "label": "Cancelada"}
                    ],
                    description="Estado actual de la factura"
                ),
                
                # === RELACIONES PRINCIPALES ===
                FieldMetadata(
                    internal_name="third_party_document",
                    display_label="Documento del Tercero",
                    field_type=FieldType.MANY_TO_ONE,
                    is_required=True,
                    related_model="third_party",
                    search_field="document_number",
                    description="Documento del cliente o proveedor"
                ),
                FieldMetadata(
                    internal_name="payment_terms_code",
                    display_label="Código Términos de Pago",
                    field_type=FieldType.MANY_TO_ONE,
                    related_model="payment_terms",
                    search_field="code",
                    description="Términos de pago (opcional)"
                ),
                FieldMetadata(
                    internal_name="journal_code",
                    display_label="Código Diario Contable",
                    field_type=FieldType.MANY_TO_ONE,
                    related_model="journal",
                    search_field="code",
                    description="Diario contable para numeración automática"
                ),
                FieldMetadata(
                    internal_name="cost_center_code",
                    display_label="Código Centro de Costo",
                    field_type=FieldType.MANY_TO_ONE,
                    related_model="cost_center",
                    search_field="code",
                    description="Centro de costo principal de la factura"
                ),
                
                # === CUENTAS CONTABLES (OVERRIDES) ===
                FieldMetadata(
                    internal_name="third_party_account_code",
                    display_label="Cuenta Cliente/Proveedor",
                    field_type=FieldType.MANY_TO_ONE,
                    related_model="account",
                    search_field="code",
                    description="Override cuenta por cobrar/pagar (opcional)"
                ),
                
                # === FECHAS ===
                FieldMetadata(
                    internal_name="invoice_date",
                    display_label="Fecha de Emisión",
                    field_type=FieldType.DATE,
                    is_required=True,
                    description="Fecha de emisión de la factura"
                ),
                FieldMetadata(
                    internal_name="due_date",
                    display_label="Fecha de Vencimiento",
                    field_type=FieldType.DATE,
                    description="Fecha límite de pago (calculada si hay términos de pago)"
                ),
                
                # === MONEDA Y CONVERSIÓN ===
                FieldMetadata(
                    internal_name="currency_code",
                    display_label="Código de Moneda",
                    field_type=FieldType.STRING,
                    max_length=3,
                    default_value="USD",
                    description="Código ISO de la moneda (USD, EUR, COP, etc.)"
                ),
                FieldMetadata(
                    internal_name="exchange_rate",
                    display_label="Tasa de Cambio",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    default_value="1.0000",
                    description="Tasa de cambio aplicada"
                ),
                
                # === MONTOS PRINCIPALES ===
                FieldMetadata(
                    internal_name="subtotal",
                    display_label="Subtotal",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    description="Subtotal antes de descuentos e impuestos"
                ),
                FieldMetadata(
                    internal_name="discount_amount",
                    display_label="Descuento Total",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    default_value="0.00",
                    description="Total de descuentos aplicados"
                ),
                FieldMetadata(
                    internal_name="tax_amount",
                    display_label="Impuestos Total",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    default_value="0.00",
                    description="Total de impuestos"
                ),
                FieldMetadata(
                    internal_name="total_amount",
                    display_label="Total",
                    field_type=FieldType.DECIMAL,
                    is_required=True,
                    min_value=0,
                    description="Valor total de la factura"
                ),
                
                # === CONTROL DE PAGOS ===
                FieldMetadata(
                    internal_name="paid_amount",
                    display_label="Monto Pagado",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    default_value="0.00",
                    description="Monto ya pagado de la factura"
                ),
                FieldMetadata(
                    internal_name="outstanding_amount",
                    display_label="Saldo Pendiente",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    description="Monto pendiente por pagar (calculado automáticamente)"
                ),
                
                # === INFORMACIÓN DESCRIPTIVA ===
                FieldMetadata(
                    internal_name="description",
                    display_label="Descripción",
                    field_type=FieldType.STRING,
                    description="Descripción general de la factura"
                ),
                FieldMetadata(
                    internal_name="notes",
                    display_label="Notas",
                    field_type=FieldType.STRING,
                    description="Notas adicionales"
                ),
                
                # === LÍNEAS DE FACTURA (DETALLE) ===
                FieldMetadata(
                    internal_name="line_sequence",
                    display_label="Línea - Secuencia",
                    field_type=FieldType.INTEGER,
                    description="Orden de la línea en la factura"
                ),
                FieldMetadata(
                    internal_name="line_product_code",
                    display_label="Línea - Código Producto",
                    field_type=FieldType.MANY_TO_ONE,
                    related_model="product",
                    search_field="code",
                    description="Código del producto o servicio"
                ),
                FieldMetadata(
                    internal_name="line_description",
                    display_label="Línea - Descripción",
                    field_type=FieldType.STRING,
                    description="Descripción del item de la línea"
                ),
                FieldMetadata(
                    internal_name="line_quantity",
                    display_label="Línea - Cantidad",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    default_value="1.0000",
                    description="Cantidad del producto/servicio"
                ),
                FieldMetadata(
                    internal_name="line_unit_price",
                    display_label="Línea - Precio Unitario",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    description="Precio unitario del producto/servicio"
                ),
                FieldMetadata(
                    internal_name="line_discount_percentage",
                    display_label="Línea - % Descuento",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    max_value=100,
                    default_value="0.00",
                    description="Porcentaje de descuento aplicado a la línea"
                ),
                
                # === CUENTAS CONTABLES POR LÍNEA ===
                FieldMetadata(
                    internal_name="line_account_code",
                    display_label="Línea - Cuenta Contable",
                    field_type=FieldType.MANY_TO_ONE,
                    related_model="account",
                    search_field="code",
                    description="Override cuenta ingreso/gasto para la línea"
                ),
                FieldMetadata(
                    internal_name="line_cost_center_code",
                    display_label="Línea - Centro de Costo",
                    field_type=FieldType.MANY_TO_ONE,
                    related_model="cost_center",
                    search_field="code",
                    description="Centro de costo específico de la línea"
                ),
                
                # === IMPUESTOS POR LÍNEA ===
                FieldMetadata(
                    internal_name="line_tax_codes",
                    display_label="Línea - Códigos Impuestos",
                    field_type=FieldType.STRING,
                    description="Códigos de impuestos separados por coma (ej: IVA19,RET01)"
                ),
                
                # === MONTOS CALCULADOS POR LÍNEA ===
                FieldMetadata(
                    internal_name="line_subtotal",
                    display_label="Línea - Subtotal",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    description="Subtotal de la línea (cantidad × precio)"
                ),
                FieldMetadata(
                    internal_name="line_discount_amount",
                    display_label="Línea - Descuento",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    description="Monto de descuento de la línea"
                ),
                FieldMetadata(
                    internal_name="line_tax_amount",
                    display_label="Línea - Impuestos",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    description="Total impuestos de la línea"
                ),
                FieldMetadata(
                    internal_name="line_total_amount",
                    display_label="Línea - Total",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    description="Total de la línea (subtotal - descuento + impuestos)"
                )
            ],
            business_key_fields=["number"],
            import_permissions=["can_create_invoices", "can_update_invoices"]
        )
        
        # Registrar los modelos
        self._models["third_party"] = third_party_metadata
        self._models["product"] = product_metadata
        self._models["account"] = account_metadata
        self._models["invoice"] = invoice_metadata
        
        # === NUEVOS MODELOS ===
        
        # Modelo Cost Center (Centros de Costo)
        cost_center_metadata = ModelMetadata(
            model_name="cost_center",
            display_name="Centro de Costo",
            description="Centros de costo para análisis de rentabilidad",
            table_name="cost_centers",
            fields=[
                FieldMetadata(
                    internal_name="code",
                    display_label="Código",
                    field_type=FieldType.STRING,
                    is_required=True,
                    is_unique=True,
                    max_length=20,
                    description="Código único del centro de costo"
                ),
                FieldMetadata(
                    internal_name="name",
                    display_label="Nombre",
                    field_type=FieldType.STRING,
                    is_required=True,
                    is_unique=True,
                    max_length=200,
                    description="Nombre único del centro de costo"
                ),
                FieldMetadata(
                    internal_name="description",
                    display_label="Descripción",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=1000,
                    description="Descripción detallada del centro de costo"
                ),
                FieldMetadata(
                    internal_name="parent_code",
                    display_label="Código del Centro Padre",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=20,
                    description="Código del centro de costo padre para estructura jerárquica"
                ),
                FieldMetadata(
                    internal_name="manager_name",
                    display_label="Responsable",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=200,
                    description="Nombre del responsable del centro de costo"
                ),
                FieldMetadata(
                    internal_name="budget_code",
                    display_label="Código Presupuestario",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=50,
                    description="Código para control presupuestario"
                ),
                FieldMetadata(
                    internal_name="is_active",
                    display_label="Activo",
                    field_type=FieldType.BOOLEAN,
                    is_required=False,
                    default_value="true",
                    description="Si el centro de costo está activo"
                ),
                FieldMetadata(
                    internal_name="allows_direct_assignment",
                    display_label="Permite Asignación Directa",
                    field_type=FieldType.BOOLEAN,
                    is_required=False,
                    default_value="true",
                    description="Si permite asignación directa de transacciones o solo es agrupador"
                ),
                FieldMetadata(
                    internal_name="notes",
                    display_label="Notas",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=1000,
                    description="Notas adicionales del centro de costo"
                )
            ],
            business_key_fields=["code"],
            import_permissions=["can_create_cost_centers", "can_update_cost_centers"]
        )
        
        # Modelo Journal (Diarios Contables)
        journal_metadata = ModelMetadata(
            model_name="journal",
            display_name="Diario Contable",
            description="Diarios contables para agrupación de asientos",
            table_name="journals",
            fields=[
                FieldMetadata(
                    internal_name="name",
                    display_label="Nombre",
                    field_type=FieldType.STRING,
                    is_required=True,
                    max_length=100,
                    description="Nombre descriptivo del diario"
                ),
                FieldMetadata(
                    internal_name="code",
                    display_label="Código",
                    field_type=FieldType.STRING,
                    is_required=True,
                    is_unique=True,
                    max_length=10,
                    description="Código único del diario"
                ),
                FieldMetadata(
                    internal_name="type",
                    display_label="Tipo de Diario",
                    field_type=FieldType.STRING,
                    is_required=True,
                    description="Tipo de diario contable",
                    choices=[
                        {"value": "sale", "label": "Ventas"},
                        {"value": "purchase", "label": "Compras"},
                        {"value": "cash", "label": "Efectivo"},
                        {"value": "bank", "label": "Banco"},
                        {"value": "miscellaneous", "label": "Varios"}
                    ]
                ),
                FieldMetadata(
                    internal_name="sequence_prefix",
                    display_label="Prefijo de Secuencia",
                    field_type=FieldType.STRING,
                    is_required=True,
                    is_unique=True,
                    max_length=10,
                    description="Prefijo único para la secuencia de numeración"
                ),
                FieldMetadata(
                    internal_name="sequence_padding",
                    display_label="Relleno de Secuencia",
                    field_type=FieldType.INTEGER,
                    is_required=False,
                    min_value=1,
                    max_value=10,
                    default_value="4",
                    description="Número de dígitos para rellenar con ceros (ej: 0001)"
                ),
                FieldMetadata(
                    internal_name="include_year_in_sequence",
                    display_label="Incluir Año en Secuencia",
                    field_type=FieldType.BOOLEAN,
                    is_required=False,
                    default_value="true",
                    description="Si incluir el año en la secuencia (ej: VEN/2025/0001)"
                ),
                FieldMetadata(
                    internal_name="reset_sequence_yearly",
                    display_label="Resetear Secuencia Anualmente",
                    field_type=FieldType.BOOLEAN,
                    is_required=False,
                    default_value="true",
                    description="Si resetear la secuencia cada año"
                ),
                FieldMetadata(
                    internal_name="requires_validation",
                    display_label="Requiere Validación",
                    field_type=FieldType.BOOLEAN,
                    is_required=False,
                    default_value="false",
                    description="Si los asientos en este diario requieren validación"
                ),
                FieldMetadata(
                    internal_name="allow_manual_entries",
                    display_label="Permite Asientos Manuales",
                    field_type=FieldType.BOOLEAN,
                    is_required=False,
                    default_value="true",
                    description="Si permite asientos manuales en este diario"
                ),
                FieldMetadata(
                    internal_name="is_active",
                    display_label="Activo",
                    field_type=FieldType.BOOLEAN,
                    is_required=False,
                    default_value="true",
                    description="Si el diario está activo"
                ),
                FieldMetadata(
                    internal_name="description",
                    display_label="Descripción",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=1000,
                    description="Descripción del propósito del diario"
                )
            ],
            business_key_fields=["code"],
            import_permissions=["can_create_journals", "can_update_journals"]
        )
        
        # Modelo Payment Terms (Términos de Pago)
        payment_terms_metadata = ModelMetadata(
            model_name="payment_terms",
            display_name="Términos de Pago",
            description="Condiciones y plazos de pago",
            table_name="payment_terms",
            fields=[
                FieldMetadata(
                    internal_name="code",
                    display_label="Código",
                    field_type=FieldType.STRING,
                    is_required=True,
                    is_unique=True,
                    max_length=20,
                    description="Código único de los términos de pago"
                ),
                FieldMetadata(
                    internal_name="name",
                    display_label="Nombre",
                    field_type=FieldType.STRING,
                    is_required=True,
                    max_length=100,
                    description="Nombre descriptivo de los términos de pago"
                ),
                FieldMetadata(
                    internal_name="description",
                    display_label="Descripción",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=1000,
                    description="Descripción detallada de los términos de pago"
                ),
                FieldMetadata(
                    internal_name="is_active",
                    display_label="Activo",
                    field_type=FieldType.BOOLEAN,
                    is_required=False,
                    default_value="true",
                    description="Si los términos de pago están activos"
                ),
                FieldMetadata(
                    internal_name="notes",
                    display_label="Notas",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=1000,
                    description="Notas adicionales de los términos de pago"
                ),
                # Campos para cronograma de pagos - formato simplificado para importación
                FieldMetadata(
                    internal_name="payment_schedule_days",
                    display_label="Días de Pago (separados por coma)",
                    field_type=FieldType.STRING,
                    is_required=True,
                    max_length=500,
                    description="Días desde la fecha de factura separados por comas (ej: 0,30,60)"
                ),
                FieldMetadata(
                    internal_name="payment_schedule_percentages",
                    display_label="Porcentajes de Pago (separados por coma)",
                    field_type=FieldType.STRING,
                    is_required=True,
                    max_length=500,
                    description="Porcentajes a pagar separados por comas (ej: 50.0,30.0,20.0)"
                ),
                FieldMetadata(
                    internal_name="payment_schedule_descriptions",
                    display_label="Descripciones de Pago (separadas por |)",
                    field_type=FieldType.STRING,
                    is_required=False,
                    max_length=1000,
                    description="Descripciones opcionales separadas por | (ej: Anticipo|Intermedio|Final)"
                )
            ],
            business_key_fields=["code"],
            import_permissions=["can_create_payment_terms", "can_update_payment_terms"]
        )
        
        # Registrar nuevos modelos
        self._models["cost_center"] = cost_center_metadata
        self._models["journal"] = journal_metadata
        self._models["payment_terms"] = payment_terms_metadata
    
    def get_model_metadata(self, model_name: str) -> ModelMetadata:
        """Obtiene los metadatos de un modelo"""
        if model_name not in self._models:
            raise ModelNotFoundError(f"Modelo '{model_name}' no encontrado")
        return self._models[model_name]
    
    def get_available_models(self) -> List[str]:
        """Obtiene lista de modelos disponibles"""
        return list(self._models.keys())
    
    def register_model(self, model_metadata: ModelMetadata):
        """Registra un nuevo modelo dinámicamente"""
        self._models[model_metadata.model_name] = model_metadata
    
    def get_field_metadata(self, model_name: str, field_name: str) -> Optional[FieldMetadata]:
        """Obtiene metadatos de un campo específico"""
        model_metadata = self.get_model_metadata(model_name)
        for field in model_metadata.fields:
            if field.internal_name == field_name:
                return field
        return None
    
    def get_required_fields(self, model_name: str) -> List[FieldMetadata]:
        """Obtiene campos obligatorios de un modelo"""
        model_metadata = self.get_model_metadata(model_name)
        return [field for field in model_metadata.fields if field.is_required]
    
    def get_unique_fields(self, model_name: str) -> List[FieldMetadata]:
        """Obtiene campos únicos de un modelo"""
        model_metadata = self.get_model_metadata(model_name)
        return [field for field in model_metadata.fields if field.is_unique]
    
    def get_business_key_fields(self, model_name: str) -> List[str]:
        """Obtiene campos clave de negocio para upsert"""
        model_metadata = self.get_model_metadata(model_name)
        return model_metadata.business_key_fields
    
    def suggest_column_mapping(self, model_name: str, column_names: List[str]) -> List[Dict[str, Any]]:
        """
        Genera sugerencias inteligentes de mapeo de columnas
        """
        model_metadata = self.get_model_metadata(model_name)
        suggestions = []
        
        # Mapeo de sinónimos comunes
        field_synonyms = {
            "name": ["nombre", "nom", "razón_social", "razon_social", "company"],
            "document_number": ["documento", "cedula", "nit", "ruc", "doc", "identificacion"],
            "email": ["correo", "mail", "e-mail", "email_address"],
            "phone": ["telefono", "tel", "celular", "movil", "phone_number"],
            "address": ["direccion", "addr", "domicilio"],
            "city": ["ciudad"],
            "code": ["codigo", "cod", "sku", "reference"],
            "description": ["descripcion", "desc", "detalle"],
            "price": ["precio", "valor", "amount"],
            "unit_price": ["precio_unitario", "precio_unidad"],
            "cost_price": ["costo", "precio_costo"],
            "invoice_date": ["fecha", "fecha_factura", "date"],
            "due_date": ["fecha_vencimiento", "vencimiento"],
            "total_amount": ["total", "valor_total", "amount"],
            "subtotal": ["subtotal", "sub_total"],
            # Sinónimos para centros de costo
            "parent_code": ["codigo_padre", "padre", "parent", "centro_padre"],
            "manager_name": ["responsable", "manager", "jefe", "encargado"],
            "budget_code": ["codigo_presupuesto", "presupuesto", "budget"],
            "allows_direct_assignment": ["asignacion_directa", "permite_asignar", "direct_assignment"],
            "notes": ["notas", "observaciones", "comentarios"],
            # Sinónimos para diarios
            "type": ["tipo", "tipo_diario", "journal_type"],
            "sequence_prefix": ["prefijo", "prefix", "prefijo_secuencia"],
            "sequence_padding": ["relleno", "padding", "digitos", "ceros"],
            "include_year_in_sequence": ["incluir_año", "año_secuencia", "year_sequence"],
            "reset_sequence_yearly": ["resetear_anual", "reset_anual", "yearly_reset"],
            "requires_validation": ["requiere_validacion", "validacion", "validation"],
            "allow_manual_entries": ["asientos_manuales", "manual_entries", "permite_manual"],
            "is_active": ["activo", "active", "estado", "habilitado"],
            # Sinónimos para términos de pago
            "payment_schedule_days": ["dias_pago", "dias", "days", "schedule_days"],
            "payment_schedule_percentages": ["porcentajes", "percentages", "%", "porcentajes_pago"],
            "payment_schedule_descriptions": ["descripciones", "descriptions", "desc_pago"]
        }
        
        for column in column_names:
            column_lower = column.lower().replace(" ", "_")
            best_match = None
            best_confidence = 0.0
            
            # Buscar coincidencia exacta
            for field in model_metadata.fields:
                if field.internal_name.lower() == column_lower:
                    best_match = field.internal_name
                    best_confidence = 1.0
                    break
            
            # Buscar en sinónimos
            if not best_match:
                for field_name, synonyms in field_synonyms.items():
                    if column_lower in synonyms:
                        # Verificar que el campo existe en el modelo
                        field_exists = any(f.internal_name == field_name for f in model_metadata.fields)
                        if field_exists:
                            best_match = field_name
                            best_confidence = 0.9
                            break
            
            # Buscar similitud parcial
            if not best_match:
                for field in model_metadata.fields:
                    field_lower = field.internal_name.lower()
                    if column_lower in field_lower or field_lower in column_lower:
                        if best_confidence < 0.7:
                            best_match = field.internal_name
                            best_confidence = 0.7
            
            if best_match and best_confidence > 0.5:
                suggestions.append({
                    "column_name": column,
                    "suggested_field": best_match,
                    "confidence": best_confidence,
                    "reason": "Coincidencia automática"
                })
        
        return suggestions


# Instancia global del registry
model_registry = ModelMetadataRegistry()
