# To-Do List for Tomorrow - January 16, 2026

## 1. Review Quick Actions and Their Value ⚡

**Objective**: Evaluate current Quick Actions for effectiveness and user value

**Current Quick Actions:**
- 🔍 Diagnostics
- 🗺️ Network Topology
- 📋 Recent Logs
- 🏥 Health Check

**Tasks:**
- [ ] Assess which Quick Actions are most frequently used
- [ ] Identify gaps - what critical actions are missing?
- [ ] Consider user workflows - do these match real troubleshooting patterns?
- [ ] Evaluate button placement and discoverability
- [ ] Review pre-filled prompts (Running Pods, Health Check, Diagnostics, Topology)

**Potential Improvements:**
- [ ] Add "Resource Usage" quick action (CPU/Memory at a glance)
- [ ] Add "Failed Pods" quick action (immediate problem identification)
- [ ] Add "Restart Pod" quick action (common remediation)
- [ ] Consider "Export Logs" or "Support Bundle" quick action
- [ ] Group by workflow: Observe → Diagnose → Remediate

---

## 2. AKS Arc Support Experience - "What to Do When..." 🆘

**Objective**: Create clear guidance for AKS Arc users when they need Microsoft support

### Current State:
- AKS Arc panel shows cluster info (name, location, resource ID)
- Diagnostics button available
- No explicit "support workflow" guidance

### Required Capabilities:

#### A. Check Diagnostics
- [ ] Enhance AKS Arc diagnostics panel with support-specific checks
- [ ] Add clear indicators: "Share these results with Microsoft Support"
- [ ] Include diagnostic correlation IDs for support tickets

#### B. Capture Logs
- [ ] **Support Bundle Generator** - One-click log collection
  - Cluster logs (control plane, nodes)
  - Pod logs (filtered by namespace/label)
  - Events (last 24-48 hours)
  - Resource manifests (deployments, services, configmaps)
  - Network policies and service mesh config
- [ ] Add "Download Support Bundle" button to AKS Arc panel
- [ ] Include timestamp and cluster ID in bundle filename
- [ ] Compress as `.zip` or `.tar.gz` for easy sharing

#### C. Review Azure Local Guidance
- [ ] Create dedicated "Azure Local Health" section
  - Azure Arc connectivity status
  - Extension health (Azure Monitor, Defender, etc.)
  - Resource sync status (Azure Resource Manager)
  - Certificate expiration warnings
- [ ] Add contextual help: "Common Azure Local Issues"
  - Network connectivity problems
  - Certificate renewal failures
  - Extension update issues
  - Resource sync delays
- [ ] Link to Azure Local documentation and troubleshooting guides

#### D. Microsoft Support Integration
- [ ] **Support Request Helper**
  - Button: "Contact Microsoft Support"
  - Pre-fill support ticket template with:
    - Cluster details (name, region, subscription)
    - Problem description (from diagnostics)
    - Diagnostic results summary
    - Links to relevant logs
  - Generate support case number placeholder
- [ ] **Proactive Support Suggestions**
  - AI analyzes diagnostics and suggests: "This looks like a known issue - see KB article XXXXX"
  - "Similar issues resolved by: [suggested action]"

#### E. Additional "What to Do" Features
- [ ] **Guided Troubleshooting Wizard**
  - "What problem are you experiencing?"
    - Pods not starting → Check resource limits, image pulls, node capacity
    - Network connectivity issues → Check services, network policies, DNS
    - Performance problems → Check resource usage, HPA, node health
    - Azure Arc issues → Check extensions, connectivity, certificates
- [ ] **Health Dashboard** with traffic lights (Green/Yellow/Red)
  - Control plane health
  - Node health
  - Azure Arc connectivity
  - Extension status
  - Certificate validity
- [ ] **Quick Fixes Panel**
  - "Restart failing pod"
  - "Scale deployment"
  - "Re-sync Azure Arc"
  - "Refresh extensions"

### UI Mockup Ideas:
```
┌─────────────────────────────────────────┐
│ ☁️ AKS Arc Cluster - [cluster-name]     │
│ ⚠️ Need Help? Microsoft Support Guide  │
├─────────────────────────────────────────┤
│ 1️⃣ Run Diagnostics                     │
│    [🔍 Run Full Diagnostics]            │
│    Status: ✅ Healthy (Last: 5m ago)    │
│                                         │
│ 2️⃣ Capture Support Bundle              │
│    [📦 Download Logs & Config]          │
│    Includes: Logs, Events, Manifests   │
│                                         │
│ 3️⃣ Azure Local Health                  │
│    Arc Connectivity: ✅ Connected       │
│    Extensions: ✅ 4/4 Healthy           │
│    Certificates: ⚠️ Expires in 45 days │
│    [View Details]                       │
│                                         │
│ 4️⃣ Contact Microsoft Support           │
│    [🎫 Open Support Ticket]             │
│    Case #: [Auto-generated]             │
└─────────────────────────────────────────┘
```

---

## 3. SLM / Chat Interface - Kubernetes Actions 🤖

**Objective**: Enable AI chat to perform cluster modifications, not just observations

