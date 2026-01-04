# DocTura Desktop - Simple Quick Run
# Just installs and runs - no fancy options

Write-Host "DocTura Desktop - Quick Launcher" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $version = python --version 2>&1
    Write-Host "Found Python: $version" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit 1
}

# Create/activate venv
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install if needed
Write-Host "Installing DocTura..." -ForegroundColor Yellow
pip install -e . --quiet --disable-pip-version-check

# Run
Write-Host ""
Write-Host "Starting DocTura Desktop..." -ForegroundColor Green
Write-Host ""
python -m docutura.app.main
