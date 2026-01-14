# Azure AI Foundry Local Integration Guide

## Overview

**Foundry Local** is the AI brain of this application. It provides the natural language understanding that allows you to ask questions about your Kubernetes cluster in plain English.

### What Foundry Local Does

- **Translates your questions** into Kubernetes queries
- **Analyzes cluster context** from the context buffer
- **Generates intelligent responses** about pod status, issues, and recommendations
- **Runs locally** - no cloud dependency for AI inference

### Current Status

✅ **Foundry Client**: Fully implemented and initialized  
⏳ **Foundry Endpoint**: Waiting for you to set up Azure AI Foundry Local  
✅ **API Endpoint Ready**: `/api/chat/query` is implemented and waiting for Foundry

---

## How It Works

```
┌─────────────┐
│   You Ask   │ "Why is my pod crashing?"
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  REST API       │  POST /api/chat/query
│  /api/chat/query│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Context Buffer  │  Last 24 hours of cluster state
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Foundry Local   │  AI analyzes context + question
│   (Your AI)     │  Generates intelligent answer
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Response      │  "Pod XYZ is crashing due to..."
└─────────────────┘
```

---

## Setting Up Foundry Local

### Prerequisites

1. **Azure AI Foundry** installed locally
2. **A language model** deployed (e.g., Phi-3, Llama, GPT-4)
3. **Endpoint URL** where Foundry is running

### Step 1: Install Azure AI Foundry Local

Follow Microsoft's official documentation to install Foundry Local:
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- Download and install the local runtime
- Set up your preferred AI model

### Step 2: Start Foundry Local

```powershell
# Example - your command may differ
foundry-local start --model phi-3-mini --port 11434
```

**Note your endpoint URL**, for example:
- `http://localhost:11434`
- `http://localhost:8080` 
- `http://127.0.0.1:5000`

### Step 3: Configure the Application

Edit `backend/.env`:

```dotenv
# Change these lines to match YOUR Foundry setup:
FOUNDRY_ENDPOINT=http://localhost:11434  # Your actual endpoint
FOUNDRY_MODEL=phi-3-mini                 # Your actual model name
FOUNDRY_TIMEOUT=60                       # Increase if needed
```

### Step 4: Verify Foundry is Running

Test manually:

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:11434/health"