### Current Capability:
- ✅ Read operations (get pods, logs, status, topology)
- ❌ Write operations (create, update, delete)

### Proposed Write Operations:

#### A. Pod/Deployment Management
- [ ] **Create Pod**
  - User: "Create a pod running nginx"
  - AI: Generates YAML → Shows preview → User confirms → Applies
- [ ] **Update Replicas**
  - User: "Scale my-app to 5 replicas"
  - AI: `kubectl scale deployment my-app --replicas=5`
- [ ] **Restart Deployment**
  - User: "Restart the api-gateway deployment"
  - AI: `kubectl rollout restart deployment/api-gateway`
- [ ] **Delete Resource**
  - User: "Delete the test-pod in namespace dev"
  - AI: Shows confirmation prompt → Deletes if approved

#### B. Configuration Management
- [ ] **Update ConfigMap**
  - User: "Update config-map key 'timeout' to '60s'"
  - AI: Fetches current config → Modifies → Shows diff → Applies
- [ ] **Create Secret**
  - User: "Create secret db-password with value from clipboard"
  - AI: Generates secret manifest → Base64 encodes → Applies
- [ ] **Update Environment Variables**
  - User: "Add env var LOG_LEVEL=debug to my-app"
  - AI: Patches deployment with new env var

#### C. Resource Scheduling
- [ ] **Create Job**
  - User: "Run a one-time job to migrate database"
  - AI: Generates Job YAML with user-specified image/command
- [ ] **Create CronJob**
  - User: "Schedule nightly backup at 2am"
  - AI: Creates CronJob with cron expression

#### D. Networking
- [ ] **Expose Service**
  - User: "Expose my-app on port 8080"
  - AI: `kubectl expose deployment my-app --port=8080`
- [ ] **Create Ingress**
  - User: "Create ingress for my-app.example.com"
  - AI: Generates Ingress manifest → Applies

#### E. Safety & Permissions
- [ ] **Confirmation Prompts**
  - All write operations require explicit user confirmation
  - Show preview of changes before applying
  - "Are you sure you want to delete [resource]? This cannot be undone."
- [ ] **Dry-Run Mode**
  - User can see what would happen without applying changes
  - "Preview Changes" button before "Apply"
- [ ] **Audit Trail**
  - Log all AI-initiated actions with timestamp, user, command
  - Exportable audit log for compliance
- [ ] **RBAC Integration**
  - Respect user's Kubernetes RBAC permissions
  - If user can't delete pods, AI can't delete pods on their behalf
  - Show permission errors clearly: "You don't have permission to..."

#### F. AI-Assisted Manifest Generation
- [ ] **Natural Language → YAML**
  - User: "Create a deployment with 3 replicas, nginx image, expose port 80"
  - AI: Generates complete YAML
  - User: Reviews, edits, applies
- [ ] **Interactive Builder**
  - AI asks clarifying questions:
    - "What image do you want to use?"
    - "How many replicas?"
    - "What resource limits? (default: 500m CPU, 512Mi memory)"
  - Builds manifest step-by-step

### Backend Implementation:
```python
# New endpoint: /api/actions/apply
@router.post("/actions/apply")
async def apply_action(action: ActionRequest):
    """
    Apply Kubernetes action based on AI intent
    - Validates action safety
    - Checks RBAC permissions
    - Logs to audit trail
    - Executes kubectl command
    """
    pass

# Example ActionRequest:
# {
#   "intent": "create_pod",
#   "resource_type": "pod",
#   "namespace": "default",
#   "manifest": {...},  # Generated YAML as dict
#   "dry_run": false
# }
```

### UI Mockup:
```
User: "Scale my-app to 10 replicas"

AI Response:
┌───────────────────────────────────────┐
│ 🤖 I'll scale deployment 'my-app'    │
│    from 3 to 10 replicas              │
│                                       │
│ Command:                              │
│ kubectl scale deployment/my-app \     │
│   --replicas=10 -n production         │
│                                       │
│ [Preview Changes] [Cancel] [✅ Apply] │
└───────────────────────────────────────┘
```

---

## 4. Review Additional Value - "Deploy Applications" 🚀

**Objective**: Explore high-value features beyond troubleshooting

### A. Application Deployment Wizard
- [ ] **One-Click App Deployment**
  - Curated marketplace of common apps:
    - 🗄️ PostgreSQL/MySQL/Redis
    - 🔍 Elasticsearch + Kibana
    - 📊 Prometheus + Grafana
    - 🔐 cert-manager
    - 🌐 NGINX Ingress Controller
  - User selects app → AI generates manifests → Deploys with one click
  - Includes sensible defaults (resource limits, storage, replicas)

- [ ] **Helm Chart Integration**
  - User: "Install WordPress using Helm"
  - AI: Searches Helm repos → Presents options → Installs with `helm install`
  - Shows values.yaml for customization

- [ ] **GitOps Integration**
  - Connect to Git repo (GitHub, GitLab, Azure DevOps)
  - User: "Deploy my app from github.com/user/repo"
  - AI: Reads repo → Detects Dockerfile/K8s manifests → Deploys
  - Sets up CI/CD pipeline (optional)

