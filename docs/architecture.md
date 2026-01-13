# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                          │
├──────────────────────┬──────────────────────────────────────────┤
│   Web UI (React)     │         CLI Tool (Python)               │
│   Port: 3000         │         Command Line Interface          │
└──────────┬───────────┴──────────────────┬──────────────────────┘
           │                               │
           │ HTTP/WebSocket                │ Direct API
           │                               │
┌──────────▼───────────────────────────────▼──────────────────────┐
│                    FastAPI Backend (Python)                      │
│                         Port: 8000                               │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ API Routes  │  │  WebSocket   │  │  Context Manager       │ │
│  │  /api/*     │  │   /ws        │  │  (In-Memory Buffer)    │ │
│  └─────────────┘  └──────────────┘  └────────────────────────┘ │
└───┬──────────────────────┬──────────────────────┬───────────────┘
    │                      │                      │
    │                      │                      │
┌───▼──────────────┐  ┌───▼────────────┐  ┌─────▼─────────────┐
│  Kubernetes      │  │  Foundry Local │  │  Context Service  │
│  Watcher Service │  │  AI Service    │  │  (Data Buffer)    │
├──────────────────┤  ├────────────────┤  ├───────────────────┤
│ - Watch Pods     │  │ - Query Model  │  │ - Last 2hr data   │
│ - Watch Events   │  │ - Generate     │  │ - Logs buffer     │
│ - Watch Logs     │  │   Responses    │  │ - Events buffer   │
│ - Collect        │  │ - Context      │  │ - Metrics buffer  │
│   Metrics        │  │   Injection    │  │                   │
└───┬──────────────┘  └────────────────┘  └───────────────────┘
    │                         │
    │                         │
┌───▼─────────────────────────▼──────────────────────────────────┐
│                    External Systems                             │
├─────────────────────────────┬───────────────────────────────────┤
│  Kubernetes Cluster         │   Azure AI Foundry Local          │
│  (k3s local / AKS Arc)      │   http://127.0.0.1:58366          │
│  - Pods, Deployments        │   Model: qwen2.5-0.5b             │
│  - Services, Events         │                                   │
│  - Logs, Metrics            │                                   │
└─────────────────────────────┴───────────────────────────────────┘
```

## Component Descriptions

### Frontend (React + TypeScript)

**Purpose:** Provides a modern, responsive web interface for interacting with the AI assistant.

**Key Features:**
- Single-page application with real-time updates
- Chat interface for natural language queries
- Status cards showing cluster health metrics
- WebSocket connection for real-time streaming responses
- Neon/vibrant color scheme inspired by Azure Arc Jumpstart

**Technology Stack:**
- React 18 with TypeScript (strict mode)
- Vite for fast development and optimized builds
- Tailwind CSS for styling
- WebSocket API for real-time communication

### Backend (FastAPI + Python)

**Purpose:** Orchestrates data collection, AI processing, and API services.

**Key Components:**

#### 1. API Layer (`src/api/`)
- **routes.py**: REST endpoints for cluster info, health checks
- **websocket.py**: WebSocket handler for streaming chat responses

#### 2. Core Layer (`src/core/`)
- **config.py**: Application configuration using Pydantic
- **logging.py**: Structured logging setup with JSON formatting
- **exceptions.py**: Custom exception classes

#### 3. Services Layer (`src/services/`)
- **kubernetes.py**: Kubernetes client wrapper, watches pods/events/logs
- **context.py**: In-memory data buffer (last 2 hours of cluster data)
- **foundry.py**: Azure AI Foundry Local integration

#### 4. Models Layer (`src/models/`)
- **cluster.py**: Data models for cluster state (pods, events, metrics)
- **chat.py**: Data models for chat requests/responses

### Kubernetes Watcher Service

**Purpose:** Continuously monitors the Kubernetes cluster and collects relevant data.

**Watches:**
- Pod status changes
- Events (warnings, errors)
- Container logs (streaming)
- Basic metrics (CPU, memory usage)

**Data Retention:**
- In-memory buffer storing last 2 hours of data
- Circular buffer implementation to prevent memory growth
- Data indexed by timestamp for fast queries

### Context Service

**Purpose:** Manages the in-memory data buffer and provides context for AI queries.

**Responsibilities:**
- Store recent cluster data (2-hour rolling window)
- Index data by resource type, namespace, timestamp
- Provide fast retrieval for AI context injection
- Implement efficient data structures for quick lookups

**Data Types Stored:**
- Pod states and status changes
- Events (system events, warnings, errors)
- Log snippets (error logs, recent logs)
- Basic metrics (CPU/memory usage)

### Foundry Local AI Service

**Purpose:** Interfaces with Azure AI Foundry Local for natural language processing.

**Responsibilities:**
- Send queries to local Foundry endpoint (http://127.0.0.1:58366)
- Inject relevant cluster context into prompts
- Stream responses back to frontend via WebSocket
- Handle model errors and retries

**Model Configuration:**
- Model: qwen2.5-0.5b (lightweight, fast)
- Temperature: 0.7 (balanced creativity/accuracy)
- Max tokens: 2048
- Context window: ~4000 tokens

## Data Flow

### Query Processing Flow

```
1. User enters question in Web UI
   ↓
2. WebSocket message sent to backend
   ↓
3. Backend parses query and extracts intent
   ↓
4. Context Service retrieves relevant cluster data
   ↓
5. Foundry Service injects context into prompt
   ↓
6. Query sent to Foundry Local (qwen2.5-0.5b)
   ↓
7. Response streamed back through WebSocket
   ↓
8. Web UI displays response in real-time
```

### Data Collection Flow

```
1. Kubernetes Watcher establishes watches
   ↓
2. Cluster events/logs stream to watcher
   ↓
3. Data normalized and timestamped
   ↓
4. Context Service stores in circular buffer
   ↓
5. Old data (>2 hours) automatically evicted
   ↓
6. Data indexed for fast retrieval
```

## Deployment Architecture

### Local Development (k3s)

```
┌─────────────────────────────────────────┐
│       Windows 11 Laptop                 │
│  ┌─────────────────────────────────┐   │
│  │  WSL2 / Docker Desktop          │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │  k3s Cluster              │  │   │
│  │  │  - Single node            │  │   │
│  │  │  - Local development      │  │   │
│  │  └───────────────────────────┘  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Azure AI Foundry Local                 │
│  http://127.0.0.1:58366                 │
│                                         │
│  AI Ops Assistant Backend               │
│  http://localhost:8000                  │
│                                         │
│  Frontend Dev Server                    │
│  http://localhost:3000                  │
└─────────────────────────────────────────┘
```

### Production (AKS Arc)

```
┌──────────────────────────────────────────────┐
│         AKS Arc Cluster                      │
│  ┌────────────────────────────────────────┐ │
│  │  Namespace: aiops-assistant            │ │
│  │  ┌──────────────┐  ┌─────────────┐    │ │
│  │  │  Backend Pod │  │ Frontend    │    │ │
│  │  │  (FastAPI)   │  │ (Static)    │    │ │
│  │  └──────────────┘  └─────────────┘    │ │
│  │                                        │ │
│  │  ServiceAccount with RBAC             │ │
│  │  (read pods, events, logs)            │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
         │
         │ Queries Foundry Local endpoint
         │ (must be accessible from cluster)
         ▼
┌──────────────────────────────────────────────┐
│  Azure AI Foundry Local                      │
│  (Deployed on-premises or edge)              │
└──────────────────────────────────────────────┘
```

## Security Considerations

### Week 1 MVP (Simplified Security)

- **No authentication**: Open access for local development
- **RBAC**: ServiceAccount with minimal required permissions
- **Network**: Backend only accessible within cluster
- **Secrets**: Foundry endpoint configured via environment variables

### Future Enhancements (Post-MVP)

- Implement user authentication (Azure AD integration)
- Add TLS/HTTPS for all communications
- Implement query rate limiting
- Add audit logging for all queries
- Secure WebSocket connections
- Implement namespace-scoped permissions

## Performance Considerations

### Memory Management

- **In-memory buffer**: Limited to 2 hours of data
- **Circular buffer**: Automatic eviction of old data
- **Indexing**: Fast lookups by timestamp, namespace, resource type
- **Estimated memory**: ~500MB for typical cluster (100 pods)

### Query Performance

- **Context retrieval**: <100ms for typical queries
- **Foundry inference**: ~1-3 seconds (depends on query complexity)
- **Streaming**: Real-time response streaming via WebSocket
- **Concurrent queries**: Supports multiple simultaneous users

### Scaling Considerations

- **Single replica**: Week 1 MVP runs single backend pod
- **Stateless design**: Easy to scale horizontally in future
- **Shared context**: Future enhancement with Redis/shared cache
- **Load testing**: Target 10 concurrent users for MVP

## Technology Choices - Rationale

### Why FastAPI?
- Async/await support for concurrent operations
- Automatic API documentation (OpenAPI/Swagger)
- Built-in WebSocket support
- Excellent performance for Python framework
- Type hints and Pydantic integration

### Why React + TypeScript?
- Strong typing prevents runtime errors
- Component-based architecture for maintainability
- Large ecosystem and community support
- Excellent developer experience with Vite

### Why In-Memory Buffer (vs. Database)?
- Simpler implementation for MVP
- Lower latency for recent data access
- No database setup/maintenance required
- Adequate for 2-hour rolling window
- Easy to replace with persistent storage later

### Why Foundry Local (vs. Cloud AI)?
- Zero cloud dependency for inference
- Lower latency (local processing)
- Cost-effective (no API charges)
- Data privacy (stays on-premises)
- Suitable for edge/disconnected scenarios

## Future Architecture Enhancements

### Post-Week 1 Considerations

1. **Persistent Storage**
   - Add PostgreSQL/TimescaleDB for historical data
   - Enable trend analysis and predictions

2. **Multi-Cluster Support**
   - Aggregate data from multiple clusters
   - Centralized AI assistant

3. **Advanced Features**
   - Anomaly detection
   - Predictive alerts
   - Automated remediation suggestions

4. **Scalability**
   - Redis for shared context cache
   - Horizontal pod autoscaling
   - Load balancing for high availability
