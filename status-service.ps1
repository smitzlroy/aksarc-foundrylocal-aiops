# Check AIOps Server Status
# This script checks if the server is running

Write-Host "🔍 Checking AIOps Server Status..." -ForegroundColor Cyan
Write-Host ""

# Check Python processes
$processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*run.py*"
}

if ($processes) {
    Write-Host "✅ Server Process Running:" -ForegroundColor Green
    $processes | ForEach-Object {
        Write-Host "   PID: $($_.Id) | CPU: $([math]::Round($_.CPU, 2))s | Memory: $([math]::Round($_.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor White
    }
} else {
    Write-Host "❌ Server process not found" -ForegroundColor Red
}

Write-Host ""

# Check if port 8080 is listening
$port = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue

if ($port) {
    Write-Host "✅ Port 8080 is listening" -ForegroundColor Green
} else {
    Write-Host "❌ Port 8080 is not listening" -ForegroundColor Red
}

Write-Host ""

# Try to hit the API
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ API Health Check:" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor White
    Write-Host "   Kubernetes: $($response.services.kubernetes)" -ForegroundColor White
    Write-Host "   Context Buffer: $($response.services.context_buffer)" -ForegroundColor White
    Write-Host "   Foundry: $($response.services.foundry)" -ForegroundColor White
    Write-Host ""
    Write-Host "✅ Server is fully operational!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📖 Access Points:" -ForegroundColor Cyan
    Write-Host "   Web UI:  http://localhost:8080/" -ForegroundColor White
    Write-Host "   API Docs: http://localhost:8080/docs" -ForegroundColor White
} catch {
    Write-Host "❌ API is not responding" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
}
