# K8s AI Assistant - Project Overview

## Executive Summary

The K8s AI Assistant is a web-based tool that provides intelligent Kubernetes cluster management through natural language queries. It combines real-time cluster monitoring with optional AI-powered insights using Microsoft's Foundry Local SDK, offering both immediate value (Direct Mode) and enhanced capabilities (AI Mode) for DevOps teams managing Kubernetes environments.

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser (UI)                          │
│                    Dark-themed Single Page App                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/WebSocket
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   FastAPI Backend (Python)                       │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────────────┐ │
│  │   API Routes │  │  K8s Client │  │  Foundry SDK Manager   │ │
│  │              │  │             │  │                        │ │
│  │ /chat/query  │──│ Pod Status  │  │  Model Lifecycle      │ │
│  │ /foundry/*   │  │ Node Info   │  │  OpenAI Client        │ │
│  │ /cluster/*   │  │ Events      │  │  Query Handler        │ │
│  └──────────────┘  └─────────────┘  └────────────────────────┘ │
└────────────────────────┬────────────────────────┬───────────────┘
                         │                        │
                         │                        │
              ┌──────────▼──────────┐  ┌──────────▼──────────────┐
              │  Kubernetes Cluster │  │  Foundry Local Service  │
              │                     │  │                         │
              │  • Pods             │  │  • LLM Runtime         │
              │  • Nodes            │  │  • Model Cache         │
              │  • Services         │  │  • OpenAI API          │
              │  • Events           │  │                         │
              └─────────────────────┘  └─────────────────────────┘
```

---

## Technical Stack

### Frontend
- **Pure HTML/CSS/JavaScript** - No framework dependencies for maximum portability
- **Dark theme UI** - Modern, professional design with gradient backgrounds
- **Real-time updates** - Polling mechanism for cluster status (30-second intervals)
- **Responsive layout** - Grid-based design adapting to different screen sizes

### Backend
- **FastAPI (Python 3.11+)** - High-performance async web framework
- **Kubernetes Python Client** - Official kubernetes library for cluster interaction
- **Foundry Local SDK** - Microsoft's official SDK for local LLM management
- **OpenAI SDK** - Standard interface for model queries
- **Structured Logging** - JSON-formatted logs for production monitoring

### Dependencies
```python
fastapi==0.115.5          # Web framework
uvicorn==0.32.1           # ASGI server
kubernetes==31.0.0        # K8s client
foundry-local-sdk==0.5.1  # Microsoft Foundry SDK
openai==2.15.0            # LLM query interface
structlog==24.4.0         # Structured logging
```

---

## Core Components Explained

### 1. Dual-Mode Operation

#### Direct Mode (Keyword Matching)
**How it works:**
- User query arrives at `/api/chat/query` endpoint
- Backend checks if Foundry is running
- If NOT running: Uses pattern matching on keywords
- Retrieves real-time K8s cluster data
- Returns formatted response based on keyword detection

**Example Flow:**
```
User: "show me all pods"
  → Keyword detected: "pod"
  → Fetch all pods from K8s API
  → Format: "Running Pods (7): pod-1, pod-2, pod-3..."
  → Return to user (instant response)
```

**Code Implementation:**
```python
# backend/src/api/routes.py
msg_lower = request.message.lower()
status = await k8s_client.get_cluster_status()

if "pod" in msg_lower:
    running = [p for p in status.pods if p.phase.value == "Running"]
    response = f"**Running Pods ({len(running)}):**\n"
    for pod in running[:10]:
        response += f"• {pod.name} ({pod.namespace}) - {pod.node}\n"
```

**Advantages:**
- ✅ Works immediately, no setup required
- ✅ Zero latency (milliseconds response time)
- ✅ No model download (saves 500MB - 8GB disk space)
- ✅ Perfect for scripted/repetitive queries

**Limitations:**
- ❌ Fixed patterns only (can't handle complex questions)
- ❌ No learning or adaptation
- ❌ Basic formatting, no insights

---

#### AI Mode (Foundry Local with LLM)
**How it works:**
- User query arrives at `/api/chat/query` endpoint
- Backend checks if Foundry is running
- If RUNNING: Sends query to local LLM via Foundry SDK
- Model receives full cluster context (pods, nodes, events)
- LLM generates natural language response
- Returns AI-powered insights to user

**Example Flow:**
```
User: "which pods are restarting frequently and why?"
  → Foundry Status: RUNNING (qwen2.5-1.5b loaded)
  → Build context:
     CURRENT CLUSTER STATE:
     - pod-1: 15 restarts (last: OOMKilled)
     - pod-2: 3 restarts (last: CrashLoopBackOff)
  → Send to LLM with system prompt
  → LLM analyzes: "pod-1 has memory issues (OOMKilled), 
     pod-2 has application crash (CrashLoopBackOff)..."
  → Return rich analysis to user
```

**Code Implementation:**
```python
# backend/src/services/foundry_manager.py
async def query_model(self, message: str, system_prompt: str = None):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})
    
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: self._client.chat.completions.create(
            model=model_info.id,
            messages=messages,
            stream=False
        )
    )
    return response.choices[0].message.content
```

**Advantages:**
- ✅ Natural language understanding (ask anything)
- ✅ Contextual insights and recommendations
- ✅ Learns from full cluster state
- ✅ Helpful explanations and troubleshooting

**Limitations:**
- ❌ Requires model download (500MB - 8GB)
- ❌ Higher latency (2-5 seconds per query)
- ❌ Uses CPU/GPU resources

---

### 2. Foundry Local SDK Integration

#### What is Foundry Local?
Microsoft Foundry Local is a framework for running large language models (LLMs) locally on your machine. It provides:
- **Model lifecycle management** - Download, load, start, stop models
- **Hardware acceleration** - GPU (NVIDIA TensorRT), CPU, NPU support
- **OpenAI-compatible API** - Standard interface for queries
- **Model catalog** - 19+ pre-optimized models for different tasks

#### SDK Implementation Journey

**Initial Approach (Subprocess - Unreliable):**
```python
# OLD WAY - Don't do this
subprocess.run(["foundry", "model", "start", model_name])
subprocess.run(["foundry", "model", "stop"])
```
**Problems:**
- ❌ No progress tracking
- ❌ Error handling was blind
- ❌ Process management issues
- ❌ No endpoint discovery

**Official SDK Approach (Current - Reliable):**
```python
# NEW WAY - Official SDK pattern
from foundry_local import FoundryLocalManager as FoundrySDK
import openai

class FoundryManager:
    def __init__(self):
        self._manager: Optional[FoundrySDK] = None
        self._client: Optional[openai.OpenAI] = None
    
    async def start_model(self, model_name: str):
        # SDK handles everything: download → load → start → endpoint
        self._manager = FoundrySDK(model_name)
        
        # Create OpenAI client pointed at local endpoint
        self._client = openai.OpenAI(
            base_url=self._manager.endpoint,  # e.g., http://127.0.0.1:49187/v1
            api_key=self._manager.api_key      # Auto-generated
        )
        
        return {
            "success": True,
            "endpoint": self._manager.endpoint,
            "model": model_name
        }
```

**SDK Features Used:**

1. **Automatic Model Discovery:**
```python
# SDK finds models in cache automatically
cache_path = Path.home() / ".foundry" / "cache" / "models" / "Microsoft"
# Models: phi-4, qwen2.5-0.5b, qwen2.5-1.5b, etc.
```

2. **Model Information:**
```python
model_info = self._manager.get_model_info(model_name)
# Returns: ModelInfo(id, name, size, device_type, status)
```

3. **Lifecycle Management:**
```python
# Start: Downloads if needed → Loads → Returns endpoint
manager = FoundrySDK("qwen2.5-1.5b")

# Query: Standard OpenAI interface
response = client.chat.completions.create(
    model=model_info.id,
    messages=[{"role": "user", "content": "Hello"}]
)

# Stop: Cleanup handled automatically
manager = None  # SDK cleans up resources
```

#### Model Selection Strategy

**CPU-Compatible Models (Recommended for most users):**
- `qwen2.5-0.5b` - 520MB, fastest, good for basic queries
- `qwen2.5-1.5b` - 1.25GB, better quality, still fast
- `qwen2.5-coder-0.5b` - 520MB, optimized for code/configs
- `qwen2.5-coder-1.5b` - 1.25GB, best for technical content

**GPU-Only Models (Require NVIDIA TensorRT):**
- `phi-4` - 8.37GB, high quality but needs GPU
- `phi-3.5-mini` - 7GB, needs GPU
- All `mistral` and `deepseek` variants - GPU required

**Selection Logic in Code:**
```python
# backend/src/services/foundry_manager.py
async def start_model(self, model_name: str):
    try:
        # SDK tries to load model
        self._manager = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: FoundrySDK(model_name)),
            timeout=60.0  # Prevent hanging on GPU-only models
        )
    except asyncio.TimeoutError:
        raise Exception(
            f"Model loading timed out. {model_name} may require GPU."
        )
    except Exception as e:
        # Parse error for better user feedback
        if "NvTensorRT" in str(e) or "GPU" in str(e):
            raise Exception(
                f"{model_name} requires GPU acceleration. "
                f"Try qwen2.5-0.5b or qwen2.5-1.5b instead."
            )
```

---

### 3. Kubernetes Integration

#### Connection Setup
```python
# backend/src/services/kubernetes.py
from kubernetes import client, config

class KubernetesClient:
    def __init__(self):
        # Auto-detects kubeconfig or in-cluster config
        config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
```

#### Data Collection
```python
async def get_cluster_status(self) -> ClusterStatus:
    # Fetch all pods across all namespaces
    pods = self.v1.list_pod_for_all_namespaces()
    
    # Fetch recent events
    events = self.v1.list_event_for_all_namespaces(
        limit=50,
        field_selector="type!=Normal"
    )
    
    # Build status object
    return ClusterStatus(
        pods=[PodStatus(
            name=pod.metadata.name,
            namespace=pod.metadata.namespace,
            phase=pod.status.phase,
            node=pod.spec.node_name,
            ip=pod.status.pod_ip,
            restarts=sum(c.restart_count for c in pod.status.container_statuses or [])
        ) for pod in pods.items],
        events=[Event(...) for event in events.items],
        timestamp=datetime.now(timezone.utc)
    )
```

#### Context Buffer (Historical Data)
```python
class ContextBuffer:
    def __init__(self, retention_hours: int = 24):
        self._snapshots: List[ClusterStatus] = []
        self._max_size = 1000
    
    def add_snapshot(self, status: ClusterStatus):
        self._snapshots.append(status)
        self._cleanup_old_snapshots()
    
    def get_pod_history(self, pod_name: str, hours: int = 1):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [s for s in self._snapshots 
                if s.timestamp >= cutoff 
                and any(p.name == pod_name for p in s.pods)]
```

---

### 4. System Prompt Engineering

The key to good AI responses is the system prompt. Here's how we guide the model:

```python
system_prompt = """You are a Kubernetes operations assistant. Your role is to help users understand and manage their Kubernetes cluster.

When answering questions:
1. Provide direct, actionable information about the cluster
2. If given cluster data, analyze it and answer based on that data
3. Be concise but thorough
4. Format responses clearly with bullet points or tables when appropriate
5. Focus on operational insights, not just commands

DO NOT provide kubectl commands or tutorials unless specifically asked.
ALWAYS use the cluster data provided in the user's message to give specific answers about THEIR cluster."""
```

**Why This Works:**
- ✅ Sets clear role and expectations
- ✅ Prevents generic tutorial responses
- ✅ Forces model to use provided data
- ✅ Encourages actionable insights

**Context Building:**
```python
# We send comprehensive cluster state to the model
context = f"""CURRENT CLUSTER STATE (as of {timestamp}):

SUMMARY:
- Total Pods: 9
- Running: 7
- Pending: 2
- Failed: 0

NODES:
- node-1: 4 pods
- node-2: 3 pods
- node-3: 2 pods

ALL PODS:
- coredns-abc123 (namespace: kube-system, node: node-1, status: Running, restarts: 0, ip: 10.42.0.5)
- traefik-def456 (namespace: kube-system, node: node-2, status: Running, restarts: 0, ip: 10.42.1.3)
- [... all other pods with full details ...]

RECENT EVENTS:
- [Warning] BackOff: Back-off restarting failed container
- [Warning] Failed: Failed to pull image

USER QUESTION: {user_question}
Provide a direct answer using the cluster data above."""
```

---

### 5. User Interface Design

#### Design Philosophy
- **Dark theme** - Reduces eye strain for DevOps monitoring
- **Information density** - Show cluster stats, status, and controls without scrolling
- **Visual hierarchy** - Important info (cluster stats, foundry status) always visible
- **Minimal friction** - No popups, inline messages, instant feedback

#### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ Header | Cluster Stats (9 pods, 3 nodes, 1 ns) | Foundry Control│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Quick Actions (6 cards):                                       │
│  [Running Pods] [Health Check] [Restarts]                       │
│  [Node Pools]   [Diagnostics]  [Topology]                       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Chat Area:                                                      │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ User: show me all pods                                      ││
│  │ Bot: [Response with pod list]                               ││
│  │ User: which ones are restarting?                            ││
│  │ Bot: [Restart analysis]                                     ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [Ask about your cluster...] [Send]                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Key UI Components

**1. Foundry Control Panel:**
```html
<div class="foundry card">
    <h2>🤖 Foundry Control</h2>
    <div class="status-badge" id="foundryStatus">
        ⏸️ Foundry not running
    </div>
    <select id="modelSelect">
        <option value="">Select a model...</option>
        <option value="phi-4">phi-4 (ready - no download needed)</option>
        <option value="qwen2.5-0.5b">qwen2.5-0.5b (ready)</option>
        <option value="qwen2.5-1.5b">qwen2.5-1.5b (ready)</option>
    </select>
    <div class="control-buttons">
        <button id="startBtn" onclick="startFoundry()">▶️ Start</button>
        <button id="stopBtn" onclick="stopFoundry()">⏹️ Stop</button>
    </div>
    <!-- Inline message area (replaces popups) -->
    <div id="foundryMessage"></div>
</div>
```

**2. Status Polling:**
```javascript
// Check cluster and Foundry status every 30 seconds
async function checkFoundryStatus() {
    const response = await fetch('/api/foundry/status');
    const data = await response.json();
    
    const statusBadge = document.getElementById('foundryStatus');
    if (data.running) {
        statusBadge.className = 'status-badge online';
        statusBadge.textContent = `✅ Running: ${data.model}`;
        startBtn.style.display = 'none';
        stopBtn.style.display = 'inline-block';
    } else {
        statusBadge.className = 'status-badge offline';
        statusBadge.textContent = '⏸️ Foundry not running';
        startBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
    }
}

setInterval(checkFoundryStatus, 30000); // Poll every 30s
```

**3. Message Display (No Popups):**
```javascript
function showFoundryMessage(message, type = 'info') {
    const messageDiv = document.getElementById('foundryMessage');
    
    // Color based on type
    if (type === 'error') {
        messageDiv.style.background = 'rgba(239, 68, 68, 0.2)';
        messageDiv.style.color = 'var(--accent-error)';
    } else if (type === 'success') {
        messageDiv.style.background = 'rgba(16, 185, 129, 0.2)';
        messageDiv.style.color = 'var(--accent-success)';
    }
    
    messageDiv.textContent = message;
    
    // Auto-hide after 5 seconds
    setTimeout(() => messageDiv.remove(), 5000);
}
```

---

## Value Proposition

### For DevOps Teams

**Immediate Benefits (Direct Mode):**
1. **Quick Cluster Insights** - "show pods", "node health", "restart info" → instant answers
2. **No Learning Curve** - Natural language queries instead of kubectl commands
3. **Always Available** - Works without internet, model downloads, or setup
4. **Fast** - Millisecond response times for real-time monitoring

**Enhanced Benefits (AI Mode):**
1. **Troubleshooting Assistant** - "Why is pod X restarting?" → Get analysis with context
2. **Pattern Recognition** - "Which services are having issues?" → AI correlates events
3. **Recommendations** - "How can I improve cluster health?" → Actionable suggestions
4. **Learning Tool** - Ask "what does CrashLoopBackOff mean?" → Educational responses

### For Organizations

**Cost Savings:**
- ✅ No cloud API costs (runs 100% locally)
- ✅ Reduced MTTR (faster troubleshooting)
- ✅ Knowledge retention (AI explains issues clearly)
- ✅ Training efficiency (junior devs learn faster)

**Security & Compliance:**
- ✅ No data leaves your network (fully local)
- ✅ No API keys or external dependencies
- ✅ Air-gap compatible (Direct Mode works offline)
- ✅ Audit trail via structured logs

**Flexibility:**
- ✅ Works with any K8s cluster (vanilla, AKS, EKS, GKE, k3s)
- ✅ Scales from laptop to production
- ✅ Optional AI (start simple, add intelligence later)
- ✅ Open source potential (community contributions)

---

## How to Share with Community

### Quick Start Guide

**What to tell users:**

> "K8s AI Assistant is a web-based tool that lets you manage Kubernetes clusters using natural language. Ask questions like 'show me all pods' or 'which services are failing' and get instant answers. It works in two modes:
>
> **Direct Mode** (default): Keyword-based queries, instant responses, no setup
> **AI Mode** (optional): Download a small language model (500MB-1GB) for intelligent analysis
>
> Everything runs locally - no cloud APIs, no data sharing, no costs."

### Installation Steps

1. **Prerequisites:**
   - Python 3.11+
   - kubectl configured for your cluster
   - Optional: Foundry Local (for AI Mode)

2. **Install:**
   ```bash
   git clone <repository>
   cd aksarc-foundrylocal-aiops
   pip install -r backend/requirements.txt
   ```

3. **Run:**
   ```bash
   # Windows
   .\run.ps1
   
   # Linux/Mac
   python backend/run.py
   ```

4. **Access:**
   - Open browser to http://localhost:8000
   - Direct Mode works immediately
   - For AI Mode: Select model → Click Start → Wait 30 seconds

### Demo Script

**Show Direct Mode (1 minute):**
1. Open UI
2. Type: "show me all pods"
3. Show instant response with pod list
4. Type: "which pods are restarting?"
5. Show filtered results

**Show AI Mode (2 minutes):**
1. Select "qwen2.5-0.5b" model
2. Click Start
3. Wait for "Running" status
4. Type: "analyze the health of my cluster"
5. Show AI-generated analysis with insights
6. Type: "which pods should I investigate first?"
7. Show prioritized recommendations

### Technical Documentation to Share

**For Developers:**
- GitHub README with architecture diagram
- API documentation (FastAPI auto-generates at /docs)
- Code examples for extending functionality
- Contribution guidelines

**For Operators:**
- Deployment guide (Docker, K8s, bare metal)
- Configuration options (ports, kubeconfig path, model selection)
- Troubleshooting guide (common errors, solutions)
- Performance tuning (model selection, caching, polling intervals)

**For Security Teams:**
- Data flow diagram (nothing leaves localhost)
- Authentication options (add SSO, RBAC if needed)
- Audit logging configuration
- Network requirements (only needs localhost:8000)

---

## Future Enhancements

### Short-term (Community Requests)
- **Multi-cluster support** - Switch between clusters in UI
- **Custom queries** - Save favorite questions
- **Export reports** - Download cluster health reports as PDF
- **Slack integration** - Query your cluster from Slack

### Medium-term (Operational Features)
- **Alert correlation** - Link K8s events to Prometheus alerts
- **Remediation actions** - "restart pod X", "scale deployment Y"
- **Historical analysis** - "show pod restarts over last 24 hours"
- **Resource recommendations** - "this pod needs more memory"

### Long-term (AI Enhancements)
- **Anomaly detection** - AI learns normal patterns, alerts on deviations
- **Predictive maintenance** - "pod X will likely fail in 2 hours"
- **Cost optimization** - "you can save $500/month by right-sizing"
- **Security analysis** - "these pods have security misconfigurations"

---

## Conclusion

The K8s AI Assistant bridges the gap between complex Kubernetes operations and natural language queries. By combining:

- **Immediate value** (Direct Mode with keyword matching)
- **Optional intelligence** (AI Mode with local LLM)
- **Microsoft's Foundry Local SDK** (professional-grade model management)
- **Modern web interface** (responsive, dark-themed, no popups)

...we create a tool that serves both quick operational queries and deep analytical insights, all while maintaining security, privacy, and zero cloud costs.

The dual-mode architecture ensures users get value immediately (Direct Mode) while having the option to unlock advanced capabilities (AI Mode) when needed. The official Foundry Local SDK integration provides reliable model management with proper error handling, timeout protection, and hardware compatibility detection.

This combination makes K8s AI Assistant suitable for individuals learning Kubernetes, teams managing production clusters, and organizations requiring local-first, secure operational tools.

---

## References

### Official Documentation
- **Foundry Local**: https://learn.microsoft.com/en-us/azure/ai-services/foundry-local/
- **Foundry Local SDK**: https://pypi.org/project/foundry-local-sdk/
- **Kubernetes Python Client**: https://github.com/kubernetes-client/python
- **FastAPI**: https://fastapi.tiangolo.com/

### Code Repository Structure
```
aksarc-foundrylocal-aiops/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   └── routes.py          # REST API endpoints
│   │   ├── services/
│   │   │   ├── kubernetes.py      # K8s cluster interaction
│   │   │   ├── foundry_manager.py # Foundry SDK integration
│   │   │   └── context.py         # Historical data buffer
│   │   └── main.py                # FastAPI application
│   ├── requirements.txt           # Python dependencies
│   └── run.py                     # Entry point
├── index.html                      # Single-page web UI
├── run.ps1                         # Windows startup script
├── QUICKSTART.md                   # User startup guide
├── FOUNDRY_SDK_INTEGRATION.md      # Technical SDK details
├── FOUNDRY_TROUBLESHOOTING.md      # Common issues & solutions
└── PROJECT_OVERVIEW.md             # This document
```

### Contact & Community
- **Issues**: Open GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Contributions**: Pull requests welcome (see CONTRIBUTING.md)
- **License**: [Specify your license - MIT, Apache 2.0, etc.]

---

*This document provides a comprehensive overview suitable for technical documentation, blog posts, conference presentations, or community sharing. Copy and paste into Word, format with headings (Heading 1 for main sections, Heading 2 for subsections), and add your organization's branding.*
