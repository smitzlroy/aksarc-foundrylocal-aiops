# Testing Guide - AKS Arc AI Ops Assistant

## Quick Start Testing

### 1. Start the Server

Open a PowerShell terminal and run:

```powershell
cd c:\AI\aksarc-foundrylocal-aiops\backend
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
python run.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
{"event": "kubernetes_connected", ...}
{"event": "cluster_watcher_started", ...}
```

**Keep this terminal open** - the server needs to stay running.

---

## Terminal Testing (PowerShell)

Open a **new PowerShell terminal** and try these commands:

### Test 1: Health Check
```powershell
Invoke-RestMethod http://localhost:8000/api/health | ConvertTo-Json -Depth 5
```

**Expected Output:**
```json
{
  "status": "healthy",
  "services": {
    "kubernetes": true,
    "context_buffer": true,
    "foundry": false
  },
  "timestamp": "2026-01-14T..."
}
```

### Test 2: Get Cluster Status
```powershell
Invoke-RestMethod http://localhost:8000/api/cluster/status | ConvertTo-Json -Depth 5
```

**Expected Output:**
```json
{
  "timestamp": "2026-01-14T...",
  "pods": [
    {
      "name": "coredns-ccb96694c-w9chf",
      "namespace": "kube-system",
      "phase": "Running",
      "node": "k3d-aiops-dev-server-0",
      "containers": ["coredns"],
      "ready": 1,
      "total": 1,
      "restarts": 0
    }
  ],
  "events": []
}
```

### Test 3: List All Pods
```powershell
$pods = Invoke-RestMethod http://localhost:8000/api/cluster/pods
Write-Host "Total Pods: $($pods.Count)"
$pods | Select-Object namespace, name, phase, ready, total | Format-Table
```

### Test 4: Filter Pods by Namespace
```powershell
$kubePods = Invoke-RestMethod "http://localhost:8000/api/cluster/pods?namespace=kube-system"
Write-Host "Pods in kube-system: $($kubePods.Count)"
$kubePods | Select-Object name, phase | Format-Table
```

### Test 5: Get Pod Logs
```powershell
# Get logs from CoreDNS
$response = Invoke-RestMethod "http://localhost:8000/api/cluster/pods/kube-system/coredns-ccb96694c-w9chf/logs?tail_lines=20"
Write-Host "Logs from $($response.pod):"
Write-Host $response.logs
```

### Test 6: Get Pod History
```powershell
# Wait a minute for the watcher to collect multiple snapshots, then:
$history = Invoke-RestMethod "http://localhost:8000/api/cluster/pods/kube-system/coredns-ccb96694c-w9chf/history?hours=1"
Write-Host "History entries: $($history.Count)"
$history | Select-Object @{Name='Time';Expression={$_.created_at}}, phase, ready, total
```

### Test 7: Interactive Pod Browser
```powershell
# Get all pods
$pods = Invoke-RestMethod http://localhost:8000/api/cluster/pods

# Display menu
Write-Host "`n=== Pod Browser ===`n"
for ($i = 0; $i -lt $pods.Count; $i++) {
    $pod = $pods[$i]
    Write-Host "[$i] $($pod.namespace)/$($pod.name) - $($pod.phase) ($($pod.ready)/$($pod.total))"
}

# Select a pod
$selection = Read-Host "`nSelect pod number to view logs"
$selectedPod = $pods[$selection]

