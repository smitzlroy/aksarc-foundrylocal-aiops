# Stop AIOps Server
# This script stops all Python processes running the AIOps server

Write-Host "⏹️  Stopping AIOps Server..." -ForegroundColor Cyan

$processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*run.py*"
}

if ($processes) {
    $processes | ForEach-Object {
        Write-Host "   Stopping process $($_.Id)..." -ForegroundColor Yellow
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "✅ Server stopped" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No running server found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📖 To start the server again, run: .\start-service.ps1" -ForegroundColor Cyan
