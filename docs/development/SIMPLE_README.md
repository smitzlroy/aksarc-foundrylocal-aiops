# 🤖 K8s AI Assistant

**Chat with your Kubernetes cluster in natural language!**

Ask questions like:
- "Show me all running pods"
- "Are there any pods with errors?"
- "What happened in the last hour?"
- "Summarize cluster health"

---

## 🚀 Quick Start (2 Steps!)

### 1. Start the Server

```powershell
.\run.ps1
```

### 2. Open the Chat UI

Double-click **`index.html`** in your browser.

### 3. Start Foundry (From the UI!)

In the web interface, you'll see **"🤖 Foundry Control"**:
1. Select a model from the dropdown (e.g., `phi-3.5-mini`)
2. Click **"▶️ Start Foundry"**
3. Wait a few seconds for it to start
4. Start chatting!

**Or** start it manually first:
```powershell
foundry model run phi-3.5-mini
```

Or use the API docs at: http://localhost:8000/docs

---

## 💬 Using the Chat

### Foundry Controls (In the UI!)
- **▶️ Start Foundry** - Pick a model and start
- **⏹️ Stop Foundry** - Stop the AI service
- **🔄 Change Model** - Switch to a different model
- **Real-time status** - See if Foundry is running

### Quick Prompts (Click the cards!)
- **Running Pods** - See all active pods
- **Health Check** - Find pods with issues
- **Recent Restarts** - Check restart activity
- **Cluster Summary** - Overall health report
- **System Pods** - View kube-system namespace

### Or Ask Anything!

Type in natural language:
```
"Show me pods in default namespace"
"Which pods are using the most resources?"
"What errors occurred today?"
"Are all my pods healthy?"
```

---

## 📊 What It Does

1. **Monitors** your K8s cluster in real-time
2. **Remembers** 24 hours of cluster history
3. **Uses AI** (Foundry Local) to understand your questions
4. **Answers** with context about YOUR actual cluster

---

## 🛠️ Troubleshooting

### Foundry Controls Not Working
The UI can start/stop Foundry automatically! Just:
1. Make sure Foundry CLI is installed
2. Select a model from the dropdown
3. Click "Start Foundry"

### "Cannot connect to K8s"
```powershell
# Check your cluster:
kubectl get nodes

# If using k3d:
k3d cluster start aiops-dev
```

### "Python not found"
Install Python 3.11+: https://python.org

---

## 🎨 Features

✅ **Start/Stop Foundry from UI** - No terminal commands needed!  
✅ **Auto-detects** Foundry Local endpoint  
✅ **Model switching** - Change AI models without restarting  
✅ **Modern chat UI** with prompt cards  
✅ **Real-time** cluster stats  
✅ **24-hour** history buffer  
✅ **Background monitoring** (updates every 30s)  
✅ **REST API** with 14+ endpoints  

---

## 📁 Project Structure

```
├── run.ps1          ← Start this
├── index.html       ← Open this in browser
└── backend/
    ├── src/
    │   ├── main.py              ← FastAPI app
    │   ├── services/
    │   │   ├── kubernetes.py    ← K8s client
    │   │   ├── foundry.py       ← AI client
    │   │   ├── context.py       ← History buffer
    │   │   └── ai_detector.py   ← Auto-detection
    │   └── api/
    │       └── routes.py        ← REST endpoints
    └── .env         ← Config (auto-configured)
```

---

## 🔐 Security

- ✅ No credentials in code
- ✅ Uses local kubeconfig
- ✅ All AI processing happens locally
- ✅ No cloud dependencies
- ✅ `.env` file is gitignored

---

## 🌟 Example Questions

**Basic:**
- "List all pods"
- "Show me namespaces"
- "What nodes do I have?"

**Diagnostic:**
- "Which pods are not ready?"
- "Show me recent restarts"
- "Any pods in CrashLoopBackOff?"

**Analysis:**
- "What's wrong with my cluster?"
- "Summarize pod health"
- "What happened in the last hour?"

---

## 💡 Tips

- **Use quick prompts** for common questions
- **Be specific** for better answers
- **Check cluster stats** in the sidebar
- **Foundry stays running** - no need to restart it

---

## 📚 Documentation

- **Foundry Local**: https://learn.microsoft.com/azure/ai-foundry/foundry-local/get-started
- **API Docs**: http://localhost:8000/docs (when server running)
- **Security**: See `SECURITY_AUDIT.md`

---

## 🤝 Need Help?

1. Make sure Foundry is running: `foundry model list`
2. Check K8s access: `kubectl get nodes`
3. Check server logs for errors
4. Visit API docs: http://localhost:8000/docs

---

**Built with FastAPI, Azure AI Foundry Local, and Kubernetes Python Client**
