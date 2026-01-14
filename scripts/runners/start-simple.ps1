# Simple Server Start Script
# Use this if start.ps1 has issues with k3d

Write-Host "🚀 Starting AKS Arc AI Ops Server..." -ForegroundColor Cyan
Write-Host ""

# Set Python path
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verify kubectl
Write-Host "✅ Checking Kubernetes..." -ForegroundColor Yellow
$nodes = kubectl get nodes --no-headers 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Kubernetes accessible ($($nodes.Count) nodes)" -ForegroundColor Green
} else {
    Write-Host "❌ Cannot access Kubernetes" -ForegroundColor Red
    Write-Host "   Run: k3d cluster start aiops-dev" -ForegroundColor Yellow
    exit 1
}

# Start server
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📖 Quick Test:" -ForegroundColor Yellow
Write-Host "   1. Open: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "   2. Double-click: dashboard.html" -ForegroundColor Gray
Write-Host "   3. Run: .\test-interactive.ps1 (in new terminal)" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

Push-Location "$PSScriptRoot\backend"
python run.py
Pop-Location
