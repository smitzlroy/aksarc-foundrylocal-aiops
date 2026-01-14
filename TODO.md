# K8s AI Assistant - TODO List

## Priority Items

### 1. Fix automated browser opening in run.ps1
- **Issue**: Background job interferes with server process
- **Solution**: Use Start-Process with -PassThru and proper detachment
- **Status**: Not started

### 2. Show downloaded vs available models ✅ IN PROGRESS
- **Backend**: Updated `_parse_available_models()` to return model objects with `downloaded` flag
- **Frontend**: Need to update UI to show ⬇️ icon for downloaded models
- **Status**: In progress

### 3. Dark theme ✅ IN PROGRESS
- **CSS**: Started updating color scheme with CSS variables
- **Status**: In progress

### 4. AKS Arc-specific features ✅ IN PROGRESS
- **Control Plane Health**: Monitor API server, etcd, controller-manager
- **Node Pool Status**: Track node pool scaling, health, upgrades
- **Diagnostic Logs**: Easy access to cluster diagnostics
- **Arc Agent Status**: Monitor Arc agents and extensions
- **Status**: Design phase

## AKS Arc Value-Add Features

### Control Plane Monitoring
- API server response time
- Controller manager health
- Scheduler health
- etcd cluster status

### Node Pool Management
- Scale operations
- Upgrade status
- Node health per pool
- Taints and labels

### Diagnostics & Troubleshooting
- Quick access to diagnostic logs
- Common issue detection
- Automated remediation suggestions
- Log aggregation

### Arc-Specific
- Arc agent health
- Extension status
- Connected cluster status
- Azure policy compliance
