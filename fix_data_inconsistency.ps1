# PowerShell script to run the journal entry data inconsistency fix
# This script helps identify and fix data inconsistencies in journal entry lines

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("report", "fix")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("keep_payment_terms", "keep_due_date")]
    [string]$Strategy = "keep_payment_terms"
)

# Set the working directory to the project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Journal Entry Data Inconsistency Tool" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Virtual environment not activated. Activating..." -ForegroundColor Yellow
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        & ".\venv\Scripts\Activate.ps1"
    } elseif (Test-Path ".\venv\bin\activate") {
        # For Linux/Mac compatibility if running on WSL
        & ".\venv\bin\activate"
    } else {
        Write-Error "Virtual environment not found. Please create and activate a virtual environment first."
        exit 1
    }
}

try {
    switch ($Action) {
        "report" {
            Write-Host "Generating data inconsistency report..." -ForegroundColor Green
            python fix_journal_entry_data_inconsistency.py report
        }
        "fix" {
            Write-Host "Fixing data inconsistencies using strategy: $Strategy" -ForegroundColor Green
            Write-Host ""
            Write-Host "WARNING: This will modify data in the database!" -ForegroundColor Red
            Write-Host "Make sure you have a backup before proceeding." -ForegroundColor Red
            Write-Host ""
            
            $confirmation = Read-Host "Do you want to continue? (y/N)"
            if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
                python fix_journal_entry_data_inconsistency.py fix $Strategy
            } else {
                Write-Host "Operation cancelled." -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Error "An error occurred: $_"
    exit 1
}

Write-Host ""
Write-Host "Operation completed." -ForegroundColor Green
