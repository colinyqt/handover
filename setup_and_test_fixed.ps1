# Pipeline Setup and Test Script
# Run this in PowerShell to set up your environment and test the pipeline

Write-Host "🚀 COMPLIANCE AUTOMATION PIPELINE SETUP" -ForegroundColor Cyan
Write-Host ("=" * 50)

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

# Check for OpenAI API Key
if ($env:OPENAI_API_KEY) {
    Write-Host "✅ OpenAI API key is set" -ForegroundColor Green
} else {
    Write-Host "⚠️  OpenAI API key not found!" -ForegroundColor Yellow
    Write-Host "Please set your API key:" -ForegroundColor Yellow
    Write-Host '$env:OPENAI_API_KEY = "your-api-key-here"' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or for this session only:" -ForegroundColor Yellow
    Write-Host 'Set-Item -Path env:OPENAI_API_KEY -Value "your-api-key-here"' -ForegroundColor Cyan
    Write-Host ""
    
    # Prompt for API key
    $apiKey = Read-Host "Enter your OpenAI API key (or press Enter to skip)"
    if ($apiKey) {
        $env:OPENAI_API_KEY = $apiKey
        Write-Host "✅ API key set for this session" -ForegroundColor Green
    }
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
