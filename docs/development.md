# Development Guide

## Prerequisites

### Required Software

- **Python 3.11+**: Backend development
- **Node.js 18+**: Frontend development
- **kubectl**: Kubernetes command-line tool
- **Docker Desktop** or **WSL2 with k3s**: Local Kubernetes cluster
- **Azure AI Foundry Local**: Running at http://127.0.0.1:58366
- **Git**: Version control
- **Make**: Build automation (optional but recommended)

### Recommended Tools

- **VS Code**: IDE with Python and TypeScript extensions
- **Postman** or **Thunder Client**: API testing
- **K9s**: Terminal-based Kubernetes UI
- **kubectx/kubens**: Kubernetes context/namespace management

## Initial Setup

### 1. Clone and Setup Backend

```bash
# Clone repository
git clone https://github.com/smitzlroy/aksarc-foundrylocal-aiops.git
cd aksarc-foundrylocal-aiops

# Create Python virtual environment
cd backend
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 2. Setup Frontend

```bash
# From project root
cd frontend

# Install dependencies
npm install
```

### 3. Configure Environment

Create `.env` file in `backend/` directory:

```env
# Foundry Local Configuration
FOUNDRY_ENDPOINT=http://127.0.0.1:58366
FOUNDRY_MODEL=qwen2.5-0.5b

# Kubernetes Configuration (optional, uses default kubeconfig)
# KUBECONFIG=/path/to/kubeconfig

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Context Buffer Configuration
CONTEXT_BUFFER_HOURS=2
MAX_BUFFER_SIZE_MB=500
```

## Development Workflow

### Using Make Commands

The project includes a comprehensive Makefile for common tasks:

```bash
# View all available commands
make help

# Setup everything
make setup

# Install development dependencies
make install-dev

# Run backend server
make run-backend

# Run frontend dev server (in separate terminal)
make run-frontend

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Type check
make type-check

# Clean build artifacts
make clean
```

### Manual Commands

If you prefer not to use Make:

#### Backend

```bash
cd backend

# Activate virtual environment first
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows

# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Format code
black src/ tests/
isort src/ tests/

# Lint code
pylint src/
mypy src/
```

#### Frontend

```bash
cd frontend

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint

# Format
npm run format

# Type check
npm run type-check
```

## Project Structure Deep Dive

### Backend Structure

```
backend/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py            # HTTP endpoints
│   │   └── websocket.py         # WebSocket handlers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic settings
│   │   ├── logging.py           # Structured logging setup
│   │   └── exceptions.py        # Custom exceptions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── kubernetes.py        # K8s client and watchers
│   │   ├── context.py           # In-memory data buffer
│   │   └── foundry.py           # Foundry Local client
│   └── models/
│       ├── __init__.py
│       ├── cluster.py           # Cluster data models
│       └── chat.py              # Chat request/response models
├── tests/
│   ├── unit/                    # Unit tests
│   │   ├── test_services/
│   │   ├── test_models/
│   │   └── test_core/
│   └── integration/             # Integration tests
│       └── test_api/
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml               # Python project config + tool settings
└── Dockerfile                   # Container image definition
```

### Frontend Structure

```
frontend/
├── src/
│   ├── main.tsx                 # Application entry point
│   ├── App.tsx                  # Root component
│   ├── index.css                # Global styles (Tailwind)
│   ├── components/              # Reusable UI components
│   │   ├── Chat/
│   │   ├── StatusCards/
│   │   ├── ClusterInfo/
│   │   └── ErrorBoundary/
│   ├── hooks/                   # Custom React hooks
│   │   ├── useWebSocket.ts
│   │   ├── useClusterData.ts
│   │   └── useChat.ts
│   ├── services/                # API clients
│   │   ├── api.ts
│   │   └── websocket.ts
│   └── types/                   # TypeScript type definitions
│       ├── cluster.ts
│       ├── chat.ts
│       └── api.ts
├── package.json                 # Node dependencies and scripts
├── tsconfig.json                # TypeScript configuration
├── vite.config.ts               # Vite bundler configuration
├── tailwind.config.js           # Tailwind CSS configuration
└── index.html                   # HTML entry point
```

## Code Standards

### Python Code Standards

#### Type Hints (Required)

```python
# ✅ Good
def process_pod_event(event: dict[str, Any]) -> PodStatus:
    """Process a pod event and return status."""
    ...

# ❌ Bad
def process_pod_event(event):
    ...
```

#### Docstrings (Required - Google Style)

```python
def query_foundry(prompt: str, context: ClusterContext) -> str:
    """Send a query to Foundry Local with cluster context.

    Args:
        prompt: User's natural language question
        context: Current cluster state and relevant data

    Returns:
        AI-generated response text

    Raises:
        FoundryConnectionError: If unable to connect to Foundry
        FoundryTimeoutError: If query exceeds timeout threshold
    """
    ...
```

#### Error Handling (Required)

```python
# ✅ Good
try:
    response = await foundry_client.query(prompt)
except httpx.TimeoutException as e:
    logger.error("Foundry query timeout", exc_info=e)
    raise FoundryTimeoutError("Query timed out") from e
except httpx.RequestError as e:
    logger.error("Foundry connection error", exc_info=e)
    raise FoundryConnectionError("Unable to connect") from e

# ❌ Bad
try:
    response = await foundry_client.query(prompt)
except Exception:
    pass  # Silent failure
```

#### Logging (Required - Structured)

```python
import structlog

logger = structlog.get_logger(__name__)

# ✅ Good
logger.info(
    "pod_status_changed",
    pod_name=pod.name,
    namespace=pod.namespace,
    old_status=old_status,
    new_status=new_status,
)

