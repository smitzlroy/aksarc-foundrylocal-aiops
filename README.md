# AKS Arc + Foundry Local AI Ops Assistant

A professional-grade AI Operations Assistant for Azure AKS Arc clusters, powered by Azure AI Foundry Local.

## Overview

This project provides a natural language interface for Kubernetes operators to interact with their AKS Arc clusters. All AI processing happens locally via Azure AI Foundry Local, ensuring no cloud dependency for inference.

**Key Differentiator**: Unlike cloud-based solutions, this assistant runs entirely on-premises or at the edge, making it ideal for disconnected environments, high-security scenarios, and cost-sensitive deployments.

## Key Features

### Week 1 MVP Features

- ✅ **Project Foundation**: Complete tooling, linting, testing infrastructure
- 🔄 **Natural Language Q&A**: Ask questions about your cluster in plain English
- 🔄 **Real-time Monitoring**: Watches logs, events, and metrics from Kubernetes
- 🔄 **Local AI Processing**: All AI inference via Azure AI Foundry Local (qwen2.5-0.5b)
- 🔄 **Modern Web UI**: Clean, responsive chat interface with status cards
- 🔄 **Production-Ready Code**: Type hints, tests, structured logging throughout
- 🔄 **Easy Deployment**: Helm chart for deployment to any Kubernetes cluster

### Explicitly Out of Scope (Week 1)

- ❌ Historical data storage (database)
- ❌ Predictions/forecasting
- ❌ Multi-cluster support
- ❌ User authentication
- ❌ Complex dashboards
- ❌ CLI tool

## Architecture

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   React UI   │────────▶│   FastAPI    │────────▶│  Kubernetes  │
│  (Port 3000) │ WS/HTTP │  (Port 8000) │  K8s API│   Cluster    │
└──────────────┘         └──────┬───────┘         └──────────────┘
                                │
                                │ HTTP
                                ▼
                         ┌──────────────┐
                         │ Foundry Local│
                         │ (Port 58366) │
                         │ qwen2.5-0.5b │
                         └──────────────┘
```

- **Backend**: Python 3.11+ with FastAPI, async/await, structured logging
- **Frontend**: React 18 + TypeScript (strict mode) with Vite and Tailwind CSS
- **AI**: Azure AI Foundry Local with qwen2.5-0.5b model
- **Deployment**: Helm chart for Kubernetes (k3s local, AKS Arc production)
- **Data**: In-memory buffer (last 2 hours of cluster data)

## Prerequisites

### Required

- **Python 3.11+**: Backend development
- **Node.js 18+**: Frontend development
- **Azure AI Foundry Local**: Running at http://127.0.0.1:58366
- **Docker Desktop** or **k3s**: Local Kubernetes cluster
- **kubectl**: Kubernetes CLI configured
- **Git**: Version control

### Recommended

- **Make**: Build automation (Windows: choco install make)
- **VS Code**: IDE with Python and TypeScript extensions
- **k9s**: Terminal-based Kubernetes UI

## Quick Start

### 1. Clone and Setup

```powershell
# Clone repository
git clone https://github.com/smitzlroy/aksarc-foundrylocal-aiops.git
cd aksarc-foundrylocal-aiops

# Run automated setup (Windows)
.\setup.ps1

# Or manual setup
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cd ..\frontend
npm install
```

### 2. Configure Environment

The setup script creates `backend\.env` with defaults. Verify Foundry endpoint:

```env
FOUNDRY_ENDPOINT=http://127.0.0.1:58366
FOUNDRY_MODEL=qwen2.5-0.5b
```

### 3. Test Foundry Connection

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m src.services.foundry
```

You should see connection tests pass.

### 4. Run Backend

```powershell
# Terminal 1
cd backend
.\venv\Scripts\Activate.ps1
uvicorn src.main:app --reload

# Or using Make
make run-backend
```

Backend runs at http://localhost:8000

### 5. Run Frontend

```powershell
# Terminal 2
cd frontend
npm run dev
```

Frontend runs at http://localhost:3000

### 6. Setup Local Kubernetes

See detailed guide: [docs/k3s-setup.md](docs/k3s-setup.md)

**Quick k3d setup:**

```powershell
# Install k3d (if not installed)
choco install k3d

# Create cluster
k3d cluster create aiops-dev --port 8000:8000@loadbalancer

# Verify
kubectl get nodes
```

## Project Structure

