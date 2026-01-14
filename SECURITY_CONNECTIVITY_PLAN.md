# Security & Connectivity Features - Implementation Plan

## Current Status Assessment

### ✅ What's Working
- **Direct Mode**: Natural language queries working perfectly (no AI needed)
- **Model Detection**: 3 models downloaded and detected (phi-4, qwen2.5-0.5b, qwen2.5-1.5b)
- **Basic K8s Queries**: Pod lists, node info, cluster status
- **Network Topology View**: Basic visualization exists

### ❌ What's Not Working
- **SLM/Foundry Integration**: Models downloaded but service won't start (external Azure API issue)
- **Limited Network Security Insights**: No pod-to-pod connectivity analysis
- **No NetworkPolicy Visualization**: Can't see restrictions or allowed traffic flows

---

## High-Value Security & Connectivity Features

### Priority 1: Network Policy Visualization

**Business Value**: Regulated/edge customers need to prove compliance with network segmentation requirements

**Features to Add**:
1. **NetworkPolicy Detection**
   - Scan cluster for all NetworkPolicy resources
   - Parse ingress/egress rules
   - Identify which pods are affected by which policies

2. **Visual Policy Map**
   - Show which namespaces have policies
   - Highlight isolated vs exposed pods
   - Traffic flow diagrams (allowed/denied)
   - Color-coding: 🔴 No policies, 🟡 Partial, 🟢 Fully restricted

3. **Natural Language Queries**:
   - "Can pod X talk to pod Y?"
   - "What can access my database pods?"
   - "Show me all pods without network policies"
   - "Which namespaces are isolated?"

**Implementation**:
```python
# backend/src/models/network.py
class NetworkPolicy:
    name: str
    namespace: str
    pod_selector: dict
    ingress_rules: List[IngressRule]
    egress_rules: List[EgressRule]
    affected_pods: List[str]

# backend/src/services/network_analyzer.py
class NetworkAnalyzer:
    async def get_network_policies() -> List[NetworkPolicy]
    async def check_connectivity(source_pod, dest_pod) -> ConnectivityResult
    async def get_policy_gaps() -> List[UnprotectedResource]
```

---

### Priority 2: Pod-to-Pod Connectivity Matrix

**Business Value**: Security teams need to understand actual vs intended network topology

**Features**:
1. **Connectivity Matrix View**
   - Table showing which pods can reach which pods
   - Based on:
     - NetworkPolicies (intended restrictions)
     - Service definitions (actual exposure)
     - Pod IPs and ports
   
2. **IP & Port Inventory**
   - Pod IPs with listening ports
   - Service ClusterIPs
   - NodePorts and LoadBalancer IPs
   - DNS names

3. **Security Insights**:
   - "Show me all publicly exposed services"
   - "Which pods can reach the internet?"
   - "List all pods listening on privileged ports"

**UI Enhancement**:
```javascript
// Connectivity Matrix Table
┌─────────────┬──────────┬──────────┬──────────┐
│ Source/Dest │ Pod A    │ Pod B    │ Pod C    │
├─────────────┼──────────┼──────────┼──────────┤
│ Pod A       │ ✓        │ ✗ Policy │ ✓        │
│ Pod B       │ ✓        │ ✓        │ ✗ Policy │
│ Pod C       │ ✗ Policy │ ✓        │ ✓        │
└─────────────┴──────────┴──────────┴──────────┘
```

---

### Priority 3: Namespace Isolation Analysis

**Business Value**: Multi-tenancy requires strong namespace boundaries

**Features**:
1. **Namespace Security Score**
   - 🟢 Fully isolated (NetworkPolicies in place)
   - 🟡 Partially isolated (some gaps)
   - 🔴 Open (no restrictions)

2. **Cross-Namespace Traffic Analysis**
   - Which namespaces can talk to each other?
   - Service exposure across namespace boundaries
   - Identify "shared services" pattern

3. **Compliance Reports**:
   - "Generate namespace isolation report"
   - "Show all cross-namespace communications"
   - "Audit namespace boundaries"

---

### Priority 4: Security Context & RBAC Integration

**Business Value**: Complete security posture requires pod security + network security

**Features**:
1. **Pod Security Standards**
   - Privileged pods
   - Host network/PID/IPC usage
   - Root vs non-root containers
   - Capabilities analysis

2. **RBAC Analysis**
   - Which ServiceAccounts have cluster-admin?
   - Pod access to K8s API
   - Secrets and ConfigMap exposure

3. **Combined View**:
   - Pods with both privileged access AND network exposure = 🔴 High Risk
   - Isolated pods with restricted security context = 🟢 Low Risk

---

## Enhanced Direct Mode Prompts

Add these to the UI prompt cards:

### Network Security Prompts
1. "🔒 **Security Audit**" → "Show me pods without network policies and their exposed ports"
2. "🌐 **Network Map**" → "Visualize all pod-to-pod connections with IPs and policies"
3. "🚫 **Isolation Check**" → "Which namespaces are NOT isolated from each other?"
4. "📊 **Connectivity Matrix**" → "Show me the full pod connectivity matrix"
5. "⚠️ **Risk Assessment**" → "Find pods with privileged access AND public exposure"

