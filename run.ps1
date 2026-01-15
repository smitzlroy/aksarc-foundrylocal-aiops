#!/usr/bin/env pwsh
# K8s AI Assistant - Quick Start
# Usage: .\run.ps1

Write-Host ""
Write-Host "🤖 " -NoNewline -ForegroundColor Cyan
Write-Host "K8s AI Assistant" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

# Check Kubernetes
Write-Host "🔍 Checking Kubernetes..." -ForegroundColor Yellow
$k8sOk = (kubectl cluster-info 2>$null) -and ($LASTEXITCODE -eq 0)
if (-not $k8sOk) {
    Write-Host "❌ Kubernetes not accessible" -ForegroundColor Red
    Write-Host "   Please start your cluster first" -ForegroundColor DarkGray
    exit 1
}
Write-Host "✅ Kubernetes connected" -ForegroundColor Green

# Start server
Write-Host ""
Write-Host "🚀 Starting server..." -ForegroundColor Cyan
Write-Host "   URL: " -NoNewline -ForegroundColor DarkGray
Write-Host "http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor DarkGray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""

# Change to backend directory and run
Set-Location "$PSScriptRoot\backend"

# Verify Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ Python not found" -ForegroundColor Red
    Write-Host "   Please install Python 3.11+ from python.org" -ForegroundColor DarkGray
    exit 1
}

# Run the server
python run.py
