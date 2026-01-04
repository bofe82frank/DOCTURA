# Quick PDF test script - handles venv automatically

param(
    [Parameter(Mandatory=$false)]
    [string]$PdfPath = "Working_Documents\Computer_Studies_TASS_And_CASS_Statistics.pdf"
)

Write-Host "DocTura PDF Conversion Test" -ForegroundColor Cyan
Write-Host "Testing: $PdfPath" -ForegroundColor Yellow
Write-Host ""

# Use venv Python
$pythonExe = ".\venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: .\run-simple.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Run test
& $pythonExe test_conversion.py $PdfPath