### Edge/AKS Arc Specific
6. "📡 **Edge Connectivity**" → "Show all external connections (LoadBalancer, NodePort)"
7. "🔐 **Compliance Report**" → "Generate network isolation compliance report"
8. "🏗️ **Infrastructure Map**" → "Visualize node-pod-service-policy relationships"

---

## Implementation Roadmap

### Phase 1: Data Collection (Week 1)
- [ ] Add NetworkPolicy fetching to kubernetes.py
- [ ] Add Service/Endpoints analysis
- [ ] Create network models (NetworkPolicy, ConnectivityRule)
- [ ] Add RBAC resource fetching

### Phase 2: Analysis Engine (Week 2)
- [ ] Build NetworkAnalyzer service
- [ ] Implement connectivity checker (can Pod A reach Pod B?)
- [ ] Calculate namespace isolation scores
- [ ] Identify policy gaps

### Phase 3: Visualization (Week 3)
- [ ] Enhanced topology view with policies
- [ ] Connectivity matrix table
- [ ] Network flow diagrams (D3.js/Cytoscape)
- [ ] Security dashboard with scores

### Phase 4: Natural Language Integration (Week 4)
- [ ] Enhance Direct Mode with network queries
- [ ] Add security-focused intent patterns
- [ ] Implement compliance report generation
- [ ] Add export capabilities (PDF/CSV)

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (index.html)                    │
├─────────────────────────────────────────────────────────────┤
│  • Network Topology View (enhanced)                          │
│  • Connectivity Matrix Table                                 │
│  • Security Dashboard                                        │
│  • Policy Compliance Reports                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend API (routes.py)                     │
├─────────────────────────────────────────────────────────────┤
│  • /api/network/policies                                     │
│  • /api/network/connectivity-matrix                          │
│  • /api/network/check-connectivity?from=X&to=Y              │
│  • /api/security/namespace-scores                            │
│  • /api/security/risks                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Business Logic (services/)                      │
├─────────────────────────────────────────────────────────────┤
│  NetworkAnalyzer:                                            │
│    • parse_network_policies()                                │
│    • check_pod_connectivity(src, dst)                        │
│    • calculate_namespace_isolation()                         │
│    • find_security_gaps()                                    │
│                                                              │
│  SecurityAnalyzer:                                           │
│    • analyze_pod_security_context()                          │
│    • check_rbac_permissions()                                │
│    • generate_risk_score()                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│            Kubernetes Client (kubernetes.py)                 │
├─────────────────────────────────────────────────────────────┤
│  • get_network_policies()                                    │
│  • get_services()                                            │
│  • get_endpoints()                                           │
│  • get_roles() / get_role_bindings()                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Example Outputs

### Network Policy Summary
```
🔒 Network Security Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Overall Security Score: 6/10

Namespaces:
  🟢 kube-system: 3/3 policies (Fully Isolated)
  🟡 default: 1/5 policies (Partially Isolated)
  🔴 monitoring: 0/2 policies (No Isolation)

High-Risk Findings:
  ⚠️ 5 pods exposed without NetworkPolicy
  ⚠️ 2 pods running as root with HostNetwork=true
  ⚠️ LoadBalancer service "web-app" accessible from 0.0.0.0/0

Recommendations:
  1. Add NetworkPolicy to 'default' namespace
  2. Restrict HostNetwork usage
  3. Implement ingress controller with TLS
```

### Connectivity Check
```
Query: "Can the frontend pod talk to the database?"

🔍 Connectivity Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Source: frontend-abc123 (default/10.42.0.5)
Target: postgres-xyz789 (database/10.42.1.10:5432)

Result: ✗ BLOCKED

Reason:
  • NetworkPolicy "db-isolation" (database namespace)
  • Blocks all ingress except from pods with label: tier=backend
  • frontend-abc123 has label: tier=frontend ✗

Solution:
  Add label "tier=backend" to frontend pod OR
  Update NetworkPolicy to allow tier=frontend
```

---

## Competitive Advantage

### vs Cloud-Native Tools (Kubescape, Falco)
- ✅ **Natural Language Interface**: "Show me security risks" vs complex YAML queries
- ✅ **Edge/Disconnected Focus**: Works without internet, tailored for AKS Arc
- ✅ **Integrated View**: Network + Security + Operations in one tool

### vs Visualization Tools (Weave Scope)
- ✅ **Security-First**: Not just visualization, but compliance and risk analysis
- ✅ **Actionable Insights**: Specific recommendations, not just graphs
- ✅ **Conversational**: Ask questions, get answers

### vs Enterprise Tools (Prisma Cloud, Aqua)
- ✅ **Free & Local**: No SaaS, no subscription, runs on-prem
- ✅ **Lightweight**: Single tool, not a platform
- ✅ **Kubernetes-Native**: Built for K8s, not adapted from containers

---

## Success Metrics

### User Value
- Time to answer "Can pod X reach pod Y?": < 5 seconds
- Network policy gap identification: 100% coverage
- Compliance report generation: < 10 seconds

### Technical
- API response time: < 500ms for connectivity checks
- Support clusters up to 500 pods
- Network policy parsing: < 1 second

---

## Next Steps

1. **Validate approach** with user feedback
2. **Prioritize features** based on customer pain points
3. **Implement Phase 1** (Data Collection)
4. **Iterate with real-world AKS Arc clusters**

