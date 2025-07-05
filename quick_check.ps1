# Script de verificación rápida para el entorno de IA
# Ejecutar con: powershell -ExecutionPolicy Bypass -File quick_check.ps1

Write-Host "🔍 Verificación Rápida - API Contable con IA" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Verificar Python
Write-Host "`n1️⃣ Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion) {
        Write-Host "✅ $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Python no encontrado" -ForegroundColor Red
        Write-Host "   Instalar Python 3.8+ desde https://python.org" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error verificando Python" -ForegroundColor Red
    exit 1
}

# Verificar si existe el entorno virtual
Write-Host "`n2️⃣ Verificando entorno virtual..." -ForegroundColor Yellow
if (Test-Path "venv_ai_chat") {
    Write-Host "✅ Entorno virtual encontrado" -ForegroundColor Green
    
    # Verificar si tiene las dependencias básicas
    Write-Host "`n3️⃣ Verificando dependencias..." -ForegroundColor Yellow
    $pipPath = "venv_ai_chat\Scripts\pip.exe"
    
    if (Test-Path $pipPath) {
        $packages = & $pipPath list 2>$null
        
        $requiredPackages = @("fastapi", "transformers", "torch", "langdetect", "httpx")
        $missing = @()
        
        foreach ($package in $requiredPackages) {
            if ($packages -match $package) {
                Write-Host "✅ $package instalado" -ForegroundColor Green
            } else {
                Write-Host "❌ $package faltante" -ForegroundColor Red
                $missing += $package
            }
        }
        
        if ($missing.Count -gt 0) {
            Write-Host "`n⚠️ Dependencias faltantes: $($missing -join ', ')" -ForegroundColor Yellow
            Write-Host "   Ejecutar: python setup_ai_environment.py" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ pip no encontrado en el entorno virtual" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Entorno virtual no encontrado" -ForegroundColor Red
    Write-Host "   Ejecutar: python setup_ai_environment.py" -ForegroundColor Yellow
}

# Verificar archivos principales
Write-Host "`n4️⃣ Verificando archivos del proyecto..." -ForegroundColor Yellow
$coreFiles = @(
    "app\main.py",
    "app\services\translation.py", 
    "app\services\hf_client.py",
    "app\api\v1\chat.py",
    "requirements.txt"
)

foreach ($file in $coreFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file faltante" -ForegroundColor Red
    }
}

# Verificar configuración
Write-Host "`n5️⃣ Verificando configuración..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ Archivo .env encontrado" -ForegroundColor Green
    
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "HUGGINGFACE_API_TOKEN=hf_exampletoken123") {
        Write-Host "⚠️ Token de Hugging Face es de ejemplo" -ForegroundColor Yellow
        Write-Host "   Configurar token real en .env" -ForegroundColor Yellow
    } elseif ($envContent -match "HUGGINGFACE_API_TOKEN=hf_") {
        Write-Host "✅ Token de Hugging Face configurado" -ForegroundColor Green
    } else {
        Write-Host "❌ Token de Hugging Face no configurado" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Archivo .env no encontrado" -ForegroundColor Red
    Write-Host "   Ejecutar: python setup_ai_environment.py" -ForegroundColor Yellow
}

# Recomendaciones
Write-Host "`n📋 PRÓXIMOS PASOS:" -ForegroundColor Cyan

if (Test-Path "venv_ai_chat") {
    Write-Host "1. Activar entorno: .\activate_ai_env.ps1" -ForegroundColor White
} else {
    Write-Host "1. Configurar entorno: python setup_ai_environment.py" -ForegroundColor White
}

Write-Host "2. Configurar token HF en .env" -ForegroundColor White
Write-Host "3. Verificar servicio: python start_ai_chat.py" -ForegroundColor White
Write-Host "4. Iniciar API: uvicorn app.main:app --reload" -ForegroundColor White

Write-Host "`n🌐 URLs útiles:" -ForegroundColor Cyan
Write-Host "   API: http://localhost:8000" -ForegroundColor White
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Chat Health: http://localhost:8000/api/v1/ai/chat/health" -ForegroundColor White

Write-Host "`n✨ Verificación completada" -ForegroundColor Green
