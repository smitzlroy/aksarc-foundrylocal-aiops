# 🧪 Quick Testing Guide

## 🚀 Fastest Way to Test

### Option 1: One-Command Start (Recommended)
```powershell
.\start.ps1
```

This will:
- ✅ Check if k3s cluster is running (start it if needed)
- ✅ Verify kubectl access
- ✅ Check Python and dependencies
- ✅ Start the API server on http://localhost:8000

**Keep this terminal open!**

---

### Option 2: Interactive Testing Menu
Open a **new terminal** and run:
```powershell
.\test-interactive.ps1
```

This gives you a menu with options like:
1. Health Check
2. View Cluster Status
3. List All Pods
4. View Pod Logs
5. Deploy Test Pods
...and more!

---

### Option 3: Browser Dashboard
While the server is running, **double-click** on:
```
dashboard.html
```

This opens a beautiful web dashboard with:
- 📊 Real-time cluster statistics
- 📦 Pod list with filtering
- 📋 Pod logs viewer
- ⚡ Recent events
- 🔄 Auto-refresh every 30 seconds

---

### Option 4: API Explorer (Swagger UI)
Open your browser to:
```
http://localhost:8000/docs
```

Interactive API documentation where you can:
- See all endpoints
- Try them with a "Try it out" button
- View request/response examples

---

## 📝 Manual PowerShell Testing

```powershell
# Health check
Invoke-RestMethod http://localhost:8000/api/health | ConvertTo-Json

# Get all pods
$pods = Invoke-RestMethod http://localhost:8000/api/cluster/pods
$pods | Select-Object namespace, name, phase | Format-Table

# Get pod logs
Invoke-RestMethod "http://localhost:8000/api/cluster/pods/kube-system/coredns-ccb96694c-w9chf/logs?tail_lines=50"

# Filter by namespace
Invoke-RestMethod "http://localhost:8000/api/cluster/pods?namespace=kube-system"
```

---

## 🎯 Testing Scenarios

### Scenario 1: Watch Live Updates
1. Start server: `.\start.ps1`
2. Open dashboard: Double-click `dashboard.html`
3. In another terminal: `kubectl run nginx-test --image=nginx`
4. Watch the dashboard auto-refresh and show the new pod!
5. Delete it: `kubectl delete pod nginx-test`

### Scenario 2: View Pod Logs
1. Open interactive menu: `.\test-interactive.ps1`
2. Select "5. View Pod Logs"
3. Pick a pod from the list
4. See the logs instantly!

### Scenario 3: Monitor Events
1. Create a failing pod: `kubectl run fail-test --image=invalid-image`
2. Open dashboard or use interactive menu
3. View "Recent Events" to see the warning events

---

## 🛠️ Troubleshooting

### Server won't start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill the process (replace <PID>)
taskkill /PID <PID> /F
```

### k3s cluster not running
```powershell
# Check status
k3d cluster list

# Start it
k3d cluster start aiops-dev

# Verify
kubectl get nodes
```

### Python not found
The `start.ps1` script automatically adds Python to PATH. If it still doesn't work:
```powershell
# Manual PATH update
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verify
python --version
```

---

## 📚 Full Documentation

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing documentation.

---

## 🎉 Quick Win

**Want to see it working right now?**

1. Open PowerShell in this directory
2. Run: `.\start.ps1`
3. Wait for "Uvicorn running on http://0.0.0.0:8000"
4. Open your browser to: http://localhost:8000/docs
5. Click "GET /api/cluster/status" → "Try it out" → "Execute"
6. 🎊 You're seeing live data from your k3s cluster!

**That's it!** 🚀
