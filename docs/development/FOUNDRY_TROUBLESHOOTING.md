# Foundry Troubleshooting Guide

## Problem: Foundry Not Starting

### Symptoms
- Clicking "Start" on a model shows "Starting..." but never completes
- Foundry status stays "Not running" even after clicking Start
- No error messages shown in UI

### Root Cause
The Foundry Local SDK was hanging during model initialization because:
1. **GPU-optimized models require GPU hardware** - Models like `phi-4` use TensorRT GPU acceleration which isn't available on all systems
2. **No timeout** - The SDK would wait indefinitely for the model to load
3. **No error feedback** - Errors weren't being passed back to the UI

### Solution Applied
Fixed in `backend/src/services/foundry_manager.py`:

1. **Added 60-second timeout** for model loading:
```python
self._manager = await asyncio.wait_for(
    loop.run_in_executor(
        None,
        lambda: FoundrySDK(model_name)
    ),
    timeout=60.0  # Prevent hanging
)
```

2. **Improved error messages** for common failures:
```python
if "NvTensorRT" in error_msg or "GPU" in error_msg:
    error_msg = f"{model_name} requires GPU acceleration. Try qwen2.5-0.5b or qwen2.5-1.5b instead."
```

3. **Proper error propagation** to UI via API response

### Models That Work

✅ **Works on most hardware:**
- `qwen2.5-0.5b` - Smallest, fastest (0.52 GB)
- `qwen2.5-1.5b` - Good balance (1.25 GB)
- `qwen2.5-coder-0.5b` - For code tasks (0.52 GB)
- `qwen2.5-coder-1.5b` - Better code quality (1.25 GB)

❌ **Requires GPU with TensorRT:**
- `phi-4` - High-end GPU required (8.37 GB)
- `phi-3.5-mini` - Needs GPU
- `phi-3-mini-4k` - Needs GPU
- `phi-3-mini-128k` - Needs GPU

### How to Test the Fix

1. **Start the server:**
   ```powershell
   .\run.ps1
   ```

2. **Open UI:** http://localhost:8000

3. **Try qwen2.5-0.5b or qwen2.5-1.5b:**
   - Select from dropdown
   - Click "▶️ Start"
   - Should complete in 10-30 seconds

4. **If you try phi-4:**
   - Will now show error message after ~60 seconds:
   - "phi-4 requires GPU acceleration which isn't available. Try qwen2.5-0.5b or qwen2.5-1.5b instead."

### Expected Behavior Now

**Success case (qwen models):**
```
1. Click "Start" → Button shows "⏳ Starting..."
2. Wait 10-30 seconds
3. Alert: "✅ Foundry started successfully!"
4. Status changes to "✅ Foundry Running"
5. Can now chat with AI Mode
```

**Failure case (phi-4 without GPU):**
```
1. Click "Start" → Button shows "⏳ Starting..."
2. Wait up to 60 seconds (timeout)
3. Alert: "❌ Failed to start Foundry: phi-4 requires GPU acceleration..."
4. Button resets to "▶️ Start"
5. Can still use Direct Mode
```

### Verification Steps

Run this to check server logs:
```powershell
# Check if model started
curl http://localhost:8000/api/foundry/status | ConvertFrom-Json | Format-List

# Try starting a model (will timeout if GPU issue)
curl "http://localhost:8000/api/foundry/start?model=qwen2.5-0.5b" -Method POST | ConvertFrom-Json | Format-List
```

Expected output:
```
running        : True
model          : qwen2.5-0.5b
endpoint       : http://127.0.0.1:49187/v1
model_count    : 19
```

### Direct Mode Always Works

Even if Foundry won't start, **Direct Mode still provides value:**
- Uses keyword-based pattern matching
- No model download required
- Works instantly
- Handles common K8s queries:
  - "show pods"
  - "list services"
  - "pod status"
  - "node health"
  - "restart info"

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "requires GPU acceleration" | Model needs TensorRT GPU | Use qwen2.5-0.5b or qwen2.5-1.5b |
| "timeout" | Model taking >60s to load | Try smaller model |
| "Failed loading model" | Hardware incompatibility | Use CPU-optimized models |
| "Foundry not installed" | Missing Foundry Local | Install from Microsoft |

### Testing Checklist

- [ ] Server starts without errors
- [ ] UI loads at http://localhost:8000
- [ ] Direct Mode works (try "show pods")
- [ ] qwen2.5-0.5b starts successfully
- [ ] qwen2.5-1.5b starts successfully
- [ ] phi-4 shows proper error message (if no GPU)
- [ ] Error messages appear in UI alerts
- [ ] Status updates correctly after start/stop
- [ ] Can query models after successful start

### Next Steps

1. **Test with qwen2.5-0.5b** first (smallest, fastest)
2. **If successful**, try qwen2.5-1.5b for better quality
3. **Check logs** if issues persist: `cat backend/logs/app.log`
4. **Use Direct Mode** as fallback - it always works!

### Additional Resources

- [Foundry Local Documentation](https://learn.microsoft.com/en-us/azure/ai-services/foundry-local/)
- [QUICKSTART.md](./QUICKSTART.md) - How to start and use the application
- [FOUNDRY_SDK_INTEGRATION.md](./FOUNDRY_SDK_INTEGRATION.md) - Technical details
