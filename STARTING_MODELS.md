# Starting AI Models (Foundry Local)

## Quick Start - Get Models Running

The topology and other features work WITHOUT AI models, but for the chat/natural language features, you need to start Foundry Local **with a model selected**.

### Important: You MUST Select a Model First

Foundry Local requires you to specify which AI model to run. You cannot start Foundry without selecting a model first.

### Check if Foundry is Running

Open http://localhost:8080/ and look at the **Foundry Control** panel (top-right). 

**Status Indicators:**
- 🔴 **Offline** = Foundry not running (you'll see model dropdown)
- 🟢 **Online** = Foundry running with a model loaded

### Start Foundry Local with a Model

**Option 1: From the Web UI (Easiest)**
1. Open http://localhost:8080/
2. Look at the **Foundry Control** panel (top-right)
3. Click the model dropdown - you'll see two groups:
   - **✅ Downloaded & Ready** - These start instantly (no download wait)
   - **📦 Available to Download** - Will download on first use (may take minutes)
4. **Select a model** from the dropdown (e.g., "phi-4" or "qwen2.5-1.5b")
5. Click **"▶️ Start"** button
6. Wait 10-30 seconds for the model to load into memory
7. Status will change to 🟢 "Running: [model-name]"

**Option 2: From Command Line**
```powershell
# Start Foundry with a specific model
foundry run phi-4                    # 8GB model (good quality)
foundry run qwen2.5-1.5b             # 1.25GB model (faster)
foundry run qwen2.5-0.5b             # 0.52GB model (smallest)

# The model will download if not already on your system
```

### Downloaded vs Available Models

The web UI shows which models are:
- **✅ Downloaded & Ready**: Already on your disk, starts in seconds
- **📦 Available to Download**: Will download from internet on first use

**Your Downloaded Models** (from your screenshot):
- ✅ phi-4 (8.37 GB) - High quality, recommended
- ✅ qwen2.5-0.5b (0.52 GB) - Tiny, very fast
- ✅ qwen2.5-1.5b (1.25 GB) - Small, good balance

### Troubleshooting

**"Loading models..." never finishes**
- Foundry might not be installed. Check: `foundry --version`
- If not installed, download from: https://aka.ms/azureai/foundry/local

**Model list is empty**
- The server couldn't connect to Foundry Local
- Make sure Foundry is installed and accessible on your system

**"Start" button doesn't work**
- Check the browser console (F12) for errors
- The API might not be responding - verify server is running at http://localhost:8080/api/health

**Foundry uses too much memory**
- Use a smaller model like "qwen2.5-0.5b" (only 0.52 GB)
- Or run without AI and just use the topology/diagnostics features

## Using the Chat Feature

Once Foundry is running:
1. Type a question in the chat box at the bottom
2. Example questions:
   - "Show me all pods"
   - "What pods are failing?"
   - "List all services"
   - "Get logs for nginx pod"

## Using Without AI

All these features work WITHOUT starting Foundry:
- ✅ Network Topology visualization
- ✅ Cluster diagnostics
- ✅ Pod/Service listing
- ✅ Health checks
- ✅ Quick actions

Only the **natural language chat** requires Foundry to be running.

---

**Need Help?** 
- Check Foundry status: http://localhost:8080/
- View API health: http://localhost:8080/api/health
- Foundry docs: https://aka.ms/azureai/foundry/docs
