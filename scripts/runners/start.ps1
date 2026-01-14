#!/usr/bin/env pwsh
# AKS Arc AI Operations Assistant - Start Server

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AKS Arc AI Operations Assistant" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory and change to backend
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"

Write-Host "Changing to backend directory..." -ForegroundColor Yellow
Set-Location $BackendDir

# Verify run.py exists
if (-not (Test-Path "run.py")) {
    Write-Host "ERROR: Cannot find run.py in $BackendDir" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Refresh PATH to find Python
Write-Host "Refreshing PATH..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verify Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    Write-Host "Please install Python 3.11 or later" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the server
Write-Host ""
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python run.py
