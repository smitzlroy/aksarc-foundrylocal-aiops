# 🎮 UI Controls Guide

## Foundry Control Panel

The web UI now includes a **Foundry Control Panel** in the sidebar:

### Status Display
```
🤖 Foundry Control
━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Running: phi-3.5-mini
http://127.0.0.1:59624/
```

Shows:
- ✅ **Running status** (🟢 running, 🔴 stopped, ❌ not installed)
- ✅ **Current model** name
- ✅ **Endpoint URL**

### Model Selection
```
📦 Select Model
├── phi-3.5-mini ⭐ (Recommended)
├── phi-4-mini
├── qwen2.5-0.5b (Fastest)
├── qwen2.5-1.5b
├── mistral-7b-v0.2
└── ... and more
```

Choose from all installed Foundry models.

### Control Buttons

#### ▶️ Start Foundry
- Starts Foundry with selected model
- Takes ~5 seconds to initialize
- Shows notification when ready

#### ⏹️ Stop Foundry
- Stops the currently running Foundry instance
- Confirms before stopping
- Clears chat context

#### 🔄 Change Model
- Stops current model
- Starts with newly selected model
- Preserves chat history

---

## How It Works

### Starting Foundry
1. Select model: `phi-3.5-mini`
2. Click **"▶️ Start Foundry"**
3. Wait for: 🟢 Running
4. Start chatting!

### Changing Models
1. Select new model: `phi-4-mini`
2. Click **"🔄 Change Model"**
3. Confirm restart
4. Wait for initialization
5. Continue chatting with better model!

### Stopping
1. Click **"⏹️ Stop Foundry"**
2. Confirm
3. Foundry stops (saves memory)

---

## API Endpoints (For Advanced Users)

### Check Status
```powershell
Invoke-RestMethod http://localhost:8000/api/foundry/status
```

Returns:
```json
{
  "running": true,
  "installed": true,
  "endpoint": "http://127.0.0.1:59624/",
  "model": "phi-3.5-mini",
  "available_models": ["phi-3.5-mini", "phi-4-mini", ...],
  "message": "Foundry Local is running"
}
```

### Start Model
```powershell
Invoke-RestMethod -Method POST "http://localhost:8000/api/foundry/start?model=phi-3.5-mini"
```

### Stop
```powershell
Invoke-RestMethod -Method POST http://localhost:8000/api/foundry/stop
```

### Restart with Different Model
```powershell
Invoke-RestMethod -Method POST "http://localhost:8000/api/foundry/restart?model=phi-4-mini"
```

---

## Model Recommendations

### For Chat (Recommended)
- **phi-3.5-mini** - Best balance of speed and quality
- **phi-4-mini** - Better understanding, slightly slower
- **mistral-7b-v0.2** - Excellent quality, needs more RAM

### For Speed
- **qwen2.5-0.5b** - Fastest, good for simple queries
- **qwen2.5-1.5b** - Fast with better quality

### For Best Quality
- **phi-4** - Highest quality, requires good GPU
- **deepseek-r1-14b** - Reasoning model, excellent for analysis

---

## Benefits of UI Control

✅ **No Terminal Commands** - Everything in the browser  
✅ **Visual Feedback** - See status in real-time  
✅ **Easy Model Switching** - Try different models  
✅ **One-Click Start/Stop** - Simple control  
✅ **Auto-Detection** - Finds Foundry automatically  
✅ **Status Monitoring** - Know when Foundry is ready

---

## Workflow

### Initial Setup
```
1. Run: .\run.ps1
2. Open: index.html
3. Select model: phi-3.5-mini
4. Click: ▶️ Start Foundry
5. Chat with your cluster!
```

### Daily Use
```
1. Open: index.html
2. If Foundry not running, click: ▶️ Start
3. Chat!
```

### When Done
```
1. Click: ⏹️ Stop Foundry
2. Or just close browser (Foundry keeps running)
```

---

## Troubleshooting

### "Foundry not installed"
Install Foundry Local:
```powershell
# Follow: https://learn.microsoft.com/azure/ai-foundry/foundry-local/get-started
```

### Start button disabled
- Check if Foundry CLI is installed: `foundry --version`
- Make sure models are downloaded: `foundry model list`

### Models not showing
- Run once: `foundry model list`
- This triggers model catalog download

### Foundry won't start
- Try starting manually first: `foundry model run phi-3.5-mini`
- Check logs in the browser console (F12)

---

**No more terminal commands needed! Everything is in the UI! 🎉**
