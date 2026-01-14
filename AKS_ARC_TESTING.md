# AKS Arc Enhancements - Testing Documentation

## Overview
This document provides comprehensive testing instructions for all AKS Arc enhancements implemented across Phases 1-5.

---

## What Was Implemented

### ✅ Phase 1: Platform Detection
- **Backend**: `kubernetes.py` - Added platform detection via labels, annotations, and namespaces
- **Frontend**: Platform badge in header (AKS Arc / k3s / Kubernetes)
- **API**: `GET /api/platform/detect`

### ✅ Phase 2: AKS Arc Diagnostics
- **Backend**: `aks_arc_diagnostics.py` - PowerShell Support.AksArc integration
- **Frontend**: AKS Arc info panel with diagnostics button
- **API**:
  - `GET /api/aksarc/diagnostics/check` - Check prerequisites
  - `POST /api/aksarc/diagnostics/install` - Install module
  - `GET /api/aksarc/diagnostics/run` - Run checks
  - `POST /api/aksarc/diagnostics/remediate` - Auto-fix

### ✅ Phase 3: Enhanced Topology
- **Backend**: `network_analyzer.py` - Network dependency analysis
- **Frontend**: Enhanced topology modal with communication matrix
- **API**: `GET /api/topology/analyze`

### ✅ Phase 4: Platform-Aware AI
- **Backend**: `routes.py` - Context-aware system prompt
- **Behavior**: AI adapts responses for AKS Arc and k3s

### ✅ Phase 5: UI/UX Enhancements
- **Frontend**: All CSS styling for new components
- **Components**: Platform badge, AKS Arc panel, diagnostic modals, enhanced topology

---

## Quick Start Testing

### 1. Start the Application
```powershell
cd c:\AI\aksarc-foundrylocal-aiops
.\run.ps1
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
{"event": "kubernetes_connected", ...}
```

### 2. Open Browser
Navigate to: **http://localhost:8000**

### 3. Visual Verification Checklist

#### On Page Load:
- [ ] Status badge turns green (🟢 Online)
- [ ] Platform badge appears next to status
  - AKS Arc: "☁️ AKS Arc" (blue)
  - k3s: "🚀 k3s" (orange)  
  - Kubernetes: "⎈ Kubernetes" (purple)
- [ ] Cluster stats populate (Pods, Nodes, Namespaces)
- [ ] AKS Arc panel appears below top bar (AKS Arc only)

---

## Detailed Test Cases

### Test 1: Platform Detection

#### 1.1 API Test
```powershell
# Call platform detection endpoint
curl http://localhost:8000/api/platform/detect | ConvertFrom-Json
```

**Expected (AKS Arc):**
```json
{
  "type": "aks-arc",
  "name": "my-cluster",
  "is_arc": true,
  "location": "eastus",
  "resource_id": "/subscriptions/.../microsoft.kubernetes/connectedclusters/..."
}
```

**Expected (k3s):**
```json
{
  "type": "k3s",
  "name": "k3s-node",
  "is_arc": false
}
```

**Expected (Vanilla k8s):**
```json
{
  "type": "kubernetes",
  "name": "kind-cluster",
  "is_arc": false
}
```

#### 1.2 UI Test
- [ ] Platform badge matches cluster type
- [ ] Badge colors are correct
- [ ] AKS Arc panel only shows for AKS Arc clusters

---

### Test 2: AKS Arc Info Panel (AKS Arc Only)

#### 2.1 Visual Verification
If cluster is AKS Arc, verify panel shows:
- [ ] "☁️ AKS Arc Cluster" header
- [ ] "🔍 Run Diagnostics" button
- [ ] Cluster name
- [ ] Location
- [ ] Resource ID

#### 2.2 Data Verification
```powershell
# Verify data matches detection
$platform = curl http://localhost:8000/api/platform/detect | ConvertFrom-Json
$platform.name
$platform.location
$platform.resource_id
```

Compare with UI display.

---

### Test 3: AKS Arc Diagnostics (AKS Arc Only)

#### 3.1 Prerequisites Check
```powershell
curl http://localhost:8000/api/aksarc/diagnostics/check | ConvertFrom-Json
```

**Expected:**
```json
{
  "powershell_available": true,
  "support_module_available": true/false,
  "message": "..."
}
```

#### 3.2 Module Installation (If Needed)
```powershell
# Requires admin PowerShell
curl -X POST http://localhost:8000/api/aksarc/diagnostics/install | ConvertFrom-Json
```

**Expected:**
```json
{
  "success": true,
  "message": "Support.AksArc module installed successfully"
}
```

#### 3.3 Run Diagnostics
```powershell
curl http://localhost:8000/api/aksarc/diagnostics/run | ConvertFrom-Json
```

**Expected:**
```json
{
  "total_tests": 15,
  "passed": 12,
  "failed": 3,
  "results": [
    {
      "test_name": "Test-KubernetesAgentConnectivity",
      "status": "Passed",
      "message": "All agents connected",
      "recommendation": null
    }
  ]
}
```

