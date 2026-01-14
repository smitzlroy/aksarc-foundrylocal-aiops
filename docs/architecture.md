# Quick Reference: Application Architecture

## What You Have Now (Working)

```
┌──────────────────────────────────────────────────────────┐
│                    YOUR SETUP                             │
│                                                           │
│  ┌─────────────┐         ┌──────────────┐               │
│  │  dashboard  │────────▶│  FastAPI     │               │
│  │  .html      │         │  Server      │               │
│  └─────────────┘         │  :8000       │               │
│        │                 └───────┬──────┘               │
│        │                         │                       │
│        ▼                         ▼                       │
│  ┌─────────────┐         ┌──────────────┐               │
│  │   Browser   │         │  REST API    │               │
│  │   Testing   │         │  11 Endpoints│               │
│  └─────────────┘         └───────┬──────┘               │
│                                   │                       │
│        ┌──────────────────────────┼──────────────┐       │
│        │                          │              │       │
│        ▼                          ▼              ▼       │
│  ┌──────────┐             ┌────────────┐  ┌─────────┐  │
│  │ K8s      │◀────────────│  Context   │  │ Foundry │  │
│  │ Client   │             │  Buffer    │  │ Client  │  │
│  │ (Active) │             │  (Active)  │  │ (Ready) │  │
│  └────┬─────┘             └────────────┘  └─────────┘  │
│       │                         ▲              │         │
│       │                         │              │         │
│       ▼                         │              ▼         │
│  ┌──────────┐           ┌──────┴──────┐   ┌─────────┐  │
│  │  k3s     │           │ Background  │   │ Foundry │  │
│  │ Cluster  │           │  Watcher    │   │  Local  │  │
│  │ 9 pods   │           │  (Every 30s)│   │ (TODO)  │  │
│  └──────────┘           └─────────────┘   └─────────┘  │
│     ✅                        ✅                ⏳       │
└──────────────────────────────────────────────────────────┘
```

## Component Status

| Component | Status | What It Does |
|-----------|--------|--------------|
| **FastAPI Server** | ✅ Running | Serves REST API on port 8000 |
| **Kubernetes Client** | ✅ Connected | Talks to k3s, gets pods/events |
| **Context Buffer** | ✅ Active | Stores 24h of cluster history |
| **Background Watcher** | ✅ Polling | Updates every 30 seconds |
| **REST API** | ✅ Working | 11 endpoints for cluster data |
| **Dashboard UI** | ✅ Ready | HTML file with live updates |
| **Foundry Client** | ✅ Ready | Waiting for Foundry endpoint |
| **Foundry Local** | ⏳ TODO | You need to install this |

## Data Flow Examples

### Example 1: Get Pod List
```
User → Browser → GET /api/cluster/pods 
                    ↓
              Kubernetes Client → k3s cluster
                    ↓
              Returns 9 pods → User sees list
```

### Example 2: Background Monitoring
```
Every 30s: Background Watcher → Kubernetes Client → Get cluster status
                                      ↓
                                Context Buffer (stores snapshot)
                                      ↓
                                Available for queries
```

### Example 3: Chat Query (Once Foundry is set up)
```
User → "Why is my pod failing?" → POST /api/chat/query
                                      ↓
                                Context Buffer → Get last 1 hour
                                      ↓
                                Build prompt with context
                                      ↓
                                Foundry Local → AI analyzes
                                      ↓
                                Returns answer → User
```

## File Locations

```
c:\AI\aksarc-foundrylocal-aiops\
│
├── start.ps1              ← Start the server (TESTED ✅)
├── dashboard.html         ← Web UI (READY ✅)
├── START.md              ← Instructions (YOU ARE HERE)
├── FOUNDRY_SETUP.md      ← Foundry instructions (NEXT STEP)
│
├── backend\
│   ├── .env              ← Configuration (UPDATE for Foundry)
│   ├── run.py            ← Entry point
│   │
│   └── src\
│       ├── main.py       ← FastAPI app
│       ├── api\
│       │   └── routes.py ← REST endpoints
│       └── services\
│           ├── kubernetes.py  ← K8s client ✅
│           ├── context.py     ← Context buffer ✅
│           └── foundry.py     ← Foundry client ⏳
```

## What Works Right Now

### ✅ Available Endpoints (Test at http://localhost:8000/docs)

1. **GET /api/health** - Check service status
2. **GET /api/cluster/status** - Full cluster state with pods
3. **GET /api/cluster/pods** - List pods (filterable)
4. **GET /api/cluster/events** - Recent cluster events
5. **GET /api/cluster/pods/{ns}/{pod}/logs** - Pod logs
6. **GET /api/context/recent** - Recent cluster snapshots
7. **GET /api/context/range** - Snapshots in time range
8. **GET /api/context/pod-history/{ns}/{pod}** - Pod history
9. **GET /api/context/events** - Events by type
10. **GET /api/context/stats** - Context buffer statistics

### ⏳ Waiting for Foundry

11. **POST /api/chat/query** - Natural language queries
    - Code is ready ✅
    - Needs Foundry Local endpoint ⏳

## Quick Commands

### Start Server
```powershell
.\start.ps1
```

### Test Health
```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

### Get All Pods
```powershell
Invoke-RestMethod http://localhost:8000/api/cluster/pods | ConvertTo-Json -Depth 3
```

### View Dashboard
```
Double-click dashboard.html
```

### Set Up Foundry (Next Step)
```
Read FOUNDRY_SETUP.md
```

## Timeline

✅ **DONE** - Kubernetes integration working  
✅ **DONE** - Context buffer tracking cluster state  
✅ **DONE** - REST API serving data  
✅ **DONE** - Background watcher monitoring  
✅ **DONE** - Dashboard UI ready  
⏳ **TODO** - Install Foundry Local (your action)  
⏳ **TODO** - Configure Foundry endpoint in .env  
⏳ **TODO** - Test natural language queries  

## Need Help?

- **Server issues**: See `START.md` troubleshooting section
- **Foundry setup**: See `FOUNDRY_SETUP.md` complete guide
- **API testing**: Go to http://localhost:8000/docs
- **Security**: See `SECURITY_AUDIT.md` for best practices