# ❌ Bad
print(f"Pod {pod.name} changed from {old_status} to {new_status}")
```

### TypeScript Code Standards

#### No 'any' Types

```typescript
// ✅ Good
interface ClusterStatus {
  healthy: boolean
  podCount: number
  errorCount: number
}

function renderStatus(status: ClusterStatus): JSX.Element {
  ...
}

// ❌ Bad
function renderStatus(status: any) {
  ...
}
```

#### Props Interfaces

```typescript
// ✅ Good
interface ChatMessageProps {
  message: string
  timestamp: Date
  isUser: boolean
  onRetry?: () => void
}

function ChatMessage({ message, timestamp, isUser, onRetry }: ChatMessageProps): JSX.Element {
  ...
}
```

#### Error Boundaries

```typescript
// Required for all major component trees
class ErrorBoundary extends React.Component<Props, State> {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('Component error:', error, errorInfo)
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return <ErrorFallback />
    }
    return this.props.children
  }
}
```

## Testing Strategy

### Backend Testing

#### Unit Tests

Test individual functions and classes in isolation:

```python
# tests/unit/test_services/test_context.py
import pytest
from src.services.context import ContextBuffer

def test_context_buffer_add_event():
    """Test adding events to context buffer."""
    buffer = ContextBuffer(max_hours=2)
    event = {"type": "Warning", "message": "Pod failed"}
    
    buffer.add_event(event)
    
    events = buffer.get_recent_events()
    assert len(events) == 1
    assert events[0]["message"] == "Pod failed"
```

#### Integration Tests

Test API endpoints and service interactions:

```python
# tests/integration/test_api/test_chat.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_chat_websocket(client):
    """Test WebSocket chat endpoint."""
    with client.websocket_connect("/ws/chat") as websocket:
        websocket.send_json({"message": "What pods are running?"})
        response = websocket.receive_json()
        assert "response" in response
```

#### Test Coverage Requirements

- **Minimum coverage**: 80% for all code
- **Critical paths**: 95%+ coverage (authentication, data processing)
- **Run coverage**: `pytest --cov=src --cov-report=html`

### Frontend Testing

(To be implemented in future phases)

## Debugging

### Backend Debugging

#### VS Code Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "FOUNDRY_ENDPOINT": "http://127.0.0.1:58366"
      }
    }
  ]
}
```

#### Using ipdb

```python
import ipdb

def problematic_function():
    # ... code ...
    ipdb.set_trace()  # Debugger will stop here
    # ... more code ...
```

### Frontend Debugging

- Use React DevTools browser extension
- Use browser's built-in debugger
- Check console for errors and warnings
- Use `console.log()` strategically (remove before committing)

## Common Development Tasks

### Adding a New API Endpoint

1. Define request/response models in `backend/src/models/`
2. Implement endpoint in `backend/src/api/routes.py`
3. Add tests in `backend/tests/integration/test_api/`
4. Update API client in `frontend/src/services/api.ts`
5. Run `make test` and `make lint`

### Adding a New React Component

1. Create component file in `frontend/src/components/`
2. Define props interface
3. Implement component with proper error handling
4. Add loading states
5. Import and use in parent component
6. Run `npm run lint` and `npm run type-check`

### Modifying Kubernetes Watcher

1. Update watcher logic in `backend/src/services/kubernetes.py`
2. Update data models if needed in `backend/src/models/cluster.py`
3. Update context buffer in `backend/src/services/context.py`
4. Add unit tests for new functionality
5. Test with local k3s cluster

## Troubleshooting

### Backend Issues

**Issue**: Import errors after installing dependencies
```bash
# Solution: Ensure virtual environment is activated
source backend/venv/bin/activate  # Linux/Mac
.\backend\venv\Scripts\Activate.ps1  # Windows
```

**Issue**: Cannot connect to Kubernetes cluster
```bash
# Solution: Check kubeconfig is valid
kubectl cluster-info
kubectl get nodes
```

**Issue**: Foundry Local connection errors
```bash
# Solution: Verify Foundry Local is running
curl http://127.0.0.1:58366/health  # or appropriate health endpoint
```

### Frontend Issues

**Issue**: Port 3000 already in use
```bash
# Solution: Change port in vite.config.ts or kill process
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Issue**: Module not found errors
```bash
# Solution: Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Pre-commit Hook Failures

**Issue**: Black formatting failures
```bash
# Solution: Run black manually to fix
cd backend
black src/ tests/
```

**Issue**: Mypy type checking failures
```bash
# Solution: Add type hints or type ignore comments
cd backend
mypy src/  # See specific errors
```

## Git Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch (future)
- `feature/*`: Feature branches (future)

For Week 1 MVP, commit directly to `main` with proper commit messages.

### Commit Message Format

Use conventional commits:

```
feat: add WebSocket support for streaming chat
fix: resolve pod watcher memory leak
docs: update architecture documentation
test: add integration tests for context buffer
chore: update dependencies
refactor: simplify Foundry client error handling
```

### Pre-commit Checklist

- [ ] All tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] No linting errors (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Manual testing completed
- [ ] Documentation updated if needed

## Performance Tips

### Backend Performance

- Use async/await for I/O operations
- Implement connection pooling for Kubernetes client
- Use efficient data structures in context buffer
- Profile code with `cProfile` for bottlenecks

### Frontend Performance

- Use React.memo for expensive components
- Implement virtualization for long lists
- Lazy load components with React.lazy
- Optimize bundle size with code splitting

## Next Steps

Once development environment is set up:

1. Run backend: `make run-backend`
2. Run frontend: `make run-frontend`
3. Verify connectivity to Foundry Local
4. Set up local k3s cluster (see k3s-setup.md)
5. Begin implementing core features