#### 3.4 UI Workflow Test
1. Click "🔍 Run Diagnostics" in AKS Arc panel
2. Modal opens
3. Diagnostics run automatically
4. Results display:
   - [ ] Summary shows pass/fail counts
   - [ ] Each test shows ✅ or ❌
   - [ ] Failed tests show recommendations
   - [ ] "🔧 Run Auto-Remediation" button appears if failures exist

#### 3.5 Remediation Test
```powershell
curl -X POST http://localhost:8000/api/aksarc/diagnostics/remediate | ConvertFrom-Json
```

**Expected:**
```json
{
  "success": true,
  "message": "Remediation completed"
}
```

Or click "🔧 Run Auto-Remediation" in UI.

---

### Test 4: Enhanced Network Topology

#### 4.1 API Test
```powershell
curl http://localhost:8000/api/topology/analyze | ConvertFrom-Json
```

**Expected Structure:**
```json
{
  "pods": [...],
  "services": [...],
  "dependencies": [
    {
      "service": "frontend",
      "namespace": "default",
      "service_ports": [
        {"protocol": "TCP", "port": 80, "target_port": 8080}
      ],
      "target_pods": ["frontend-abc", "frontend-def"]
    }
  ],
  "network_policies": [...],
  "network_policy_analysis": {
    "affected_pods": [...],
    "unrestricted_namespaces": [...]
  },
  "namespace_connectivity": {
    "default": ["default", "kube-system"],
    "production": ["production"]
  },
  "communication_matrix": [
    {
      "source": "frontend",
      "target": "backend",
      "protocol": "TCP",
      "port": 80,
      "target_port": 8080
    }
  ]
}
```

#### 4.2 UI Test
1. Click "🗺️ Topology" quick prompt card
2. Modal opens with enhanced view
3. Verify sections:
   - [ ] **Summary**: Shows counts (pods, services, dependencies, policies)
   - [ ] **Communication Matrix**: Source → Target flows with protocol:port
   - [ ] **Service Dependencies**: Cards with port mappings
   - [ ] **Network Policy Coverage**: Affected pods listed
   - [ ] **Namespace Connectivity**: Matrix of namespace-to-namespace access
4. Visual checks:
   - [ ] Arrows (→) between source and target
   - [ ] Protocol badges (e.g., "TCP:80") are colored
   - [ ] Port mappings show "80→8080" format
   - [ ] Warning box for unrestricted namespaces

---

### Test 5: Platform-Aware AI

#### 5.1 AKS Arc Test
1. Click "⚠️ Diagnostics" quick prompt
2. Or ask: *"What should I check if my cluster has issues?"*

**Expected Response Should Mention:**
- AKS Arc-specific diagnostic tools
- Azure Arc agent health
- Hybrid connectivity
- Azure-integrated monitoring
- Recommendation to use diagnostics panel

#### 5.2 k3s Test
Ask: *"Why do I see klipper-lb pods?"*

**Expected Response:**
- Explains klipper-lb is k3s-specific
- ServiceLB functionality
- Normal behavior for k3s

#### 5.3 Vanilla k8s Test
**Expected**: Standard Kubernetes guidance without platform-specific mentions

---

## Integration Testing

### Test 6: Full Workflow (AKS Arc)

**Scenario**: New user opens app on AKS Arc cluster

1. Open http://localhost:8000
   - [ ] Platform badge shows "☁️ AKS Arc"
   - [ ] AKS Arc panel displays below stats
2. Click "🔍 Run Diagnostics"
   - [ ] Modal opens
   - [ ] Diagnostics run automatically
   - [ ] Results categorized (pass/fail)
3. Click "🗺️ Topology"
   - [ ] Enhanced topology loads
   - [ ] Communication flows visible
   - [ ] Network policies analyzed
4. Ask AI: *"How do I troubleshoot Arc agent issues?"*
   - [ ] AI mentions AKS Arc diagnostics
   - [ ] Recommends diagnostic panel
   - [ ] Provides Arc-specific guidance

### Test 7: Cross-Platform Switching

If you have multiple cluster contexts:

```powershell
# Switch to AKS Arc
kubectl config use-context <aks-arc-context>
# Refresh browser → Should show AKS Arc

# Switch to k3s
kubectl config use-context <k3s-context>
# Refresh browser → Should show k3s

# Switch to vanilla k8s
kubectl config use-context <vanilla-k8s-context>
# Refresh browser → Should show Kubernetes
```

---

## Error Handling Tests

### Test 8: Error Scenarios

#### 8.1 No PowerShell
1. Temporarily rename `pwsh.exe`
2. Try diagnostics
   - [ ] Graceful error message displays

#### 8.2 Module Not Installed
1. Ensure Support.AksArc not installed
2. Click "Run Diagnostics"
   - [ ] Shows "Install Now" button
   - [ ] Installation works

#### 8.3 Cluster Disconnected
1. Stop kubeconfig access
2. Reload app
   - [ ] Status badge shows offline
   - [ ] Platform detection fails gracefully
   - [ ] No crashes

