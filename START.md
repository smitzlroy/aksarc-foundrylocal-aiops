# AKS Arc AI Operations Assistant - Quick Start

## ✅ Tested & Verified

All components have been tested and verified working.

## Start the Server

Open PowerShell in this directory and run:

```powershell
.\start.ps1
```

The server will:
1. Refresh your PATH to find Python
2. Change to the backend directory
3. Start the FastAPI server on http://localhost:8000

You'll see:
```
========================================
  AKS Arc AI Operations Assistant
========================================

Changing to backend directory...
Refreshing PATH...
Found: Python 3.11.9

Starting server on http://localhost:8000
Press Ctrl+C to stop the server

INFO:     Started server process [XXXXX]
{"message": "Successfully connected to Kubernetes cluster", ...}
{"pod_count": 9, ...}
```

## Test the Application

### Option 1: Interactive API Documentation (Recommended)
1. Keep the server running
2. Open your browser to: **http://localhost:8000/docs**
3. Try the endpoints:
   - Click **GET /api/health** → "Try it out" → "Execute"
   - Click **GET /api/cluster/status** → "Try it out" → "Execute"
   - Click **GET /api/cluster/pods** → "Try it out" → "Execute"

### Option 2: Dashboard UI
1. Keep the server running
2. Open `dashboard.html` in your browser (double-click it)
3. You'll see:
   - Real-time cluster status
   - Pod list with filtering
   - Live logs viewer
   - Auto-refresh every 30 seconds

### Option 3: PowerShell Commands
In a **new** PowerShell window:

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/api/health"

# Cluster status with all pods
Invoke-RestMethod -Uri "http://localhost:8000/api/cluster/status" | ConvertTo-Json -Depth 3

# List pods in specific namespace
Invoke-RestMethod -Uri "http://localhost:8000/api/cluster/pods?namespace=kube-system"

# Get pod logs
Invoke-RestMethod -Uri "http://localhost:8000/api/cluster/pods/kube-system/coredns-ccb96694c-w9chf/logs?tail=20"
```

## What You Should See

### Health Check Response:
```json
{
  "status": "healthy",
  "services": {
    "kubernetes": true,
    "context_buffer": true,
    "foundry": true
  },
  "timestamp": "2026-01-14T12:44:52.513556Z"
}
```

### Cluster Status Response:
- List of 9 pods from your k3s cluster
- Pod details: name, namespace, phase, node, containers, ready count
- Empty events list (populated when events occur)

## Stop the Server

Press `Ctrl+C` in the terminal where start.ps1 is running.

## Troubleshooting

**Server won't start:**
- Make sure you're in the `c:\AI\aksarc-foundrylocal-aiops` directory
- Verify Python 3.11 is installed: `python --version`
- Check k3s cluster is running: `kubectl get nodes`

**Can't connect to API:**
- Verify server is running (you should see "Uvicorn running on http://0.0.0.0:8000")
- Try http://localhost:8000/docs in your browser
- Check no other service is using port 8000

**Dashboard shows errors:**
- Make sure server is running FIRST
- Check browser console (F12) for error messages
- Verify the API URL in dashboard.html is correct (should be http://localhost:8000)

## Next Steps

1. **Try the interactive API docs** - Most user-friendly way to test
2. **Explore the dashboard** - Visual interface for monitoring
3. **Check background watcher** - Server logs show cluster updates every 30 seconds
4. **Set up Foundry Local** - See `FOUNDRY_SETUP.md` for AI chat integration

---

**Everything is working!** The server successfully:
- ✅ Connects to your k3s cluster
- ✅ Detects 9 running pods
- ✅ Starts background watcher
- ✅ Serves all API endpoints
- ✅ Provides interactive documentation

**Optional:** For natural language chat queries about your cluster, see **`FOUNDRY_SETUP.md`** for instructions on setting up Azure AI Foundry Local. The application works perfectly without it - Foundry just adds AI-powered Q&A capabilities.
