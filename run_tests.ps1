# Script de PowerShell para ejecutar tests de integración
# Uso: .\run_tests.ps1

param(
    [string]$TestFile = "",
    [switch]$Coverage = $false,
    [switch]$Verbose = $false,
    [switch]$Help = $false
)

# Mostrar ayuda
if ($Help) {
    Write-Host @"
🧪 SCRIPT DE TESTS DE INTEGRACIÓN - API CONTABLE

USO:
    .\run_tests.ps1 [opciones]

OPCIONES:
    -TestFile <archivo>    Ejecutar archivo específico de tests
    -Coverage             Generar reporte de cobertura
    -Verbose              Salida detallada
    -Help                 Mostrar esta ayuda

EJEMPLOS:
    .\run_tests.ps1                                              # Todos los tests
    .\run_tests.ps1 -Coverage                                    # Con cobertura
    .\run_tests.ps1 -TestFile test_auth_endpoints.py            # Test específico
    .\run_tests.ps1 -TestFile test_end_to_end_workflow.py -Verbose  # Test E2E verbose

ARCHIVOS DE TESTS DISPONIBLES:
    - test_auth_endpoints.py
    - test_user_endpoints.py  
    - test_account_endpoints.py
    - test_journal_entry_endpoints.py
    - test_report_endpoints.py
    - test_end_to_end_workflow.py
"@
    exit 0
}

Write-Host "🧪 EJECUTOR DE TESTS DE INTEGRACIÓN - API CONTABLE" -ForegroundColor Cyan
Write-Host "📅 Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# Verificar que estamos en el directorio correcto
if (!(Test-Path "app") -or !(Test-Path "tests")) {
    Write-Host "❌ Error: Debes ejecutar este script desde el directorio raíz del proyecto" -ForegroundColor Red
    Write-Host "   Directorio actual: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "   Busca el directorio que contiene las carpetas 'app' y 'tests'" -ForegroundColor Yellow
    exit 1
}

Write-Host "📁 Directorio: $(Get-Location)" -ForegroundColor Green

# Verificar que Python y pytest estén disponibles
Write-Host "`n🔍 Verificando dependencias..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python no está instalado o no está en el PATH" -ForegroundColor Red
    exit 1
}

try {
    $pytestVersion = python -m pytest --version 2>&1
    Write-Host "✅ Pytest disponible" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Pytest no encontrado. Instalando dependencias..." -ForegroundColor Yellow
    python -m pip install pytest pytest-asyncio pytest-cov httpx
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error instalando dependencias" -ForegroundColor Red
        exit 1
    }
}

# Función para ejecutar comando y mostrar resultado
function Invoke-TestCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "🚀 $Description" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    Write-Host "Ejecutando: $Command" -ForegroundColor Gray
    
    $startTime = Get-Date
    
    try {
        Invoke-Expression $Command
        $success = $LASTEXITCODE -eq 0
        
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        if ($success) {
            Write-Host "✅ ÉXITO ($('{0:mm}:{0:ss}' -f $duration))" -ForegroundColor Green
        } else {
            Write-Host "❌ ERROR ($('{0:mm}:{0:ss}' -f $duration))" -ForegroundColor Red
        }
        
        return $success
    } catch {
        Write-Host "❌ EXCEPCIÓN: $_" -ForegroundColor Red
        return $false
    }
}

# Definir comandos de test
$testCommands = @(
    @{
        Command = "python -m pytest tests/integration/test_auth_endpoints.py -v"
        Description = "Tests de Autenticación"
    },
    @{
        Command = "python -m pytest tests/integration/test_user_endpoints.py -v"
        Description = "Tests de Gestión de Usuarios"
    },
    @{
        Command = "python -m pytest tests/integration/test_account_endpoints.py -v"
        Description = "Tests de Cuentas Contables"
    },
    @{
        Command = "python -m pytest tests/integration/test_journal_entry_endpoints.py -v"
        Description = "Tests de Asientos Contables"
    },
    @{
        Command = "python -m pytest tests/integration/test_report_endpoints.py -v"
        Description = "Tests de Reportes Financieros"
    },
    @{
        Command = "python -m pytest tests/integration/test_end_to_end_workflow.py -v -s"
        Description = "Tests de Flujo End-to-End"
    }
)

# Ejecutar tests específicos o todos
$results = @()

if ($TestFile) {
    # Ejecutar archivo específico
    $verboseFlag = if ($Verbose) { "-v -s" } else { "-v" }
    $command = "python -m pytest tests/integration/$TestFile $verboseFlag"
    $success = Invoke-TestCommand -Command $command -Description "Test específico: $TestFile"
    $results += @{ Description = $TestFile; Success = $success }
} else {
    # Ejecutar todos los tests
    Write-Host "`n$('='*80)" -ForegroundColor Magenta
    Write-Host "📋 EJECUTANDO TESTS INDIVIDUALES" -ForegroundColor Magenta
    Write-Host "$('='*80)" -ForegroundColor Magenta
    
    foreach ($testCmd in $testCommands) {
        $success = Invoke-TestCommand -Command $testCmd.Command -Description $testCmd.Description
        $results += @{ Description = $testCmd.Description; Success = $success }
    }
}

