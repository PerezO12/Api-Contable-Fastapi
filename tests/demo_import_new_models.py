#!/usr/bin/env python3
"""
Script de ejemplo para demostrar la importación genérica de nuevos modelos:
- Centros de Costo
- Diarios Contables
- Términos de Pago

Este script muestra cómo usar la API de importación genérica
"""
import requests
import json
import time
import csv
import io
from typing import Dict, Any


class GenericImportDemo:
    """Demostración de importación genérica para nuevos modelos"""
    
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if auth_token:
            self.session.headers.update({'Authorization': f'Bearer {auth_token}'})
    
    def get_available_models(self) -> list:
        """Obtener lista de modelos disponibles"""
        response = self.session.get(f"{self.base_url}/api/v1/generic-import/models")
        response.raise_for_status()
        return response.json()
    
    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """Obtener metadatos de un modelo específico"""
        response = self.session.get(f"{self.base_url}/api/v1/generic-import/models/{model_name}/metadata")
        response.raise_for_status()
        return response.json()
    
    def create_import_session(self, model_name: str, csv_data: str) -> Dict[str, Any]:
        """Crear sesión de importación con datos CSV"""
        files = {
            'file': ('test_data.csv', io.StringIO(csv_data), 'text/csv')
        }
        data = {
            'model_name': model_name
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/generic-import/sessions",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_preview(self, session_token: str, column_mappings: list) -> Dict[str, Any]:
        """Obtener vista previa con validaciones"""
        payload = {
            "import_session_token": session_token,
            "column_mappings": column_mappings,
            "preview_rows": 10
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/generic-import/preview",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def execute_import(self, session_token: str, column_mappings: list) -> Dict[str, Any]:
        """Ejecutar importación"""
        payload = {
            "import_session_token": session_token,
            "column_mappings": column_mappings,
            "import_policy": "upsert",
            "options": {
                "batch_size": 100,
                "continue_on_error": True
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/generic-import/execute",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def demo_cost_centers(self):
        """Demostración de importación de centros de costo"""
        print("=== DEMOSTRACIÓN: IMPORTACIÓN DE CENTROS DE COSTO ===")
        
        # Datos de ejemplo para centros de costo
        csv_data = """code,name,description,parent_code,manager_name,is_active
ADM,Administración,Centro administrativo,,Juan Pérez,true
VEN,Ventas,Centro de ventas,,María García,true
VEN-NAC,Ventas Nacionales,Ventas del mercado nacional,VEN,Carlos López,true
VEN-INT,Ventas Internacionales,Ventas internacionales,VEN,Ana Martínez,true
PROD,Producción,Centro de producción,,Luis Rodríguez,true"""
        
        try:
            # 1. Obtener metadatos del modelo
            print("\n1. Obteniendo metadatos del modelo...")
            metadata = self.get_model_metadata("cost_center")
            print(f"Campos disponibles: {[f['internal_name'] for f in metadata['fields']]}")
            
            # 2. Crear sesión de importación
            print("\n2. Creando sesión de importación...")
            session = self.create_import_session("cost_center", csv_data)
            print(f"Sesión creada: {session['import_session_token'][:20]}...")
            print(f"Columnas detectadas: {[col['name'] for col in session['detected_columns']]}")
            
            # 3. Configurar mapeo de columnas
            print("\n3. Configurando mapeo de columnas...")
            column_mappings = [
                {"column_name": "code", "field_name": "code"},
                {"column_name": "name", "field_name": "name"},
                {"column_name": "description", "field_name": "description"},
                {"column_name": "parent_code", "field_name": "parent_code"},
                {"column_name": "manager_name", "field_name": "manager_name"},
                {"column_name": "is_active", "field_name": "is_active"}
            ]
            
            # 4. Vista previa con validaciones
            print("\n4. Obteniendo vista previa...")
            preview = self.get_preview(session['import_session_token'], column_mappings)
            print(f"Filas válidas: {preview['validation_summary']['valid_rows']}")
            print(f"Filas con errores: {preview['validation_summary']['rows_with_errors']}")
            
            if preview['validation_summary']['rows_with_errors'] > 0:
                print("Errores encontrados:")
                for row in preview['preview_data']:
                    if row['errors']:
                        print(f"  Fila {row['row_number']}: {[e['message'] for e in row['errors']]}")
            
            # 5. Ejecutar importación si no hay errores críticos
            if preview['can_proceed']:
                print("\n5. Ejecutando importación...")
                result = self.execute_import(session['import_session_token'], column_mappings)
                print(f"Estado: {result['status']}")
                print(f"Registros creados: {result['execution_summary']['successful_operations']['created']}")
                print(f"Registros actualizados: {result['execution_summary']['successful_operations']['updated']}")
                if result['execution_summary']['failed_operations']['total'] > 0:
                    print(f"Operaciones fallidas: {result['execution_summary']['failed_operations']['total']}")
            else:
                print("\n❌ No se puede proceder debido a errores críticos")
                
        except requests.RequestException as e:
            print(f"Error en la solicitud: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
    
    def demo_journals(self):
        """Demostración de importación de diarios contables"""
        print("\n=== DEMOSTRACIÓN: IMPORTACIÓN DE DIARIOS CONTABLES ===")
        
        # Datos de ejemplo para diarios
        csv_data = """name,code,type,sequence_prefix,description
Diario de Ventas,VEN,sale,VEN,Para registrar todas las ventas
Diario de Compras,COM,purchase,COM,Para registrar todas las compras
Diario de Caja,CAJ,cash,CAJ,Para movimientos de efectivo
Diario Banco Principal,BAN,bank,BAN,Para movimientos bancarios"""
        
        try:
            print("\n1. Creando sesión de importación...")
            session = self.create_import_session("journal", csv_data)
            
            column_mappings = [
                {"column_name": "name", "field_name": "name"},
                {"column_name": "code", "field_name": "code"},
                {"column_name": "type", "field_name": "type"},
                {"column_name": "sequence_prefix", "field_name": "sequence_prefix"},
                {"column_name": "description", "field_name": "description"}
            ]
            
            print("\n2. Obteniendo vista previa...")
            preview = self.get_preview(session['import_session_token'], column_mappings)
            print(f"Validación: {preview['validation_summary']['valid_rows']} válidas, {preview['validation_summary']['rows_with_errors']} con errores")
            
            if preview['can_proceed']:
                print("\n3. Ejecutando importación...")
                result = self.execute_import(session['import_session_token'], column_mappings)
                print(f"✅ Importación completada: {result['execution_summary']['successful_operations']['created']} diarios creados")
            
        except Exception as e:
            print(f"Error: {e}")
    
    def demo_payment_terms(self):
        """Demostración de importación de términos de pago"""
        print("\n=== DEMOSTRACIÓN: IMPORTACIÓN DE TÉRMINOS DE PAGO ===")
        
        # Datos de ejemplo para términos de pago
        csv_data = """code,name,payment_schedule_days,payment_schedule_percentages,payment_schedule_descriptions
CONT,Contado,0,100.0,Pago inmediato
30D,30 Días,30,100.0,Pago a 30 días
30-60,30/60 Días,"30,60","50.0,50.0",Primera cuota|Segunda cuota
TRIM,Trimestral,"30,60,90","33.33,33.33,33.34",Mes 1|Mes 2|Mes 3"""
        
        try:
            print("\n1. Creando sesión de importación...")
            session = self.create_import_session("payment_terms", csv_data)
            
            column_mappings = [
                {"column_name": "code", "field_name": "code"},
                {"column_name": "name", "field_name": "name"},
                {"column_name": "payment_schedule_days", "field_name": "payment_schedule_days"},
                {"column_name": "payment_schedule_percentages", "field_name": "payment_schedule_percentages"},
                {"column_name": "payment_schedule_descriptions", "field_name": "payment_schedule_descriptions"}
            ]
            
            print("\n2. Obteniendo vista previa...")
            preview = self.get_preview(session['import_session_token'], column_mappings)
            print(f"Validación: {preview['validation_summary']['valid_rows']} válidas, {preview['validation_summary']['rows_with_errors']} con errores")
            
            # Mostrar detalles de validación para términos de pago
            for row in preview['preview_data']:
                if row['validation_status'] == 'valid':
                    print(f"  ✅ Fila {row['row_number']}: {row['transformed_data']['code']} - {row['transformed_data']['name']}")
                elif row['errors']:
                    print(f"  ❌ Fila {row['row_number']}: {[e['message'] for e in row['errors']]}")
            
            if preview['can_proceed']:
                print("\n3. Ejecutando importación...")
                result = self.execute_import(session['import_session_token'], column_mappings)
                print(f"✅ Importación completada: {result['execution_summary']['successful_operations']['created']} términos de pago creados")
            
        except Exception as e:
            print(f"Error: {e}")
    
    def run_full_demo(self):
        """Ejecutar demostración completa"""
        print("🚀 DEMOSTRACIÓN COMPLETA DE IMPORTACIÓN GENÉRICA - NUEVOS MODELOS")
        print("=" * 80)
        
        try:
            # Mostrar modelos disponibles
            print("\n📋 Modelos disponibles:")
            models = self.get_available_models()
            for model in models:
                print(f"  - {model}")
            
            # Verificar que los nuevos modelos están disponibles
            new_models = ["cost_center", "journal", "payment_terms"]
            available_new_models = [m for m in new_models if m in models]
            
            if len(available_new_models) < len(new_models):
                missing = set(new_models) - set(available_new_models)
                print(f"\n⚠️  Modelos no disponibles: {missing}")
                print("Asegúrese de que el servidor esté actualizado con los nuevos modelos")
                return
            
            print(f"\n✅ Todos los nuevos modelos están disponibles: {available_new_models}")
            
            # Ejecutar demostraciones
            self.demo_cost_centers()
            time.sleep(1)  # Pausa entre demostraciones
            
            self.demo_journals()
            time.sleep(1)
            
            self.demo_payment_terms()
            
            print("\n" + "=" * 80)
            print("🎉 DEMOSTRACIÓN COMPLETADA")
            print("Los nuevos modelos han sido integrados exitosamente al sistema de importación genérica")
            
        except Exception as e:
            print(f"\n❌ Error en la demostración: {e}")
            print("Verifique que el servidor esté ejecutándose y que tenga los permisos necesarios")


def main():
    """Función principal"""
    print("Demostración de Importación Genérica - Nuevos Modelos")
    print("=" * 60)
    
    # Configurar la demostración
    # Nota: Ajustar la URL base y token según el entorno
    base_url = "http://localhost:8000"
    auth_token: str | None = None  # Agregar token de autenticación si es necesario
    
    demo = GenericImportDemo(base_url, auth_token)
    
    # Ejecutar demostración completa
    demo.run_full_demo()


if __name__ == "__main__":
    main()
