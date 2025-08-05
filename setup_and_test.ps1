# Pipeline Setup and Test Script
# Run this in PowerShell to set up your environment and test the pipeline

Write-Host "🚀 COMPLIANCE AUTOMATION PIPELINE SETUP" -ForegroundColor Cyan
Write-Host "=" * 50

# Check if we're in a virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠️  No virtual environment detected. Activating..." -ForegroundColor Yellow
    & "C:/Users/cyqt2/Database/.venv/Scripts/Activate.ps1"
}

# Check current directory
$currentDir = Get-Location
Write-Host "📂 Current directory: $currentDir"

if ($currentDir.Path -notlike "*overhaul*") {
    Write-Host "📁 Changing to overhaul directory..."
    Set-Location "c:\Users\cyqt2\Database\overhaul"
}

# Check for Ollama service
Write-Host "🤖 Checking Ollama service..." -ForegroundColor Cyan
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "✅ Ollama service is running" -ForegroundColor Green
    Write-Host "📋 Available models:" -ForegroundColor White
    foreach ($model in $ollamaCheck.models) {
        Write-Host "  - $($model.name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Ollama service not accessible" -ForegroundColor Red
    Write-Host "Please ensure Ollama is running with: ollama serve" -ForegroundColor Yellow
}

# Run quick test
Write-Host "`n🧪 Running quick pipeline test..." -ForegroundColor Cyan
python quick_test.py

# Run diagnostics
Write-Host "`n🔍 Running full diagnostics..." -ForegroundColor Cyan
python diagnose_pipeline.py

Write-Host "`n🎯 READY TO TEST!" -ForegroundColor Green
Write-Host "Now you can run:" -ForegroundColor White
Write-Host "  python main.py prompts/debug_oneshot.yaml --analysis_file test_document.txt" -ForegroundColor Cyan
Write-Host "or" -ForegroundColor White
Write-Host "  python main.py prompts/oneshot.yaml --analysis_file test_document.txt" -ForegroundColor Cyan