### B. Application Management
- [ ] **App Catalog / Installed Apps**
  - Dashboard showing all deployed applications
  - Grouped by namespace or label
  - Status: Healthy / Degraded / Failed
  - Quick actions: View logs, Scale, Restart, Delete

- [ ] **Blue/Green Deployments**
  - User: "Deploy new version of my-app (blue/green)"
  - AI: Creates new deployment → Waits for health → Switches traffic → Removes old

- [ ] **Rollback Capability**
  - User: "Rollback my-app to previous version"
  - AI: `kubectl rollout undo deployment/my-app`

### C. Resource Optimization
- [ ] **Right-Sizing Recommendations**
  - AI analyzes actual CPU/memory usage
  - Suggests: "Your app is using 100m CPU but requested 1000m - consider reducing"
  - One-click apply optimized resource requests

- [ ] **Cost Analysis**
  - Show estimated costs per namespace/app (if using AKS with Azure Cost Management)
  - "Your 'dev' namespace is costing $X/month - consider scaling down non-critical workloads"

### D. Disaster Recovery
- [ ] **Backup & Restore**
  - User: "Backup all resources in namespace prod"
  - AI: Exports all YAML manifests to timestamped bundle
  - User: "Restore from backup-2026-01-15.zip"
  - AI: Re-applies all manifests

- [ ] **Cluster Snapshot**
  - Full cluster state export (all namespaces, resources)
  - Useful for migrations or disaster recovery

### E. Developer Experience
- [ ] **Local Development Helpers**
  - "Port-forward my-app to localhost:8080"
  - "Open shell in pod my-app-abc123"
  - "Copy file from pod to local machine"

- [ ] **Rapid Prototyping**
  - User: "Create a dev environment for testing my Python app"
  - AI: Creates namespace, deployment, service, ingress
  - Provides access URL: "Your app is live at http://dev-myapp.local"

### F. Multi-Cluster Management
- [ ] **Cluster Switcher**
  - If user has multiple kubeconfigs
  - "Switch to production cluster"
  - "Compare resources between dev and prod"

- [ ] **Cross-Cluster Deployment**
  - "Deploy my-app to all clusters (dev, staging, prod)"
  - Handles environment-specific configs

### G. Compliance & Security
- [ ] **Security Scanning**
  - Scan container images for vulnerabilities
  - "Check if my-app has any CVEs"
  - Integration with Trivy or similar tools

- [ ] **Policy Enforcement**
  - "Are all pods running as non-root?"
  - "Do all deployments have resource limits?"
  - OPA/Gatekeeper integration

---

## Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Quick Actions Review | Medium | Low | **P1** |
| AKS Arc Support Workflow | High | Medium | **P0** |
| Support Bundle Generator | High | Medium | **P0** |
| Azure Local Health Panel | High | Low | **P1** |
| Chat Write Operations (Scale/Restart) | High | Medium | **P1** |
| Pod/Deployment Creation via Chat | High | High | **P2** |
| App Deployment Wizard | Medium | High | **P2** |
| Helm Integration | Medium | Medium | **P2** |
| Backup & Restore | Medium | Medium | **P3** |
| Security Scanning | Low | High | **P3** |

---

## Success Metrics

**Quick Actions (Goal 1):**
- [ ] 80% of users engage with Quick Actions within first 2 minutes
- [ ] Reduce "time to first diagnostic" by 50%

**AKS Arc Support (Goal 2):**
- [ ] Support bundle generation takes <30 seconds
- [ ] 100% of critical diagnostics included in bundle
- [ ] Clear "next steps" provided in 90% of error scenarios

**Chat Actions (Goal 3):**
- [ ] Users can scale deployments via chat with 100% accuracy
- [ ] <5 second latency from chat command to Kubernetes action
- [ ] Zero accidental deletions (confirmation prompts work)

**Deploy Applications (Goal 4):**
- [ ] Users can deploy common apps (nginx, postgres) in <2 minutes
- [ ] 95% success rate for automated deployments
- [ ] Generated manifests follow best practices (resource limits, health checks)

---

## Technical Debt / Prerequisites

Before implementing above features:
- [ ] Ensure backend has proper RBAC checking
- [ ] Add rate limiting to prevent accidental mass actions
- [ ] Implement audit logging for all write operations
- [ ] Add unit tests for action validation
- [ ] Document security model and permission boundaries
- [ ] Add feature flags to enable/disable write operations

---

## Demo Preparation for Leadership

**Story Arc:**
1. **Problem**: AKS Arc cluster has an issue, user doesn't know what to do
2. **Quick Actions**: User clicks "Diagnostics" → Immediate insights
3. **Support Workflow**: User clicks "Download Support Bundle" → Ready for Microsoft Support
4. **Azure Local**: User sees Arc health dashboard → Identifies certificate expiring soon
5. **Remediation via Chat**: User says "Restart failing pod" → AI executes safely
6. **Deploy New App**: User says "Deploy Redis" → AI generates manifests → App running in 30 seconds

**Tagline**: "From detection to resolution - all in natural language, all with Foundry Local."

---

*Generated: January 15, 2026*
*Next Review: January 16, 2026*
