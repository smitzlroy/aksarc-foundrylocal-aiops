# 🤖 K8s AI Assistant

<div align="center">

**Chat with your Kubernetes cluster in natural language**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Documentation](#-documentation)

</div>

---

## 🌟 What is K8s AI Assistant?

K8s AI Assistant is a **natural language interface** for Kubernetes that lets you interact with your cluster using plain English. Ask questions, get pod logs, visualize network topology, and run diagnostics - all through an intuitive chat interface powered by local AI.

### Why Choose K8s AI Assistant?

- **💬 Natural Language**: No more memorizing kubectl commands - just ask naturally
- **🔒 Privacy First**: All AI processing happens locally via Azure AI Foundry Local
- **🎯 Multi-Platform**: Works with k8s, k3s, and Azure Kubernetes Service (AKS Arc)
- **🗺️ Network Topology**: Visualize pod communication, services, and network policies with IP addresses
- **🔍 Smart Diagnostics**: Automated cluster health checks with actionable recommendations
- **⚡ Modern UI**: Clean, responsive interface with real-time updates
- **🚀 Easy Setup**: Get running in under 5 minutes

---

## ✨ Features

### 🗣️ Natural Language Query
```
You: "Show me all failing pods"
Assistant: Here are 2 pods with issues:
  - nginx-deployment-xyz: CrashLoopBackOff
  - redis-cache-abc: ImagePullBackOff
```

### 🗺️ Network Topology Visualization
- **Communication Matrix**: See which pods talk to which services
- **IP Addresses**: View pod IPs, service cluster IPs, and external IPs with visual indicators
- **Dependencies**: Understand service-to-pod relationships with port mappings
- **Network Policies**: Identify security rules and unrestricted namespaces
- **Export**: Download topology data as JSON for documentation and analysis

### 🔍 Cluster Diagnostics
- **Basic Health Checks**: Cluster connectivity, pod health, service status (works on all K8s platforms)
- **AKS Arc Diagnostics**: Advanced PowerShell-based diagnostics (optional module)
- **Progress Tracking**: Real-time feedback with 3-step progress indicator
- **Auto-Remediation**: Automated fixes for common issues
- **Fallback Support**: Works even without AKS Arc module installed

### 📊 Quick Actions Bar
- 🔍 **Diagnostics & Logs**: One-click access to cluster diagnostics
- 🗺️ **Network Topology**: Visualize cluster network instantly
- 📋 **Recent Logs**: View recent pod logs
- 🏥 **Health Check**: Get cluster status overview

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** installed ([Download](https://www.python.org/downloads/))
- **kubectl** configured with cluster access ([Install Guide](https://kubernetes.io/docs/tasks/tools/))
- **Kubernetes cluster** - Any of these work:
  - ✅ AKS (Azure Kubernetes Service) or AKS Arc
  - ✅ k3s (lightweight Kubernetes)
  - ✅ k3d (k3s in Docker - perfect for local testing)
  - ✅ EKS, GKE, Minikube, or any standard k8s 1.27+
- **Ollama** (optional, for AI chat) ([Install Guide](https://ollama.ai/))

### Installation

```bash
# Clone the repository
git clone https://github.com/smitzlroy/aksarc-foundrylocal-aiops.git
cd aksarc-foundrylocal-aiops

# Install Python dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### Running the Server

**Option 1: Background Service (Recommended)**
```powershell
# Start server in background
.\start-service.ps1

# Check status
.\status-service.ps1

# Stop server
.\stop-service.ps1
```

**Option 2: Foreground (for debugging)**
```powershell
cd backend
python run.py
```

**Option 3: Quick Setup Script**
```powershell
.\run.ps1  # Installs dependencies + starts server
```

### Access the Application

Open your browser to:
- **Web UI**: http://localhost:8080/
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/api/health

The server will:
1. ✅ Auto-detect your cluster type (k3s, AKS Arc, vanilla k8s)
2. ✅ Connect using your existing kubectl credentials
3. ✅ Start serving the web interface on port 8080
4. ✅ Run in background (with start-service.ps1)

### First Steps

1. **Verify Connection**: The UI will show cluster stats (pods, nodes, namespaces) if connected
   - If showing "Offline", wait 15-20 seconds for initialization
   - Hard refresh browser (Ctrl+F5) if needed

2. **Try Quick Actions**:
   - 🔍 **Diagnostics & Logs**: Run automated health checks
   - 🗺️ **Network Topology**: Visualize service dependencies and pod communication
   - 📋 **Recent Logs**: View recent pod activity
   - 🏥 **Health Check**: Get overall cluster status

3. **Use Natural Language Chat** (requires Ollama):
   ```
   "Show me all pods in the default namespace"
   "Which pods are using the most memory?"
   "Get logs from nginx pod"
   "Check for any failing pods"
   ```

### Connecting to Your Cluster

**The tool uses your existing kubectl configuration** - no additional setup!

1. **Verify kubectl access**:
   ```bash
   kubectl cluster-info
   kubectl get nodes
   ```

2. **That's it!** The tool will automatically:
   - Read your `~/.kube/config`
   - Detect cluster type (AKS Arc / k3s / vanilla k8s)
   - Connect using your credentials
   - Start monitoring

**Supported Environments:**
- AKS (Azure Kubernetes Service) including AKS on Arc
- k3s (lightweight Kubernetes for edge/IoT)
- k3d (k3s in Docker for local development)
- Any standard Kubernetes 1.27+ cluster

**Local Testing with k3d:**
```bash
# Create a test cluster
k3d cluster create aiops-dev --agents 2

# Start the tool
.\start-service.ps1

# Access at http://localhost:8080/
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Browser                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Chat UI     │  │  Topology    │  │   Diagnostics      │    │
│  │ (HTML/JS)   │  │  Viewer      │  │   Panel            │    │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬──────────┘    │
└─────────┼─────────────────┼────────────────────┼───────────────┘
          │                 │                    │
          └─────────────────┴────────────────────┘
                            │
                         HTTP/REST
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend (Python)                     │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐     │
│  │ Routes     │  │ Services   │  │  Kubernetes Client   │     │
│  │            │  │            │  │                      │     │
│  │ • /chat    │→ │ • K8s      │→ │  • Pod Management    │     │
│  │ • /topology│  │ • Network  │  │  • Service Discovery │     │
│  │ • /diag    │  │ • Diag     │  │  • Event Monitoring  │     │
│  └────────────┘  └────────────┘  └──────────────────────┘     │
└───────────────────────┬──────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌────────────────┐
│ Kubernetes   │ │   Azure AI  │ │   PowerShell   │
│   Cluster    │ │   Foundry   │ │  (AKS Arc)     │
│              │ │   Local     │ │                │
│ • k8s/k3s    │ │ (Optional)  │ │  (Optional)    │
│ • AKS Arc    │ └─────────────┘ └────────────────┘
└──────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML/CSS/JavaScript | Single-page application |
| **Backend** | Python 3.11+ FastAPI | REST API server |
| **AI (Optional)** | Azure AI Foundry Local | Natural language processing |
| **Kubernetes** | kubectl / Python Client | Cluster interaction |
| **Platform** | k8s / k3s / AKS Arc | Target clusters |

---

## 📖 Documentation

### User Guides
- [Quick Start Guide](QUICKSTART.md) - Get up and running
- [Background Service Setup](README-SERVICE.md) - Run as Windows background service
- [Linux Server Deployment](deploy/systemd/README.md) - Deploy on jumpbox/dev server with systemd
- [Troubleshooting](FOUNDRY_TROUBLESHOOTING.md) - Common issues and solutions

### Developer Guides
- [Architecture Overview](ARCHITECTURE.md) - System design and components
- [Development Setup](docs/DEVELOPMENT.md) - Setting up dev environment

### Feature Documentation
- [Network Topology](docs/development/VISUAL_IMPROVEMENTS_GUIDE.md) - Topology visualization and network analysis
- [Diagnostics System](docs/development/DIAGNOSTICS_IMPROVEMENTS.md) - Cluster diagnostics and health checks
- [AKS Arc Integration](docs/development/AKS_ARC_IMPLEMENTATION_SUMMARY.md) - AKS Arc specific features

---

## 🔧 Configuration

### Backend Configuration

Create `backend/.env` (optional - defaults work for most cases):

```env
# API Server Configuration
API_PORT=8080                                    # Web UI and API port
LOG_LEVEL=INFO                                   # DEBUG, INFO, WARN, ERROR

# AI Configuration (Optional - auto-detected if Ollama/Foundry running)
FOUNDRY_ENDPOINT=http://localhost:11434          # Ollama/Foundry endpoint
FOUNDRY_MODEL=llama2                             # Default AI model (can be changed in UI)
FOUNDRY_TIMEOUT=30.0                             # Request timeout

# Kubernetes Configuration (Auto-detected)
KUBECONFIG=~/.kube/config                        # Path to kubeconfig file
```

### Setting Up AI Features (Optional)

1. **Install Ollama or Azure AI Foundry Local**:
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: Download from https://ollama.ai/
   ```

2. **Start Ollama** (runs on port 11434 by default):
   ```bash
   ollama serve
   ```

3. **Select and Download Models** - Use the UI dropdown in the Foundry Control panel:
   - The UI will detect available models
   - Select a model from the dropdown (e.g., llama2, phi-3, qwen)
   - Click to download and start the model
   - No manual `ollama pull` commands needed!

**Without Ollama:** All features work except natural language chat. You can still use topology, diagnostics, and monitoring.

### Deployment Options

**Local Development:**
```powershell
.\start-service.ps1  # Runs on localhost:8080
```

**Production (with authentication/TLS):**
1. Deploy behind reverse proxy (nginx/Traefik)
2. Add authentication layer (OAuth2/OIDC)
3. Use HTTPS with proper certificates
4. Configure RBAC permissions appropriately
5. Run as system service (systemd/Windows Service)

See `README-SERVICE.md` for background service setup and auto-start on boot

---

## 🎯 Use Cases

### For DevOps Engineers
- **Quick Troubleshooting**: "Show me pods with high restart counts"
- **Log Analysis**: "Get logs from all nginx pods in the last hour"
- **Resource Monitoring**: "Which nodes are under pressure?"

### For Platform Engineers
- **Network Mapping**: Visualize service mesh and dependencies with full IP information
- **Security Audits**: Identify pods without network policies
- **Capacity Planning**: Export topology data as JSON for documentation

### For Site Reliability Engineers (SRE)
- **Health Checks**: Automated diagnostics with remediation suggestions
- **Incident Response**: Quick access to logs and events
- **Post-Mortem**: Export cluster state for analysis

---

## 🔐 Security

- **No Cloud Dependencies**: All processing happens locally
- **No Data Collection**: Your cluster data stays on your infrastructure
- **Audit Trail**: All API calls are logged
- **RBAC Compatible**: Works with Kubernetes RBAC

**Important**: Never commit sensitive data. All `.env` files and credentials are excluded via `.gitignore`.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for the Kubernetes community**

Star ⭐ this repo if you find it helpful!

</div>
