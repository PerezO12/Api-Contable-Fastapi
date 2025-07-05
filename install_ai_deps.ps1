# Script para instalar dependencias de IA en Windows
Write-Host "🚀 Instalando dependencias de IA..." -ForegroundColor Green

# Verificar si Python está disponible
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python no encontrado. Instala Python primero." -ForegroundColor Red
    exit 1
}

# Instalar dependencias
$dependencies = @(
    "transformers==4.36.2",
    "torch==2.1.2"
)

foreach ($dep in $dependencies) {
    Write-Host "📦 Instalando $dep..." -ForegroundColor Cyan
    try {
        python -m pip install $dep
        Write-Host "✅ $dep instalado correctamente" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error instalando $dep" -ForegroundColor Red
    }
}

# Verificar instalación
Write-Host "`n🔍 Verificando instalación..." -ForegroundColor Yellow
python -c "
try:
    import transformers, torch, sentencepiece
    print('✅ Todas las dependencias instaladas correctamente')
except ImportError as e:
    print(f'❌ Error: {e}')
"

Write-Host "`n✅ Instalación completada!" -ForegroundColor Green
Write-Host "💡 Ejecuta 'python check_ai_system.py' para diagnóstico completo" -ForegroundColor Cyan