```
aksarc-foundrylocal-aiops/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── api/               # HTTP and WebSocket routes
│   │   ├── core/              # Config, logging, exceptions
│   │   ├── models/            # Pydantic data models
│   │   ├── services/          # K8s, Foundry, context services
│   │   └── main.py            # FastAPI application
│   ├── tests/                 # Unit and integration tests
│   ├── requirements.txt       # Production dependencies
│   ├── requirements-dev.txt   # Development dependencies
│   ├── pyproject.toml         # Python tooling config
│   └── Dockerfile             # Container image
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API clients
│   │   ├── types/             # TypeScript types
│   │   └── App.tsx            # Root component
│   ├── package.json           # Node dependencies
│   ├── tsconfig.json          # TypeScript config (strict)
│   └── vite.config.ts         # Vite bundler config
├── helm/                       # Helm chart for deployment
├── docs/                       # Documentation
│   ├── architecture.md        # System architecture
│   ├── development.md         # Development guide
│   ├── deployment.md          # Deployment guide
│   └── k3s-setup.md           # k3s setup instructions
├── Makefile                    # Build automation
├── setup.ps1                   # Automated setup script
└── README.md                   # This file
```

## Development Workflow

### Code Quality Standards

This project has **strict quality requirements**:

- ✅ **Type hints required** on all Python functions
- ✅ **Docstrings required** (Google style)
- ✅ **Error handling required** (no bare exceptions)
- ✅ **Logging required** (structured JSON logs)
- ✅ **Tests required** (80%+ coverage)
- ✅ **TypeScript strict mode** (no 'any' types)

### Pre-commit Checks

Pre-commit hooks automatically run:

- **black**: Python code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **pylint**: Code linting
- **prettier**: Frontend formatting

### Common Commands

```powershell
# Run all tests
make test

# Format all code
make format

# Run all linters
make lint

# Type check
make type-check

# Clean build artifacts
make clean

# Run pre-commit hooks
make pre-commit
```

## Documentation

Comprehensive documentation is available:

- **[Architecture](docs/architecture.md)**: System design, data flow, component details
- **[Development](docs/development.md)**: Setup, coding standards, testing strategy
- **[Deployment](docs/deployment.md)**: Local and production deployment guides
- **[k3s Setup](docs/k3s-setup.md)**: Local Kubernetes cluster setup

## Current Status

🚧 **Week 1 MVP - Foundation Complete** 🚧

**Completed:**
- ✅ Complete project structure
- ✅ Backend tooling (black, isort, mypy, pylint, pytest)
- ✅ Frontend tooling (ESLint, Prettier, TypeScript strict)
- ✅ Foundry Local client with validation
- ✅ Core configuration and logging
- ✅ Data models for cluster state and chat
- ✅ Comprehensive documentation
- ✅ Makefile and setup scripts

**In Progress:**
- 🔄 Kubernetes watcher implementation
- 🔄 Context buffer implementation
- 🔄 REST API endpoints
- 🔄 WebSocket chat streaming
- 🔄 React UI components
- 🔄 Helm chart
- 🔄 Integration tests

**Next Steps:**
1. Implement Kubernetes watcher service
2. Build context buffer with circular buffer
3. Create REST API endpoints
4. Implement WebSocket streaming
5. Build React chat UI components
6. Create Helm chart
7. End-to-end testing

## Testing

```powershell
# Run all tests with coverage
cd backend
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/unit/test_api_basic.py -v

# View coverage report
# Open htmlcov/index.html in browser
```

## Contributing

This is currently a personal project. Contribution guidelines will be added in future releases.

### Development Principles

- **Quality over speed**: Code must be production-grade
- **Test everything**: No untested code
- **Document thoroughly**: Code should be self-explanatory
- **Type everything**: Leverage Python and TypeScript type systems
- **Log strategically**: Structured logging for observability

## License

*(License information to be added)*

## Troubleshooting

### Backend won't start

```powershell
# Ensure virtual environment is activated
backend\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements-dev.txt
```

### Foundry connection fails

```powershell
# Test Foundry is running
curl http://127.0.0.1:58366

# Run connection test
python -m src.services.foundry
```

### Frontend build errors

```powershell
# Clear cache and reinstall
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

## Contact

**Repository**: [github.com/smitzlroy/aksarc-foundrylocal-aiops](https://github.com/smitzlroy/aksarc-foundrylocal-aiops)

**Author**: smitzlroy

---

*Built with ❤️ for Kubernetes operators who need local AI assistance*
