# Setup script for Windows PowerShell

Write-Host "🚀 AKS Arc AI Ops Assistant - Setup Script" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Check Python version
Write-Host "📋 Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.11 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Found: $pythonVersion`n" -ForegroundColor Green

# Check Node.js version
Write-Host "📋 Checking Node.js version..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Node.js not found. Please install Node.js 18 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Found: Node.js $nodeVersion`n" -ForegroundColor Green

# Setup backend
Write-Host "🔧 Setting up backend..." -ForegroundColor Yellow
Set-Location backend

# Create virtual environment
if (Test-Path "venv") {
    Write-Host "  ℹ️  Virtual environment already exists" -ForegroundColor Cyan
} else {
    Write-Host "  📦 Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    Write-Host "  ✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "  🔌 Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "  📦 Installing dependencies..." -ForegroundColor Cyan
pip install --upgrade pip | Out-Null
pip install -r requirements-dev.txt

Write-Host "  ✅ Backend setup complete`n" -ForegroundColor Green

# Return to root
Set-Location ..

# Setup frontend
Write-Host "🔧 Setting up frontend..." -ForegroundColor Yellow
Set-Location frontend

Write-Host "  📦 Installing npm packages..." -ForegroundColor Cyan
npm install

Write-Host "  ✅ Frontend setup complete`n" -ForegroundColor Green

# Return to root
Set-Location ..

# Install pre-commit hooks
Write-Host "🔧 Installing pre-commit hooks..." -ForegroundColor Yellow
& backend\venv\Scripts\Activate.ps1
pre-commit install
Write-Host "✅ Pre-commit hooks installed`n" -ForegroundColor Green

# Create .env file if it doesn't exist
if (-not (Test-Path "backend\.env")) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    @"
# Foundry Local Configuration
FOUNDRY_ENDPOINT=http://127.0.0.1:58366
FOUNDRY_MODEL=qwen2.5-0.5b

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Context Buffer
CONTEXT_BUFFER_HOURS=2
MAX_BUFFER_SIZE_MB=500
"@ | Out-File -FilePath "backend\.env" -Encoding UTF8
    Write-Host "✅ .env file created`n" -ForegroundColor Green
} else {
    Write-Host "ℹ️  .env file already exists`n" -ForegroundColor Cyan
}

# Summary
Write-Host "`n✅ Setup Complete!" -ForegroundColor Green
Write-Host "==================`n" -ForegroundColor Green

Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Activate virtual environment:" -ForegroundColor White
Write-Host "     backend\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Run backend (in one terminal):" -ForegroundColor White
Write-Host "     make run-backend" -ForegroundColor Gray
Write-Host "     or: cd backend && uvicorn src.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Run frontend (in another terminal):" -ForegroundColor White
Write-Host "     make run-frontend" -ForegroundColor Gray
Write-Host "     or: cd frontend && npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Test Foundry Local connection:" -ForegroundColor White
Write-Host "     cd backend && python -m src.services.foundry" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Setup k3s cluster:" -ForegroundColor White
Write-Host "     See docs\k3s-setup.md" -ForegroundColor Gray
Write-Host ""

Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "  - Architecture: docs\architecture.md" -ForegroundColor White
Write-Host "  - Development: docs\development.md" -ForegroundColor White
Write-Host "  - Deployment: docs\deployment.md" -ForegroundColor White
Write-Host "  - k3s Setup: docs\k3s-setup.md" -ForegroundColor White
Write-Host ""

Write-Host "🎉 Happy coding!" -ForegroundColor Cyan