# Get logs
$logs = Invoke-RestMethod "http://localhost:8000/api/cluster/pods/$($selectedPod.namespace)/$($selectedPod.name)/logs?tail_lines=50"
Write-Host "`n=== Logs for $($selectedPod.name) ===`n"
Write-Host $logs.logs
```

---

## Browser Testing (Simple HTML UI)

### Option 1: Interactive API Explorer (Swagger UI)

Open your browser to:
```
http://localhost:8000/docs
```

This gives you a full interactive API documentation where you can:
- See all endpoints
- Try each endpoint with parameters
- View request/response schemas

**Try it:**
1. Click on `GET /api/cluster/status`
2. Click "Try it out"
3. Click "Execute"
4. See the live response!

### Option 2: Alternative API Docs (ReDoc)

```
http://localhost:8000/redoc
```

Better for reading documentation.

---

## Python Testing Script

Run the comprehensive test script:

```powershell
cd c:\AI\aksarc-foundrylocal-aiops
python test_api.py
```

**Expected Output:**
```
🧪 Testing AKS Arc AI Ops API

1️⃣ Testing root endpoint...
   Status: 200
   Response: {'name': 'AKS Arc AI Ops Assistant', ...}

2️⃣ Testing health check...
   Status: 200
   Overall Status: healthy
   Services: {'kubernetes': True, 'context_buffer': True, ...}

...

✅ All tests completed successfully!
```

---

## Testing with curl (if you have it installed)

### Get cluster status
```bash
curl http://localhost:8000/api/cluster/status | jq
```

### Get pods
```bash
curl http://localhost:8000/api/cluster/pods | jq
```

### Get health
```bash
curl http://localhost:8000/api/health | jq
```

---

## Testing the Background Watcher

The watcher runs automatically and polls every 30 seconds. Watch the server logs:

```
{"pod_count": 9, "event_count": 0, "event": "cluster_status_retrieved", ...}
```

This appears every 30 seconds, showing the watcher is working.

---

## Creating Test Workloads in k3s

To generate more interesting events and pod activity:

### Deploy a test application
```powershell
kubectl run nginx-test --image=nginx:latest
```

### Watch it appear in the API
```powershell
# Wait a few seconds, then:
Invoke-RestMethod http://localhost:8000/api/cluster/pods | 
    Where-Object { $_.name -like "*nginx*" } | 
    ConvertTo-Json
```

### Create a failing pod (for testing events)
```powershell
kubectl run fail-test --image=invalid-image:latest
```

### Check for Warning events
```powershell
$events = Invoke-RestMethod "http://localhost:8000/api/cluster/events?hours=1&event_type=Warning"
$events | Select-Object type, reason, message | Format-Table -AutoSize
```

### Delete test pods
```powershell
kubectl delete pod nginx-test
kubectl delete pod fail-test
```

---

## Troubleshooting

### Server won't start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill the process if needed (replace PID)
taskkill /PID <PID> /F

# Try starting again
cd c:\AI\aksarc-foundrylocal-aiops\backend
python run.py
```

### Can't connect to Kubernetes
```powershell
# Verify k3d cluster is running
k3d cluster list

# Start it if stopped
k3d cluster start aiops-dev

# Test kubectl access
kubectl get nodes
```

### Python not found
```powershell
# Add Python to PATH for current session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verify Python
python --version
```

---

## Next Steps

Once you're comfortable with terminal testing, you can:

1. **Build a React frontend** - Connect to these APIs for a full UI
2. **Set up Foundry Local** - Test the AI chat functionality
3. **Deploy to AKS Arc** - Switch from k3s to production cluster
4. **Add authentication** - Secure the API endpoints
5. **Add WebSockets** - Get real-time push updates instead of polling

---

## Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info |
| `/api/health` | GET | Health check |
| `/api/cluster/status` | GET | Full cluster snapshot |
| `/api/cluster/pods` | GET | List pods (filter: namespace, phase) |
| `/api/cluster/events` | GET | Recent events (filter: hours, type) |
| `/api/cluster/pods/{ns}/{pod}/logs` | GET | Pod logs (param: tail_lines) |
| `/api/cluster/pods/{ns}/{pod}/history` | GET | Pod history (param: hours) |
| `/api/chat/query` | POST | AI assistant query |
| `/docs` | GET | Interactive API docs |
| `/redoc` | GET | API documentation |

**Happy Testing! 🚀**