# Ejecutar con cobertura si se solicita
if ($Coverage) {
    Write-Host "`n$('='*80)" -ForegroundColor Magenta
    Write-Host "📊 EJECUTANDO ANÁLISIS DE COBERTURA" -ForegroundColor Magenta
    Write-Host "$('='*80)" -ForegroundColor Magenta
    
    $coverageCommand = "python -m pytest tests/integration/ --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml"
    $coverageSuccess = Invoke-TestCommand -Command $coverageCommand -Description "Análisis de cobertura completo"
    
    if ($coverageSuccess) {
        Write-Host "`n📊 Reportes de cobertura generados:" -ForegroundColor Green
        Write-Host "   📄 HTML: htmlcov/index.html" -ForegroundColor Yellow
        Write-Host "   📄 XML:  coverage.xml" -ForegroundColor Yellow
        
        # Abrir reporte HTML si existe
        if (Test-Path "htmlcov/index.html") {
            $openReport = Read-Host "`n¿Abrir reporte de cobertura HTML? (y/N)"
            if ($openReport -eq "y" -or $openReport -eq "Y") {
                Start-Process "htmlcov/index.html"
            }
        }
    }
}

# Generar resumen final
Write-Host "`n$('='*80)" -ForegroundColor Magenta
Write-Host "📋 RESUMEN FINAL" -ForegroundColor Magenta
Write-Host "$('='*80)" -ForegroundColor Magenta

$successfulTests = ($results | Where-Object { $_.Success }).Count
$totalTests = $results.Count

Write-Host "📊 Resultados detallados:" -ForegroundColor Cyan
foreach ($result in $results) {
    $status = if ($result.Success) { "✅" } else { "❌" }
    Write-Host "   $status $($result.Description)" -ForegroundColor $(if ($result.Success) { "Green" } else { "Red" })
}

Write-Host "`n📈 Resumen:" -ForegroundColor Cyan
Write-Host "   ✅ Tests exitosos: $successfulTests/$totalTests" -ForegroundColor Green
Write-Host "   📊 Cobertura: $(if ($Coverage) { '✅ Generada' } else { '⏭️  No solicitada' })" -ForegroundColor Yellow

if ($successfulTests -eq $totalTests) {
    Write-Host "`n🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!" -ForegroundColor Green
    $exitCode = 0
} else {
    Write-Host "`n⚠️  $($totalTests - $successfulTests) tests fallaron" -ForegroundColor Red
    $exitCode = 1
}

# Generar reporte markdown
$reportPath = "test_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
$reportContent = @"
# Reporte de Tests de Integración

**Fecha:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
**Comando ejecutado:** $($MyInvocation.Line)

## Resumen

| Categoría | Estado | Descripción |
|-----------|--------|-------------|
"@

foreach ($result in $results) {
    $status = if ($result.Success) { "✅ PASÓ" } else { "❌ FALLÓ" }
    $reportContent += "`n| Test | $status | $($result.Description) |"
}

$reportContent += @"

## Estadísticas

- **Total de tests:** $totalTests
- **Tests exitosos:** $successfulTests
- **Tests fallidos:** $($totalTests - $successfulTests)
- **Porcentaje de éxito:** $([math]::Round(($successfulTests / $totalTests) * 100, 2))%

## Archivos de Tests

- `test_auth_endpoints.py` - Autenticación y autorización
- `test_user_endpoints.py` - Gestión de usuarios  
- `test_account_endpoints.py` - Cuentas contables
- `test_journal_entry_endpoints.py` - Asientos contables
- `test_report_endpoints.py` - Reportes financieros
- `test_end_to_end_workflow.py` - Flujos completos end-to-end

## Comandos Útiles

```powershell
# Ejecutar todos los tests
.\run_tests.ps1

# Ejecutar con cobertura
.\run_tests.ps1 -Coverage

# Ejecutar test específico
.\run_tests.ps1 -TestFile test_auth_endpoints.py

# Test específico con verbose
.\run_tests.ps1 -TestFile test_end_to_end_workflow.py -Verbose
```

---
*Reporte generado automáticamente por run_tests.ps1*
"@

$reportContent | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "`n📄 Reporte guardado en: $reportPath" -ForegroundColor Yellow

Write-Host "`n🔗 Enlaces útiles:" -ForegroundColor Cyan
Write-Host "   📚 Documentación de tests: tests/README.md" -ForegroundColor Yellow
Write-Host "   🐛 Si hay errores, revisa: test_report_*.md" -ForegroundColor Yellow

exit $exitCode