# Or try the models endpoint
Invoke-RestMethod -Uri "http://localhost:11434/v1/models"
```

You should get a response (200 OK or similar) indicating Foundry is running.

### Step 5: Restart the Application

```powershell
# Stop the server (Ctrl+C if running)
# Then restart:
.\start.ps1
```

Check the logs - you should see:
```
{"event": "foundry_client_initialized", "endpoint": "http://localhost:11434", ...}
{"event": "foundry_health_check_success", ...}
```

---

## Testing Foundry Integration

### Option 1: Using the API Documentation

1. Start server: `.\start.ps1`
2. Open: http://localhost:8000/docs
3. Find **POST /api/chat/query**
4. Click "Try it out"
5. Enter a test query:
   ```json
   {
     "query": "Show me all running pods",
     "include_context": true,
     "max_history_hours": 1
   }
   ```
6. Click "Execute"

**Expected Response:**
```json
{
  "query": "Show me all running pods",
  "response": "Based on your cluster, you have 9 running pods:\n1. coredns-ccb96694c-w9chf in kube-system...",
  "timestamp": "2026-01-14T...",
  "context_used": {
    "pods": 9,
    "events": 0
  }
}
```

### Option 2: Using PowerShell

```powershell
$body = @{
    query = "What pods are in the kube-system namespace?"
    include_context = $true
    max_history_hours = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/chat/query" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

### Option 3: Using the Dashboard

1. Double-click `dashboard.html`
2. Look for the **"Chat"** or **"Query"** section
3. Type: "Show me pod status"
4. Press Enter
5. See AI-generated response

---

## Example Queries to Try

Once Foundry Local is connected, try these:

### Basic Queries
- "What pods are running?"
- "Show me pods in kube-system namespace"
- "Which pods have restarted?"

### Diagnostic Queries
- "Why is my pod crashing?"
- "What errors occurred in the last hour?"
- "Are there any unhealthy pods?"

### Analysis Queries
- "Summarize cluster health"
- "What's causing high resource usage?"
- "Show me recent events"

---

## How the Code Works

### The Chat Endpoint (`backend/src/api/routes.py`)

```python
@router.post("/chat/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest) -> ChatResponse:
    """
    1. Takes your natural language question
    2. Fetches recent cluster context (pods, events)
    3. Builds a prompt with context
    4. Sends to Foundry Local
    5. Returns AI-generated response
    """
```

### The Foundry Client (`backend/src/services/foundry.py`)

```python
class FoundryClient:
    async def query(self, prompt: str) -> str:
        """
        - Sends HTTP POST to Foundry Local
        - Uses OpenAI-compatible API format
        - Handles errors gracefully
        - Returns AI response text
        """
```

### The Context Building (`backend/src/api/routes.py`)

```python
# Gets last N hours of cluster state
context_snapshots = context_buffer.get_recent(hours=max_history_hours)

# Builds a prompt like:
"""
You are an AI assistant for Kubernetes operators.

Current Cluster State:
- 9 pods running
- Pod: coredns-ccb96694c-w9chf (Running, 1/1 ready)
- Pod: traefik-5d45fc8cc9-n94x7 (Running, 1/1 ready)
...

User Question: Why is my pod crashing?

Provide a helpful answer based on the cluster context.
"""
```

---

## Troubleshooting

### Issue: "Foundry health check failed"

**Cause:** Foundry Local is not running or wrong endpoint

**Fix:**
1. Start Foundry Local: `foundry-local start`
2. Verify endpoint: `Invoke-RestMethod -Uri "http://localhost:11434/health"`
3. Update `backend/.env` with correct endpoint
4. Restart server: `.\start.ps1`

### Issue: "Connection refused" error

**Cause:** Wrong port or endpoint

**Fix:**
1. Check Foundry Local logs for the actual port
2. Common ports: 11434 (Ollama), 5000, 8080, 1234
3. Update `FOUNDRY_ENDPOINT` in `.env`
4. Test: `Invoke-RestMethod -Uri "http://localhost:YOUR_PORT/health"`

### Issue: Chat queries return "Error querying AI"

**Cause:** Foundry is running but API format mismatch

**Fix:**
1. Check Foundry Local documentation for API format
2. The code uses OpenAI-compatible format:
   ```json
   {
     "model": "your-model",
     "messages": [{"role": "user", "content": "..."}],
     "temperature": 0.7,
     "max_tokens": 2048
   }
   ```
3. If your Foundry uses a different format, update `backend/src/services/foundry.py`

### Issue: Queries are slow

**Cause:** Model is too large or timeout too short

**Fix:**
1. Increase timeout in `.env`: `FOUNDRY_TIMEOUT=120`
2. Use a smaller/faster model (e.g., Phi-3-mini instead of Llama-70B)
3. Check Foundry Local has enough RAM/GPU

---

## Without Foundry Local

**The application still works!** All these features run fine:

✅ Kubernetes connection  
✅ Pod monitoring  
✅ Event tracking  
✅ Logs retrieval  
✅ REST API endpoints  
✅ Dashboard UI  
✅ Background watcher  

❌ **Only missing:** Natural language chat queries (`/api/chat/query`)

**Health check will show:**
```json
{
  "status": "healthy",
  "services": {
    "kubernetes": true,
    "context_buffer": true,
    "foundry": false  // ← Only this is false
  }
}
```

---

## Recommended Foundry Models

For this use case, consider:

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **Phi-3-mini** | 3.8B | ⚡ Fast | Good | Development/Testing |
| **Phi-3-medium** | 14B | 🔥 Medium | Better | Production (Small) |
| **Llama-3-8B** | 8B | 🔥 Medium | Great | Production (Medium) |
| **Llama-3-70B** | 70B | 🐢 Slow | Excellent | Production (Large) |

**Recommendation:** Start with **Phi-3-mini** for testing. It's fast and handles Kubernetes queries well.

---

## API Reference

### POST /api/chat/query

**Request:**
```json
{
  "query": "Your natural language question",
  "include_context": true,
  "max_history_hours": 1
}
```

**Response:**
```json
{
  "query": "Your question",
  "response": "AI-generated answer with cluster context",
  "timestamp": "2026-01-14T12:00:00Z",
  "context_used": {
    "pods": 9,
    "events": 0,
    "time_range": "1 hours"
  }
}
```

**Error Response:**
```json
{
  "detail": "Foundry Local is not available. Please check connection."
}
```

---

## Next Steps

1. **Install Azure AI Foundry Local** (if not already done)
2. **Deploy a model** (Phi-3-mini recommended for testing)
3. **Note the endpoint URL** and port
4. **Update `backend/.env`** with your Foundry endpoint
5. **Restart the server**: `.\start.ps1`
6. **Test with `/api/chat/query`** endpoint
7. **Try example queries** from the list above

---

## Summary

| Component | Status | Ready For |
|-----------|--------|-----------|
| Application Code | ✅ Complete | Foundry integration |
| Foundry Client | ✅ Implemented | Your endpoint |
| Chat Endpoint | ✅ Ready | Testing |
| Context Builder | ✅ Working | AI queries |
| **Your Action** | ⏳ Needed | Install Foundry Local |

**You're one step away!** Install Foundry Local, update `.env`, and start asking your cluster questions in natural language.
