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
- **IP Addresses**: View pod IPs (📍 10.42.0.5), service cluster IPs (🌐 10.43.0.1), and external IPs (🌍 52.186.14.10)
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

- **Kubernetes Cluster**: k3s, k8s, or AKS Arc
- **kubectl**: Configured to access your cluster
- **Python 3.11+**: For the backend
- **Azure AI Foundry Local** *(optional)*: For AI-powered chat features

### Installation

#### Windows:

```powershell
# Clone the repository
git clone https://github.com/yourusername/k8s-ai-assistant.git
cd k8s-ai-assistant

# Run the start script
.\run.ps1
```

#### Linux/Mac:

```bash
# Clone the repository
git clone https://github.com/yourusername/k8s-ai-assistant.git
cd k8s-ai-assistant

# Make script executable and run
chmod +x run.py
python3 run.py
```

The application will:
1. ✅ Check Python dependencies
2. ✅ Install required packages
3. ✅ Start the backend server
4. ✅ Open your browser to http://localhost:8000

### First Steps

1. **Check Cluster Connection**: The UI will show cluster stats (pods, nodes, namespaces) if connected
2. **Try Quick Actions**:
   - 🔍 **Diagnostics & Logs**: Run cluster health checks
   - 🗺️ **Network Topology**: Visualize your cluster network with IP addresses
   - 📋 **Recent Logs**: View recent pod logs
   - 🏥 **Health Check**: Get cluster status overview

3. **Ask Questions** (requires AI Foundry):
   ```
   "Show me all pods in the default namespace"
   "Which pods are using the most memory?"
   "Get logs from nginx pod"
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
- [Troubleshooting](FOUNDRY_TROUBLESHOOTING.md) - Common issues and solutions

### Developer Guides
- [Architecture Overview](ARCHITECTURE.md) - System design and components
- [Development Setup](docs/DEVELOPMENT.md) - Setting up dev environment

### Feature Documentation
- [Network Topology](VISUAL_IMPROVEMENTS_GUIDE.md) - Topology visualization with IP addresses
- [Diagnostics System](DIAGNOSTICS_IMPROVEMENTS.md) - Cluster diagnostics and health checks
- [AKS Arc Integration](AKS_ARC_IMPLEMENTATION_SUMMARY.md) - AKS Arc specific features

---

## 🔧 Configuration

### Backend Configuration

Create `backend/.env` (optional for AI features):

```env
# Azure AI Foundry Local (optional)
FOUNDRY_ENDPOINT=http://localhost:8080
FOUNDRY_MODEL=phi-3-mini-4k-instruct

# Logging
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000
```

### Kubernetes Configuration

The assistant uses your existing `~/.kube/config`. Ensure kubectl is configured:

```bash
kubectl cluster-info
```

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
