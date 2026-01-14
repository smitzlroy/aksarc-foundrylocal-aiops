# 🚀 Quick Start Guide

## Starting the Application

### Option 1: One-Command Startup (Recommended)

Open PowerShell in the project directory and run:

```powershell
.\run.ps1
```

This will:
1. ✅ Check if Foundry Local is running
2. ✅ Check Kubernetes connection
3. ✅ Start the FastAPI backend server
4. ✅ Automatically open the UI in your browser

The UI will be available at: **http://localhost:8000**

---

## What You'll See

### On Startup:
```
🤖 K8s AI Assistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Checking Foundry Local...
⚠️  Foundry not running - you can start it from the UI

🔍 Checking Kubernetes...
✅ K8s cluster connected (3 nodes)

🚀 Starting server...

✨ Server starting on http://localhost:8000
```

### In the UI:

**Dark-themed interface with:**
- 💬 Chat interface for K8s queries
- 🤖 Model selector dropdown
- 📊 Cluster topology visualization
- 🔧 Direct Mode (works without AI)

---

## Using the Application

### Without AI (Direct Mode) - Works Immediately ✅

Direct Mode uses **keyword pattern matching** to answer common queries:

**Try these queries:**
- `show me all pods`
- `what nodes do I have?`
- `show pod restarts`
- `cluster health status`
- `system pods`

**Result**: Formatted K8s data with bullets, sections, node assignments

**Note**: This is NOT natural language AI - it's simple keyword matching!

---

### With AI (Foundry Mode) - Optional 🤖

For **true natural language understanding**, start a model:

1. **In the UI**: Click the model dropdown (top left)
2. **Select a model**:
   - ✅ **qwen2.5-0.5b** (fastest, 0.52 GB) - RECOMMENDED
   - ✅ **qwen2.5-1.5b** (better quality, 1.25 GB)
   - ✅ **phi-4** (best quality, 8.37 GB)

3. **Click "Start"** - SDK will:
   - Load model into memory (~10-30 seconds)
   - Start Foundry Local service
   - Enable AI-powered chat

4. **Now ask complex questions:**
   - "Which pods have been restarting most frequently in the last hour?"
   - "Show me pods consuming high memory"
   - "Are there any network connectivity issues?"
   - "Analyze security policies in my cluster"

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Browser UI                     │
│          http://localhost:8000                  │
│  Dark theme • Chat • Topology • Model selector  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│            FastAPI Backend (port 8000)          │
│                                                 │
│  Routes:                                        │
│  • /api/chat/query    - Dual-mode chat         │
│  • /api/foundry/start  - Start AI model        │
│  • /api/foundry/status - Check models          │
│  • /api/topology       - Network visualization │
└─────────────────────────────────────────────────┘
           ↓                           ↓
┌──────────────────────┐   ┌──────────────────────┐
│  Direct Mode         │   │   AI Mode (Optional) │
│  (Always Available)  │   │   (Foundry SDK)      │
│                      │   │                      │
│  • Pattern matching  │   │  • FoundryLocalMgr   │
│  • Keyword detection │   │  • OpenAI SDK        │
│  • K8s data format   │   │  • True NLP          │
└──────────────────────┘   └──────────────────────┘
           ↓                           ↓
┌─────────────────────────────────────────────────┐
│          Kubernetes Client (kubectl)            │
│  Connects to: k3d cluster "aiops-dev"          │
│  • 3 nodes  • 9 pods  • kube-system namespace  │
└─────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Server won't start
```powershell
# Check if port 8000 is in use
Get-NetTCPConnection -LocalPort 8000

# Kill existing process
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force
}

# Restart
.\run.ps1
```

### Kubernetes not connecting
```powershell
# Check kubectl
kubectl get nodes

# Check cluster context
kubectl config current-context

# If using k3d
k3d cluster list
k3d cluster start aiops-dev
```

### Models not showing
```powershell
# Check Foundry CLI
foundry model list

# Check cache
Get-ChildItem "$env:USERPROFILE\.foundry\cache\models\Microsoft\"

# Should show:
# - Phi-4-trtrtx-gpu-1
# - qwen2.5-0.5b-instruct-trtrtx-gpu-2
# - qwen2.5-1.5b-instruct-trtrtx-gpu-2
```

### UI not loading
1. Check server logs in terminal
2. Navigate manually to http://localhost:8000
3. Check browser console (F12) for errors
4. Verify `index.html` exists in project root

---

## Files Structure

```
aksarc-foundrylocal-aiops/
├── run.ps1                          # ⭐ START HERE
├── index.html                       # UI (dark theme)
├── backend/
│   ├── run.py                      # FastAPI entry point
│   └── src/
│       ├── main.py                 # App initialization
│       ├── api/
│       │   └── routes.py           # API endpoints
│       ├── services/
│       │   ├── foundry_manager.py  # SDK-based manager
│       │   └── kubernetes.py       # K8s client
│       └── models/
│           └── cluster.py          # Data models
├── test_foundry_sdk.py             # Test SDK integration
└── FOUNDRY_SDK_INTEGRATION.md      # Technical details
```

---

## Key Features

### ✅ Currently Working
- 🔧 **Direct Mode**: Keyword-based K8s queries (no AI needed)
- 📊 **Topology View**: Network visualization with IPs
- 🎨 **Dark Theme UI**: Modern, clean interface
- 🔄 **Model Management**: Detect 3 downloaded models
- 📥 **Download Progress**: Real-time model download tracking
- ☁️ **K8s Integration**: Live cluster monitoring

### 🚀 Available with Model Start
- 🤖 **AI Chat**: True natural language understanding
- 🧠 **Smart Queries**: Complex analysis and recommendations
- 💡 **Context-Aware**: Uses cluster state for better answers

### 📋 Planned (from SECURITY_CONNECTIVITY_PLAN.md)
- 🔒 **NetworkPolicy Visualization**
- 🌐 **Pod-to-Pod Connectivity Matrix**
- 🚫 **Namespace Isolation Analysis**
- ⚠️ **Security Scoring & Compliance**

---

## Quick Command Reference

```powershell
# Start application
.\run.ps1

# Test Foundry SDK
python test_foundry_sdk.py

# Check models in cache
foundry model list

# Check K8s cluster
kubectl get nodes
kubectl get pods -A

# Stop server
# Press Ctrl+C in the terminal running run.ps1
```

---

## Next Steps

1. **Start the app**: `.\run.ps1`
2. **Open browser**: http://localhost:8000
3. **Try Direct Mode**: Ask "show me all pods"
4. **Optional**: Start a model (qwen2.5-0.5b recommended)
5. **Try AI queries**: Ask complex questions

**Need help?** Check `FOUNDRY_SDK_INTEGRATION.md` for technical details!
