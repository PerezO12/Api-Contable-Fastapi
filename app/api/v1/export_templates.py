"""
API endpoints para exportación de plantillas de importación
Proporciona ejemplos en CSV, XLSX y JSON para cuentas y asientos contables
"""
import io
import csv
import pandas as pd
from typing import Dict, Any
from enum import Enum
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.deps import get_current_active_user
from app.models.user import User
from app.utils.exceptions import raise_insufficient_permissions

router = APIRouter()


class ImportFormat(str, Enum):
    """Formatos de importación disponibles"""
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


@router.get(
    "/accounts/{format}",
    summary="Export accounts template",
    description="Download example template for accounts in CSV, XLSX, or JSON format"
)
async def export_accounts_template(
    format: ImportFormat,
    current_user: User = Depends(get_current_active_user)
):
    """
    Exportar plantilla de ejemplo para importación de cuentas.
    Proporciona la estructura y nombres de columnas requeridos.
    """    # Verificar permisos
    if not current_user.can_modify_accounts:
        raise_insufficient_permissions()
    
    # Datos de ejemplo para cuentas
    example_accounts = [
        {
            "code": "1105",
            "name": "Caja General",
            "account_type": "ACTIVO",
            "category": "ACTIVO_CORRIENTE",
            "parent_code": "1100",
            "description": "Dinero en efectivo en caja principal",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": False,
            "requires_cost_center": False,
            "notes": "Cuenta para manejo de efectivo"
        },
        {
            "code": "1110",
            "name": "Bancos Moneda Nacional",
            "account_type": "ACTIVO",
            "category": "ACTIVO_CORRIENTE", 
            "parent_code": "1100",
            "description": "Depósitos en bancos en moneda nacional",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": True,
            "requires_cost_center": False,
            "notes": "Requiere especificar el banco como tercero"
        },
        {
            "code": "2105",
            "name": "Proveedores Nacionales",
            "account_type": "PASIVO",
            "category": "PASIVO_CORRIENTE",
            "parent_code": "2100",
            "description": "Cuentas por pagar a proveedores nacionales",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": True,
            "requires_cost_center": False,
            "notes": "Requiere especificar el proveedor"
        },
        {
            "code": "4105",
            "name": "Ingresos por Ventas",
            "account_type": "INGRESO",
            "category": "INGRESOS_OPERACIONALES",
            "parent_code": "4100",
            "description": "Ingresos por venta de productos o servicios",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": False,
            "requires_cost_center": True,
            "notes": "Requiere centro de costo para análisis"
        },
        {
            "code": "5105",
            "name": "Gastos de Oficina",
            "account_type": "GASTO",
            "category": "GASTOS_OPERACIONALES",
            "parent_code": "5100",
            "description": "Gastos administrativos de oficina",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": False,
            "requires_cost_center": True,
            "notes": "Para gastos de papelería, suministros, etc."
        }
    ]
    
    if format == ImportFormat.JSON:
        return JSONResponse(
            content={
                "template_info": {
                    "data_type": "accounts",
                    "format": "json",
                    "description": "Plantilla de ejemplo para importación de cuentas contables",
                    "required_fields": ["code", "name", "account_type"],
                    "optional_fields": ["category", "parent_code", "description", "is_active", "allows_movements", "requires_third_party", "requires_cost_center", "notes"]
                },
                "field_descriptions": {
                    "code": "Código único de la cuenta (máximo 20 caracteres)",
                    "name": "Nombre de la cuenta (máximo 200 caracteres)",
                    "account_type": "Tipo de cuenta: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS",
                    "category": "Categoría específica según el tipo de cuenta",
                    "parent_code": "Código de la cuenta padre para estructura jerárquica",
                    "description": "Descripción detallada de la cuenta",
                    "is_active": "true/false - Si la cuenta está activa",
                    "allows_movements": "true/false - Si permite registrar movimientos",
                    "requires_third_party": "true/false - Si requiere especificar tercero en los movimientos",
                    "requires_cost_center": "true/false - Si requiere centro de costo",
                    "notes": "Notas adicionales sobre la cuenta"
                },
                "valid_account_types": ["ACTIVO", "PASIVO", "PATRIMONIO", "INGRESO", "GASTO", "COSTOS"],
                "valid_categories": {
                    "ACTIVO": ["ACTIVO_CORRIENTE", "ACTIVO_NO_CORRIENTE"],
                    "PASIVO": ["PASIVO_CORRIENTE", "PASIVO_NO_CORRIENTE"],
                    "PATRIMONIO": ["CAPITAL", "RESERVAS", "RESULTADOS"],
                    "INGRESO": ["INGRESOS_OPERACIONALES", "INGRESOS_NO_OPERACIONALES"],
                    "GASTO": ["GASTOS_OPERACIONALES", "GASTOS_NO_OPERACIONALES"],
                    "COSTOS": ["COSTO_VENTAS", "COSTOS_PRODUCCION"]
                },
                "example_data": example_accounts
            },
            headers={"Content-Disposition": "attachment; filename=accounts_template.json"}
        )
    
    elif format == ImportFormat.CSV:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        headers = ["code", "name", "account_type", "category", "parent_code", 
                  "description", "is_active", "allows_movements", "requires_third_party", 
                  "requires_cost_center", "notes"]
        writer.writerow(headers)
        
        # Escribir datos de ejemplo
        for account in example_accounts:
            row = [account.get(field, "") for field in headers]
            writer.writerow(row)
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=accounts_template.csv"}
        )
    
    elif format == ImportFormat.XLSX:
        # Crear DataFrame con los datos de ejemplo
        df = pd.DataFrame(example_accounts)
        
        # Reordenar columnas en orden lógico
        column_order = ["code", "name", "account_type", "category", "parent_code", 
                       "description", "is_active", "allows_movements", "requires_third_party", 
                       "requires_cost_center", "notes"]
        df = df.reindex(columns=column_order)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja con datos de ejemplo
            df.to_excel(writer, sheet_name='Accounts_Template', index=False)
            
            # Hoja con documentación
            doc_data = {
                'Field': column_order,
                'Required': ['Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No'],
                'Description': [
                    'Código único de la cuenta (máximo 20 caracteres)',
                    'Nombre de la cuenta (máximo 200 caracteres)', 
                    'Tipo: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS',
                    'Categoría específica según el tipo de cuenta',
                    'Código de la cuenta padre para jerarquía',
                    'Descripción detallada de la cuenta',
                    'true/false - Si la cuenta está activa',
                    'true/false - Si permite movimientos',
                    'true/false - Si requiere tercero',
                    'true/false - Si requiere centro de costo',
                    'Notas adicionales'
                ]
            }
            doc_df = pd.DataFrame(doc_data)
            doc_df.to_excel(writer, sheet_name='Field_Documentation', index=False)
            
            # Hoja con tipos de cuenta válidos
            types_data = {
                'Account_Type': ['ACTIVO', 'PASIVO', 'PATRIMONIO', 'INGRESO', 'GASTO', 'COSTOS'],
                'Valid_Categories': [
                    'ACTIVO_CORRIENTE, ACTIVO_NO_CORRIENTE',
                    'PASIVO_CORRIENTE, PASIVO_NO_CORRIENTE',
                    'CAPITAL, RESERVAS, RESULTADOS',
                    'INGRESOS_OPERACIONALES, INGRESOS_NO_OPERACIONALES',
                    'GASTOS_OPERACIONALES, GASTOS_NO_OPERACIONALES',
                    'COSTO_VENTAS, COSTOS_PRODUCCION'
                ]
            }
            types_df = pd.DataFrame(types_data)
            types_df.to_excel(writer, sheet_name='Valid_Types', index=False)
        
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=accounts_template.xlsx"}
        )


