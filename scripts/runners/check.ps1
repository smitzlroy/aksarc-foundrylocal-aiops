#!/usr/bin/env pwsh
# Quick verification script - Run this to verify everything is ready

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  QUICK SYSTEM CHECK" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if server is running
Write-Host "1. Server Status..." -NoNewline
$serverRunning = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object {$_.State -eq 'Listen'}
if ($serverRunning) {
    Write-Host " ✅ RUNNING (PID: $($serverRunning.OwningProcess))" -ForegroundColor Green
} else {
    Write-Host " ❌ NOT RUNNING" -ForegroundColor Red
    Write-Host "`n  Run this to start: .\run.ps1`n" -ForegroundColor Yellow
    exit 1
}

# Check critical endpoints
Write-Host "2. API Endpoints..." -ForegroundColor White

$endpoints = @(
    @{Name="Homepage"; Url="http://localhost:8000/"},
    @{Name="Platform Detection"; Url="http://localhost:8000/api/platform/detect"},
    @{Name="Cluster Status"; Url="http://localhost:8000/api/cluster/status"},
    @{Name="Network Topology"; Url="http://localhost:8000/api/topology/analyze"},
    @{Name="AKS Arc Check"; Url="http://localhost:8000/api/aksarc/diagnostics/check"}
)

$allGood = $true
foreach ($ep in $endpoints) {
    Write-Host "   - $($ep.Name)..." -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $ep.Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host " ✅" -ForegroundColor Green
    } catch {
        Write-Host " ❌" -ForegroundColor Red
        $allGood = $false
    }
}

# Check AI Model status
Write-Host "3. AI Model Status..." -NoNewline
try {
    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/foundry/status" -UseBasicParsing
    if ($status.running) {
        Write-Host " ✅ Running ($($status.selected_model))" -ForegroundColor Green
    } else {
        Write-Host " ⏸️  Not started (user can start from UI)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " ❌ Cannot check" -ForegroundColor Red
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "  STATUS: ✅ ALL SYSTEMS GO!" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Cyan
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "  1. Open browser: http://localhost:8000" -ForegroundColor White
    Write-Host "  2. Press Ctrl+F5 to refresh" -ForegroundColor White
    Write-Host "  3. Click '🗺️ Topology' to test new features" -ForegroundColor White
    Write-Host "  4. Start AI model from UI if needed`n" -ForegroundColor White
} else {
    Write-Host "  STATUS: ⚠️  SOME ISSUES FOUND" -ForegroundColor Yellow
    Write-Host "========================================`n" -ForegroundColor Cyan
    Write-Host "Try restarting the server:`n  .\run.ps1`n" -ForegroundColor Yellow
}
