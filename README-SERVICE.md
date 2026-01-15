# AIOps Server - Background Service

This guide shows you how to run the AIOps server as a background service (without keeping a terminal open).

## Quick Start

### Start the Server
```powershell
.\start-service.ps1
```

The server will start in the background and continue running even if you close the terminal.

### Check Status
```powershell
.\status-service.ps1
```

### Stop the Server
```powershell
.\stop-service.ps1
```

## Access Points

Once the server is running:

- **Web UI**: http://localhost:8080/
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/api/health

## Troubleshooting

### Server won't start
1. Make sure no other process is using port 8080:
   ```powershell
   Get-NetTCPConnection -LocalPort 8080 -State Listen
   ```

2. Check if k3d cluster is running:
   ```powershell
   kubectl cluster-info
   ```

3. If cluster is down, start it:
   ```powershell
   k3d cluster start aiops-dev
   ```

### API shows "Offline" in UI
- Wait 15-20 seconds after starting for full initialization
- Refresh the browser page (Ctrl+F5 for hard refresh)
- Check status with: `.\status-service.ps1`

### Can't connect to cluster
If you see "Kubernetes client not initialized":
```powershell
# Restart the k3d cluster
k3d cluster stop aiops-dev
k3d cluster start aiops-dev

# Then restart the server
.\stop-service.ps1
.\start-service.ps1
```

## Manual Start (For Debugging)

If you need to see the server logs:

```powershell
cd backend
python run.py
```

This will run in the foreground with full log output.

## Configuration

Server configuration is in `backend/.env`:
- `API_PORT=8080` - API server port
- `FOUNDRY_ENDPOINT=http://localhost:11434` - Ollama/Foundry endpoint

## What Runs in Background

The `start-service.ps1` script:
1. Stops any existing server processes
2. Starts Python with `run.py` in a hidden window
3. The process continues running independently
4. No terminal window needs to stay open

## Automatic Restart on Reboot

To make the server start automatically on Windows boot:

1. Open Task Scheduler
2. Create a new Basic Task
3. Set trigger: "When I log on"
4. Set action: "Start a program"
5. Program: `powershell.exe`
6. Arguments: `-ExecutionPolicy Bypass -File "C:\AI\aksarc-foundrylocal-aiops\start-service.ps1"`
7. Save and test by logging out/in