@router.get(
    "/journal-entries/{format}",
    summary="Export journal entries template", 
    description="Download example template for journal entries in CSV, XLSX, or JSON format"
)
async def export_journal_entries_template(
    format: ImportFormat,
    current_user: User = Depends(get_current_active_user)
):
    """
    Exportar plantilla de ejemplo para importación de asientos contables.
    Proporciona la estructura y nombres de columnas requeridos.
    """    # Verificar permisos
    if not current_user.can_create_entries:
        raise_insufficient_permissions()
    
    # Datos de ejemplo para asientos contables
    example_entries = [
        {
            "entry_number": "AST-2024-001",
            "entry_date": "2024-01-15",
            "description": "Compra de material de oficina",
            "reference": "FAC-001234",
            "entry_type": "MANUAL",
            "account_code": "5105",
            "line_description": "Material de oficina - papelería",
            "debit_amount": 150000,
            "credit_amount": "",
            "third_party": "PAPELERIA ABC LTDA",
            "cost_center": "ADMIN",
            "line_reference": "FAC-001234"
        },
        {
            "entry_number": "AST-2024-001",
            "entry_date": "2024-01-15", 
            "description": "Compra de material de oficina",
            "reference": "FAC-001234",
            "entry_type": "MANUAL",
            "account_code": "1110",
            "line_description": "Pago con cheque Banco XYZ",
            "debit_amount": "",
            "credit_amount": 150000,
            "third_party": "BANCO XYZ",
            "cost_center": "",
            "line_reference": "CHQ-5678"
        },
        {
            "entry_number": "AST-2024-002",
            "entry_date": "2024-01-16",
            "description": "Venta de productos",
            "reference": "FAC-VTA-100",
            "entry_type": "MANUAL", 
            "account_code": "1105",
            "line_description": "Cobro en efectivo venta productos",
            "debit_amount": 230000,
            "credit_amount": "",
            "third_party": "CLIENTE VARIOS",
            "cost_center": "VENTAS",
            "line_reference": "FAC-VTA-100"
        },
        {
            "entry_number": "AST-2024-002",
            "entry_date": "2024-01-16",
            "description": "Venta de productos", 
            "reference": "FAC-VTA-100",
            "entry_type": "MANUAL",
            "account_code": "4105",
            "line_description": "Ingresos por venta de productos",
            "debit_amount": "",
            "credit_amount": 230000,
            "third_party": "CLIENTE VARIOS",
            "cost_center": "VENTAS", 
            "line_reference": "FAC-VTA-100"
        }
    ]
    
    if format == ImportFormat.JSON:
        return JSONResponse(
            content={
                "template_info": {
                    "data_type": "journal_entries",
                    "format": "json",
                    "description": "Plantilla de ejemplo para importación de asientos contables",
                    "required_fields": ["entry_number", "entry_date", "description", "account_code", "line_description"],
                    "optional_fields": ["reference", "entry_type", "debit_amount", "credit_amount", "third_party", "cost_center", "line_reference"],
                    "important_notes": [
                        "Cada línea del asiento debe tener entry_number idéntico para agruparse",
                        "Solo uno de debit_amount o credit_amount debe tener valor por línea",
                        "La suma de débitos debe igual la suma de créditos por asiento",
                        "Se requieren mínimo 2 líneas por asiento (doble partida)"
                    ]
                },
                "field_descriptions": {
                    "entry_number": "Número único del asiento contable",
                    "entry_date": "Fecha del asiento (formato: YYYY-MM-DD)",
                    "description": "Descripción general del asiento",
                    "reference": "Referencia externa (factura, documento, etc.)",
                    "entry_type": "Tipo de asiento: MANUAL, AUTOMATIC, ADJUSTMENT, OPENING, CLOSING",
                    "account_code": "Código de la cuenta contable",
                    "line_description": "Descripción específica de esta línea del asiento",
                    "debit_amount": "Monto débito (dejar vacío si es crédito)",
                    "credit_amount": "Monto crédito (dejar vacío si es débito)",
                    "third_party": "Tercero relacionado con el movimiento",
                    "cost_center": "Centro de costo para análisis de costos",
                    "line_reference": "Referencia específica de la línea"
                },
                "valid_entry_types": ["MANUAL", "AUTOMATIC", "ADJUSTMENT", "OPENING", "CLOSING", "REVERSAL"],
                "example_data": example_entries
            },
            headers={"Content-Disposition": "attachment; filename=journal_entries_template.json"}
        )
    
    elif format == ImportFormat.CSV:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        headers = ["entry_number", "entry_date", "description", "reference", "entry_type",
                  "account_code", "line_description", "debit_amount", "credit_amount", 
                  "third_party", "cost_center", "line_reference"]
        writer.writerow(headers)
        
        # Escribir datos de ejemplo
        for entry in example_entries:
            row = [entry.get(field, "") for field in headers]
            writer.writerow(row)
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=journal_entries_template.csv"}
        )
    
    elif format == ImportFormat.XLSX:
        # Crear DataFrame con los datos de ejemplo
        df = pd.DataFrame(example_entries)
        
        # Reordenar columnas en orden lógico
        column_order = ["entry_number", "entry_date", "description", "reference", "entry_type",
                       "account_code", "line_description", "debit_amount", "credit_amount", 
                       "third_party", "cost_center", "line_reference"]
        df = df.reindex(columns=column_order)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja con datos de ejemplo
            df.to_excel(writer, sheet_name='Journal_Entries_Template', index=False)
            
            # Hoja con documentación
            doc_data = {
                'Field': column_order,
                'Required': ['Yes', 'Yes', 'Yes', 'No', 'No', 'Yes', 'Yes', 'Conditional', 'Conditional', 'No', 'No', 'No'],
                'Description': [
                    'Número único del asiento contable',
                    'Fecha del asiento (formato: YYYY-MM-DD)',
                    'Descripción general del asiento',
                    'Referencia externa (factura, documento, etc.)',
                    'Tipo: MANUAL, AUTOMATIC, ADJUSTMENT, OPENING, CLOSING',
                    'Código de la cuenta contable',
                    'Descripción específica de esta línea',
                    'Monto débito (vacío si es crédito)',
                    'Monto crédito (vacío si es débito)',
                    'Tercero relacionado con el movimiento',
                    'Centro de costo para análisis',
                    'Referencia específica de la línea'
                ]
            }
            doc_df = pd.DataFrame(doc_data)
            doc_df.to_excel(writer, sheet_name='Field_Documentation', index=False)
            
            # Hoja con reglas de negocio
            rules_data = {
                'Rule': [
                    'Balance del asiento',
                    'Líneas mínimas',
                    'Monto por línea',
                    'Agrupación',
                    'Código de cuenta',
                    'Fecha válida',
                    'Tipos de asiento'
                ],
                'Description': [
                    'La suma de débitos debe ser igual a la suma de créditos',
                    'Cada asiento debe tener mínimo 2 líneas',
                    'Solo debit_amount O credit_amount debe tener valor por línea',
                    'Líneas con el mismo entry_number se agrupan en un asiento',
                    'El código de cuenta debe existir en el sistema',
                    'La fecha debe estar en formato YYYY-MM-DD',
                    'MANUAL, AUTOMATIC, ADJUSTMENT, OPENING, CLOSING, REVERSAL'
                ]
            }
            rules_df = pd.DataFrame(rules_data)
            rules_df.to_excel(writer, sheet_name='Business_Rules', index=False)
        
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=journal_entries_template.xlsx"}
        )


