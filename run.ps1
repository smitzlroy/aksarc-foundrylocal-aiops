#!/usr/bin/env pwsh
# K8s AI Assistant - One-Click Start
# Just run: .\run.ps1

Write-Host ""
Write-Host "🤖 " -NoNewline -ForegroundColor Cyan
Write-Host "K8s AI Assistant" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""

# 1. Check Foundry Local
Write-Host "🔍 Checking Foundry Local..." -ForegroundColor Yellow
try {
    $foundryCheck = foundry model list 2>&1 | Out-String
    if ($foundryCheck -match 'Service is Started on (http://[^,]+)') {
        $endpoint = $Matches[1]
        Write-Host "✅ Foundry running: $endpoint" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Foundry not running - you can start it from the UI" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Foundry CLI not found. Chat features will be limited." -ForegroundColor Yellow
    Write-Host "   Install: https://learn.microsoft.com/azure/ai-foundry/foundry-local/get-started" -ForegroundColor DarkGray
}

Write-Host ""

# 2. Check Kubernetes
Write-Host "🔍 Checking Kubernetes..." -ForegroundColor Yellow
try {
    $nodes = kubectl get nodes --no-headers 2>&1
    if ($LASTEXITCODE -eq 0) {
        $nodeCount = ($nodes | Measure-Object).Count
        Write-Host "✅ K8s cluster connected ($nodeCount nodes)" -ForegroundColor Green
    } else {
        Write-Host "❌ Cannot connect to Kubernetes cluster" -ForegroundColor Red
        Write-Host "   Make sure kubectl is configured and cluster is running" -ForegroundColor DarkGray
        exit 1
    }
} catch {
    Write-Host "❌ kubectl not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 3. Start Server
Write-Host "🚀 Starting server..." -ForegroundColor Cyan
Write-Host ""

# Change to backend directory
$BackendDir = Join-Path $PSScriptRoot "backend"
Set-Location $BackendDir

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Python not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Python not found" -ForegroundColor Red
    exit 1
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "✨ Server starting on " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "   UI will open in your browser shortly..." -ForegroundColor Yellow
Write-Host ""
Write-Host "   Press Ctrl+C to stop" -ForegroundColor DarkGray
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""

# Run the server (blocking)
python run.py
