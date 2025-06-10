"""
Script para ejecutar todos los tests de integración
"""
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path


def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Ejecutando: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.returncode == 0:
            print("✅ ÉXITO")
            if result.stdout:
                print(f"Salida:\n{result.stdout}")
        else:
            print("❌ ERROR")
            if result.stderr:
                print(f"Error:\n{result.stderr}")
            if result.stdout:
                print(f"Salida:\n{result.stdout}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {e}")
        return False


def main():
    """Función principal para ejecutar tests"""
    print("🧪 EJECUTOR DE TESTS DE INTEGRACIÓN - API CONTABLE")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    print(f"📁 Directorio de trabajo: {project_dir}")
    
    # Lista de comandos a ejecutar
    test_commands = [
        {
            "command": "python -m pytest tests/integration/test_auth_endpoints.py -v",
            "description": "Tests de Autenticación"
        },
        {
            "command": "python -m pytest tests/integration/test_user_endpoints.py -v",
            "description": "Tests de Gestión de Usuarios"
        },
        {
            "command": "python -m pytest tests/integration/test_account_endpoints.py -v",
            "description": "Tests de Cuentas Contables"
        },
        {
            "command": "python -m pytest tests/integration/test_journal_entry_endpoints.py -v",
            "description": "Tests de Asientos Contables"
        },
        {
            "command": "python -m pytest tests/integration/test_report_endpoints.py -v",
            "description": "Tests de Reportes Financieros"
        },
        {
            "command": "python -m pytest tests/integration/test_end_to_end_workflow.py -v -s",
            "description": "Tests de Flujo End-to-End"
        }
    ]
    
    # Comandos de cobertura y reportes
    coverage_commands = [
        {
            "command": "python -m pytest tests/integration/ --cov=app --cov-report=term-missing --cov-report=html:htmlcov",
            "description": "Ejecutar todos los tests con cobertura"
        },
        {
            "command": "python -m pytest tests/integration/ --cov=app --cov-report=xml",
            "description": "Generar reporte de cobertura XML"
        }
    ]
    
    # Verificar que pytest esté instalado
    print("\n🔍 Verificando dependencias...")
    check_result = run_command("python -m pytest --version", "Verificar pytest")
    if not check_result:
        print("❌ pytest no está instalado. Instalando...")
        install_result = run_command("pip install pytest pytest-asyncio pytest-cov httpx", "Instalar dependencias")
        if not install_result:
            print("❌ No se pudieron instalar las dependencias")
            return False
    
    # Ejecutar tests individuales
    print("\n" + "="*80)
    print("📋 EJECUTANDO TESTS INDIVIDUALES")
    print("="*80)
    
    results = []
    for test_cmd in test_commands:
        success = run_command(test_cmd["command"], test_cmd["description"])
        results.append({
            "description": test_cmd["description"],
            "success": success
        })
    
    # Ejecutar tests con cobertura
    print("\n" + "="*80)
    print("📊 EJECUTANDO ANÁLISIS DE COBERTURA")
    print("="*80)
    
    coverage_results = []
    for cov_cmd in coverage_commands:
        success = run_command(cov_cmd["command"], cov_cmd["description"])
        coverage_results.append({
            "description": cov_cmd["description"],
            "success": success
        })
    
    # Generar reporte de markdown
    print("\n" + "="*80)
    print("📄 GENERANDO REPORTE")
    print("="*80)
    
    generate_markdown_report(results, coverage_results)
    
    # Resumen final
    print("\n" + "="*80)
    print("📋 RESUMEN FINAL")
    print("="*80)
    
    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)
    
    print(f"✅ Tests exitosos: {successful_tests}/{total_tests}")
    print(f"📊 Cobertura generada: {'✅' if any(r['success'] for r in coverage_results) else '❌'}")
    
    if successful_tests == total_tests:
        print("\n🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        return True
    else:
        print(f"\n⚠️  {total_tests - successful_tests} tests fallaron")
        return False


def generate_markdown_report(test_results, coverage_results):
    """Generar reporte en formato markdown"""
    
    report_content = f"""# Reporte de Tests de Integración

**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Resumen

| Categoría | Estado | Descripción |
|-----------|--------|-------------|
"""
    
    for result in test_results:
        status = "✅ PASÓ" if result["success"] else "❌ FALLÓ"
        report_content += f"| Test | {status} | {result['description']} |\n"
    
    report_content += "\n## Cobertura de Código\n\n"
    
    for result in coverage_results:
        status = "✅ GENERADO" if result["success"] else "❌ ERROR"
        report_content += f"- **{result['description']}**: {status}\n"
    
    report_content += f"""
## Archivos de Tests

### Tests de Integración
- `test_auth_endpoints.py` - Autenticación y autorización
- `test_user_endpoints.py` - Gestión de usuarios
- `test_account_endpoints.py` - Cuentas contables
- `test_journal_entry_endpoints.py` - Asientos contables
- `test_report_endpoints.py` - Reportes financieros
- `test_end_to_end_workflow.py` - Flujos completos

### Configuración
- `conftest.py` - Configuración de pytest y fixtures
- `test_helpers.py` - Utilities y helpers para tests

## Cobertura

Si la generación de cobertura fue exitosa, puedes ver el reporte detallado en:
- **HTML**: `htmlcov/index.html`
- **XML**: `coverage.xml`

## Comandos Útiles

```bash
# Ejecutar todos los tests
python -m pytest tests/integration/ -v

# Ejecutar tests con cobertura
python -m pytest tests/integration/ --cov=app --cov-report=html

# Ejecutar tests específicos
python -m pytest tests/integration/test_auth_endpoints.py -v

# Ejecutar solo tests rápidos
python -m pytest tests/integration/ -m "not slow"
```

---
*Reporte generado automáticamente por run_tests.py*
"""
    
    # Guardar reporte
    report_path = Path("test_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"📄 Reporte guardado en: {report_path.absolute()}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