@router.get(
    "/",
    summary="List available templates",
    description="Get list of available import templates"
)
async def list_import_templates(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Listar plantillas de importación disponibles.
    """
    return {
        "available_templates": {
            "accounts": {
                "description": "Plantilla para importación de cuentas contables",
                "formats": ["csv", "xlsx", "json"],
                "endpoints": {
                    "csv": "/api/v1/templates/accounts/csv",
                    "xlsx": "/api/v1/templates/accounts/xlsx", 
                    "json": "/api/v1/templates/accounts/json"
                },
                "required_fields": ["code", "name", "account_type"],
                "optional_fields": ["category", "parent_code", "description", "is_active", "allows_movements", "requires_third_party", "requires_cost_center", "notes"],
                "example_data": {
                    "code": "1105",
                    "name": "Caja General",
                    "account_type": "ACTIVO",
                    "category": "ACTIVO_CORRIENTE",
                    "parent_code": "1100"
                }
            },
            "journal_entries": {
                "description": "Plantilla para importación de asientos contables",
                "formats": ["csv", "xlsx", "json"], 
                "endpoints": {
                    "csv": "/api/v1/templates/journal-entries/csv",
                    "xlsx": "/api/v1/templates/journal-entries/xlsx",
                    "json": "/api/v1/templates/journal-entries/json"
                },
                "required_fields": ["entry_number", "entry_date", "description", "account_code", "line_description"],
                "conditional_fields": ["debit_amount", "credit_amount"],
                "optional_fields": ["reference", "entry_type", "third_party", "cost_center", "line_reference"],
                "example_data": {
                    "entry_number": "AST-2024-001",
                    "entry_date": "2024-01-15",
                    "description": "Compra de material de oficina",
                    "account_code": "5105",
                    "line_description": "Material de oficina - papelería",
                    "debit_amount": 150000
                }
            }
        },
        "formats_supported": ["csv", "xlsx", "json"],
        "notes": [
            "Las plantillas incluyen datos de ejemplo y documentación",
            "Los archivos XLSX incluyen hojas adicionales con documentación de campos",
            "Para asientos contables, agrupe las líneas por entry_number",
            "Respete los nombres de columnas exactos mostrados en las plantillas",
            "Para importar cuentas use los tipos: ACTIVO, PASIVO, PATRIMONIO, INGRESO, GASTO, COSTOS",
            "Para asientos contables, solo un monto (débito o crédito) debe tener valor por línea"
        ]
    }
