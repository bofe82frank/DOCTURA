# DocTura Desktop - Run Script
# Quick launcher for Windows PowerShell

param(
    [switch]$Install,
    [switch]$Test,
    [switch]$Clean,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

function Show-Help {
    Write-Host "DocTura Desktop - Run Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\run.ps1           - Run the application (installs if needed)"
    Write-Host "  .\run.ps1 -Install  - Install/reinstall dependencies"
    Write-Host "  .\run.ps1 -Test     - Run test suite"
    Write-Host "  .\run.ps1 -Clean    - Clean virtual environment"
    Write-Host "  .\run.ps1 -Help     - Show this help"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\run.ps1                    # Quick start"
    Write-Host "  .\run.ps1 -Install -Test     # Install and test"
    Write-Host ""
}

function Test-PythonInstalled {
    try {
        $version = python --version 2>&1
        Write-Host "✓ Found Python: $version" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ Python not found. Please install Python 3.10 or higher." -ForegroundColor Red
        Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
        return $false
    }
}

function Initialize-VirtualEnvironment {
    Write-Host "`n=== Setting up Virtual Environment ===" -ForegroundColor Cyan

    $venvPath = Join-Path $ProjectRoot "venv"

    if (Test-Path $venvPath) {
        Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
    } else {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv venv
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
    }

    # Activate virtual environment
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

    if (Test-Path $activateScript) {
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & $activateScript
        Write-Host "✓ Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to find activation script" -ForegroundColor Red
        exit 1
    }
}

function Install-Dependencies {
    Write-Host "`n=== Installing Dependencies ===" -ForegroundColor Cyan

    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip --quiet

    Write-Host "Installing DocTura Desktop..." -ForegroundColor Yellow
    pip install -e . --quiet

    Write-Host "✓ Installation complete" -ForegroundColor Green
}

function Install-DevDependencies {
    Write-Host "`nInstalling development dependencies..." -ForegroundColor Yellow
    pip install pytest pytest-qt --quiet
    Write-Host "✓ Development dependencies installed" -ForegroundColor Green
}

function Run-Tests {
    Write-Host "`n=== Running Tests ===" -ForegroundColor Cyan

    if (-not (Get-Command pytest -ErrorAction SilentlyContinue)) {
        Write-Host "Installing pytest..." -ForegroundColor Yellow
        Install-DevDependencies
    }

    Write-Host "Running test suite..." -ForegroundColor Yellow
    pytest docutura/tests/test_basic.py -v

    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✓ All tests passed!" -ForegroundColor Green
    } else {
        Write-Host "`n✗ Some tests failed" -ForegroundColor Red
    }
}

function Start-Application {
    Write-Host "`n=== Starting DocTura Desktop ===" -ForegroundColor Cyan
    Write-Host "Launching application..." -ForegroundColor Yellow
    Write-Host ""

    python -m docutura.app.main
}

function Remove-VirtualEnvironment {
    Write-Host "`n=== Cleaning Virtual Environment ===" -ForegroundColor Cyan

    $venvPath = Join-Path $ProjectRoot "venv"

    if (Test-Path $venvPath) {
        Write-Host "Removing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Path $venvPath -Recurse -Force
        Write-Host "✓ Virtual environment removed" -ForegroundColor Green
    } else {
        Write-Host "No virtual environment found" -ForegroundColor Yellow
    }
}

# Main execution
Clear-Host
Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      DocTura Desktop - Launcher v1.0      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan

if ($Help) {
    Show-Help
    exit 0
}

# Check Python
if (-not (Test-PythonInstalled)) {
    exit 1
}

# Clean mode
if ($Clean) {
    Remove-VirtualEnvironment
    Write-Host "`n✓ Cleanup complete" -ForegroundColor Green
    exit 0
}

# Initialize environment
Initialize-VirtualEnvironment

# Install mode
if ($Install) {
    Install-Dependencies

    if ($Test) {
        Install-DevDependencies
    }
}

# Test mode
if ($Test) {
    Run-Tests
    exit 0
}

# Check if installed
try {
    python -c "import docutura" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n⚠ DocTura not installed. Installing now..." -ForegroundColor Yellow
        Install-Dependencies
    }
} catch {
    Write-Host "`n⚠ DocTura not installed. Installing now..." -ForegroundColor Yellow
    Install-Dependencies
}

# Run application
Start-Application

Write-Host "`n=== Application Closed ===" -ForegroundColor Cyan
Write-Host "Thank you for using DocTura Desktop!" -ForegroundColor Green
