.PHONY: help setup setup-backend setup-frontend install-dev clean test test-backend test-frontend lint lint-backend lint-frontend format format-backend format-frontend type-check run-backend run-frontend run docker-build docker-run pre-commit

# Default target
help:
	@echo "AKS Arc AI Ops Assistant - Development Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup              - Full setup (backend + frontend)"
	@echo "  make setup-backend      - Setup Python backend environment"
	@echo "  make setup-frontend     - Setup Node.js frontend environment"
	@echo "  make install-dev        - Install development dependencies"
	@echo ""
	@echo "Development Commands:"
	@echo "  make run-backend        - Run backend server"
	@echo "  make run-frontend       - Run frontend dev server"
	@echo "  make run                - Run both backend and frontend"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  make test               - Run all tests"
	@echo "  make test-backend       - Run backend tests with coverage"
	@echo "  make lint               - Run all linters"
	@echo "  make lint-backend       - Run Python linters"
	@echo "  make format             - Format all code"
	@echo "  make format-backend     - Format Python code"
	@echo "  make type-check         - Run mypy type checking"
	@echo "  make pre-commit         - Run pre-commit hooks"
	@echo ""
	@echo "Cleanup Commands:"
	@echo "  make clean              - Remove build artifacts and caches"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build       - Build Docker image"
	@echo "  make docker-run         - Run Docker container"

# Setup targets
setup: setup-backend setup-frontend
	@echo "✅ Full setup complete!"

setup-backend:
	@echo "🔧 Setting up Python backend..."
	cd backend && python -m venv venv
	@echo "⚠️  Activate venv manually:"
	@echo "   Windows: backend\\venv\\Scripts\\Activate.ps1"
	@echo "   Linux/Mac: source backend/venv/bin/activate"
	@echo "Then run: make install-dev"

setup-frontend:
	@echo "🔧 Setting up Node.js frontend..."
	cd frontend && npm install
	@echo "✅ Frontend setup complete!"

install-dev:
	@echo "📦 Installing development dependencies..."
	cd backend && pip install -r requirements-dev.txt
	pre-commit install
	@echo "✅ Development dependencies installed!"

# Run targets
run-backend:
	@echo "🚀 Starting backend server..."
	cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "🚀 Starting frontend dev server..."
	cd frontend && npm run dev

run:
	@echo "🚀 Starting both backend and frontend..."
	@echo "⚠️  Run these in separate terminals:"
	@echo "   Terminal 1: make run-backend"
	@echo "   Terminal 2: make run-frontend"

# Testing targets
test: test-backend
	@echo "✅ All tests passed!"

test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && pytest tests/ -v --cov=src --cov-report=term-missing

# Linting targets
lint: lint-backend
	@echo "✅ All linting passed!"

lint-backend:
	@echo "🔍 Running Python linters..."
	cd backend && black --check src/ tests/
	cd backend && isort --check-only src/ tests/
	cd backend && pylint src/
	cd backend && flake8 src/ tests/

# Formatting targets
format: format-backend
	@echo "✅ All code formatted!"

format-backend:
	@echo "✨ Formatting Python code..."
	cd backend && black src/ tests/
	cd backend && isort src/ tests/

# Type checking
type-check:
	@echo "🔍 Running mypy type checking..."
	cd backend && mypy src/

# Pre-commit
pre-commit:
	@echo "🔍 Running pre-commit hooks..."
	pre-commit run --all-files

# Cleanup targets
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf dist/ node_modules/.cache/ 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Docker targets
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t aksarc-aiops-assistant:latest -f backend/Dockerfile .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 -e FOUNDRY_ENDPOINT=http://host.docker.internal:58366 aksarc-aiops-assistant:latest