#### 8.4 No Network Policies
1. Connect to cluster without policies
2. View topology
   - [ ] Shows "0 Network Policies"
   - [ ] No errors displayed

---

## Performance Tests

### Test 9: Response Times

#### 9.1 Platform Detection
```powershell
Measure-Command { curl http://localhost:8000/api/platform/detect }
```
**Target**: < 2 seconds

#### 9.2 Topology Analysis
```powershell
Measure-Command { curl http://localhost:8000/api/topology/analyze }
```
**Target**: < 5 seconds (for < 100 pods)

#### 9.3 Diagnostic Run
```powershell
Measure-Command { curl http://localhost:8000/api/aksarc/diagnostics/run }
```
**Target**: 10-30 seconds (PowerShell execution time)

---

## Regression Tests

### Test 10: Existing Features

Verify nothing broke:

#### 10.1 Quick Prompts
- [ ] "🚀 Running Pods" - Works
- [ ] "💚 Health Check" - Works
- [ ] "🔄 Restarts" - Works
- [ ] "🖥️ Node Pools" - Works
- [ ] "⚙️ System Pods" - Works
- [ ] "⚠️ Diagnostics" - Works
- [ ] "🗺️ Topology" - Works

#### 10.2 Chat Interface
- [ ] Send message works
- [ ] AI responds
- [ ] Message history preserved
- [ ] Markdown formatting works

#### 10.3 Cluster Stats
- [ ] Pod count updates
- [ ] Node count updates
- [ ] Namespace count updates
- [ ] Stats refresh every 30s

#### 10.4 Foundry Control
- [ ] Model dropdown populates
- [ ] Start button works
- [ ] Stop button works
- [ ] Restart button works

---

## Browser Compatibility

### Test 11: Cross-Browser

Test on:
- [ ] **Chrome** (v120+)
- [ ] **Edge** (v120+)
- [ ] **Firefox** (v121+)
- [ ] **Safari** (v17+) - macOS only

Verify:
- [ ] Modals display correctly
- [ ] Platform badge renders
- [ ] CSS animations work
- [ ] Button clicks responsive

---

## Troubleshooting Guide

### Issue: Platform Not Detected
**Solution:**
```powershell
# Check logs for platform detection
# Should see: {"event": "platform_detected", "platform": "aks-arc"}

# Manually verify cluster labels
kubectl get nodes -o yaml | Select-String "kubernetes.azure.com/cluster"
```

### Issue: Diagnostics Fail
**Solution:**
```powershell
# Verify PowerShell
pwsh --version

# Check module manually
pwsh -Command "Get-Module -ListAvailable Support.AksArc"

# Run test manually
pwsh -Command "Test-SupportAksArcKnownIssues | ConvertTo-Json"
```

### Issue: Topology Empty
**Solution:**
```powershell
# Check if services exist
kubectl get services --all-namespaces

# Check if NetworkingV1Api is initialized
# Look for errors in server logs
```

### Issue: UI Not Updating
**Solution:**
```powershell
# Hard refresh browser
# Windows: Ctrl+F5
# Mac: Cmd+Shift+R

# Check browser console (F12 → Console)
# Look for JavaScript errors

# Check network tab for failed API calls
```

---

## Success Criteria

**All tests pass when:**
- ✅ Platform detection works for AKS Arc, k3s, and vanilla k8s
- ✅ Platform badge displays correctly
- ✅ AKS Arc panel appears only on AKS Arc
- ✅ Diagnostics module installs and runs
- ✅ Enhanced topology shows all new features
- ✅ AI provides platform-specific guidance
- ✅ No regressions in existing features
- ✅ Error handling is graceful
- ✅ Performance meets targets
- ✅ UI is responsive and clear

---

## Test Report Template

```
===========================================
AKS Arc Enhancements - Test Report
===========================================

**Date**: ___________
**Tester**: ___________
**Cluster Type**: [ ] AKS Arc [ ] k3s [ ] Kubernetes

**Results Summary**:
- Platform Detection: [ ] PASS [ ] FAIL
- AKS Arc Panel: [ ] PASS [ ] FAIL [ ] N/A
- Diagnostics: [ ] PASS [ ] FAIL [ ] N/A
- Enhanced Topology: [ ] PASS [ ] FAIL
- Platform-Aware AI: [ ] PASS [ ] FAIL
- Regression Tests: [ ] PASS [ ] FAIL

**Issues Found**:
1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

**Performance**:
- Platform Detection: _____ seconds
- Topology Analysis: _____ seconds
- Diagnostics Run: _____ seconds

**Overall Status**: [ ] PASS [ ] FAIL

**Notes**:
_____________________________________________
_____________________________________________
```

---

## Next Steps After Testing

1. ✅ Complete all test cases
2. 📝 Document any issues found
3. 🔧 Fix critical bugs
4. 📊 Review performance metrics
5. 👥 Share results with team
6. 📚 Update user documentation
7. 🚀 Deploy to production

---

**For Support**: Review backend logs and browser console for errors.
