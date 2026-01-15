# Start AIOps Server as Background Service
# This script starts the server in a hidden window that runs in the background

$scriptPath = "c:\AI\aksarc-foundrylocal-aiops\backend"
$pythonScript = "run.py"

Write-Host "🚀 Starting AIOps Server in background..." -ForegroundColor Cyan

# Kill any existing Python processes running run.py
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*run.py*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

# Start the server in a hidden window
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "python"
$processInfo.Arguments = $pythonScript
$processInfo.WorkingDirectory = $scriptPath
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$processInfo.CreateNoWindow = $true
$processInfo.UseShellExecute = $false

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processInfo
$process.Start() | Out-Null

Write-Host "✅ Server started (PID: $($process.Id))" -ForegroundColor Green
Write-Host ""
Write-Host "📖 Server Access:" -ForegroundColor Cyan
Write-Host "   Web UI:  http://localhost:8080/" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8080/docs" -ForegroundColor White
Write-Host ""
Write-Host "⏹️  To stop the server, run: .\stop-service.ps1" -ForegroundColor Yellow
Write-Host ""

# Wait a few seconds and verify it's running
Start-Sleep -Seconds 8

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Server is responding! Status: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Server may still be starting... Give it a few more seconds." -ForegroundColor Yellow
    Write-Host "   Check http://localhost:8080/ in your browser." -ForegroundColor White
}
