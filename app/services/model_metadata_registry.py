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
        
        # Modelo Invoice
        invoice_metadata = ModelMetadata(
            model_name="invoice",
            display_name="Factura",
            description="Facturas de venta y compra",
            table_name="invoices",
            fields=[
                FieldMetadata(
                    internal_name="number",
                    display_label="Número de Factura",
                    field_type=FieldType.STRING,
                    is_required=True,
                    is_unique=True,
                    max_length=50,
                    description="Número único de la factura"
                ),
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
                    description="Fecha límite de pago"
                ),
                FieldMetadata(
                    internal_name="customer_document",
                    display_label="Documento del Cliente",
                    field_type=FieldType.MANY_TO_ONE,
                    is_required=True,
                    related_model="third_party",
                    search_field="document_number",
                    description="Documento del cliente"
                ),
                FieldMetadata(
                    internal_name="invoice_type",
                    display_label="Tipo de Factura",
                    field_type=FieldType.STRING,
                    is_required=True,
                    description="sale, purchase"
                ),
                FieldMetadata(
                    internal_name="subtotal",
                    display_label="Subtotal",
                    field_type=FieldType.DECIMAL,
                    is_required=True,
                    min_value=0,
                    description="Valor antes de impuestos"
                ),
                FieldMetadata(
                    internal_name="tax_amount",
                    display_label="Valor de Impuestos",
                    field_type=FieldType.DECIMAL,
                    min_value=0,
                    description="Total de impuestos"
                ),
                FieldMetadata(
                    internal_name="total_amount",
                    display_label="Valor Total",
                    field_type=FieldType.DECIMAL,
                    is_required=True,
                    min_value=0,
                    description="Valor total de la factura"
                ),
                FieldMetadata(
                    internal_name="status",
                    display_label="Estado",
                    field_type=FieldType.STRING,
                    default_value="draft",
                    description="draft, confirmed, paid, cancelled"
                ),
                FieldMetadata(
                    internal_name="reference",
                    display_label="Referencia",
                    field_type=FieldType.STRING,
                    max_length=100,
                    description="Referencia externa o número de orden"
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
            "subtotal": ["subtotal", "sub_total"]
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
