# AKS Arc Enhancement Plan

## Executive Summary

This document outlines the implementation plan to enhance the K8s AI Assistant with specialized support for AKS enabled by Azure Arc (AKS Arc), while maintaining full compatibility with standard Kubernetes (k8s) and k3s distributions. The enhancements focus on:

1. **Platform Detection** - Auto-detect AKS Arc vs k8s/k3s
2. **AKS Arc-Specific UI** - Visual indicators and specialized features
3. **Diagnostic Integration** - Built-in support for AKS Arc diagnostic tools
4. **Troubleshooting Guides** - Contextual help for AKS Arc issues
5. **Enhanced Topology** - Network dependency mapping with communication flows

---

## 1. Platform Compatibility Analysis

### Current State: ✅ ALREADY COMPATIBLE

The tool uses the standard Kubernetes Python client which works with:
- **Vanilla Kubernetes** - Any standard k8s distribution
- **k3s** - Lightweight Kubernetes (currently tested)
- **AKS Arc** - Uses standard Kubernetes API

**Why it works:**
```python
# backend/src/services/kubernetes.py
config.load_kube_config()  # Works with any kubeconfig
self.core_v1 = client.CoreV1Api()  # Standard K8s API
self.apps_v1 = client.AppsV1Api()  # Standard K8s API
```

**No changes needed** - The existing implementation already supports all three platforms.

---

## 2. AKS Arc Detection & UI Enhancement

### Objective
Automatically detect when connected to an AKS Arc cluster and provide specialized UI/features.

### Detection Strategy

#### Method 1: Label Detection (Recommended)
AKS Arc clusters have specific node labels:
```python
# Check for AKS Arc-specific labels
def detect_aks_arc(self) -> dict:
    """Detect if cluster is AKS Arc enabled."""
    nodes = self.core_v1.list_node()
    
    for node in nodes.items:
        labels = node.metadata.labels or {}
        
        # AKS Arc specific labels
        if 'kubernetes.azure.com/cluster' in labels:
            return {
                'is_aks_arc': True,
                'cluster_name': labels.get('kubernetes.azure.com/cluster'),
                'arc_resource_id': labels.get('kubernetes.azure.com/arc-resource-id'),
                'azure_location': labels.get('kubernetes.azure.com/location')
            }
    
    return {'is_aks_arc': False}
```

#### Method 2: Annotation Detection
Check for Arc-specific annotations:
```python
# Look for Arc Resource Bridge annotations
annotations = node.metadata.annotations or {}
if 'management.azure.com/arc-enabled' in annotations:
    return {'is_aks_arc': True}
```

#### Method 3: Namespace Detection
Check for AKS Arc system namespaces:
```python
namespaces = self.core_v1.list_namespace()
arc_namespaces = [
    'azure-arc',
    'azurehybridcompute',
    'azure-arc-release',
    'arc-system'
]

for ns in namespaces.items:
    if ns.metadata.name in arc_namespaces:
        return {'is_aks_arc': True}
```

### UI Changes

#### Header Badge
```html
<!-- Add platform badge to header -->
<div class="header card">
    <h1>K8s AI Assistant v2</h1>
    <p>Intelligent Kubernetes Management</p>
    <div class="platform-badge" id="platformBadge">
        <!-- Dynamic content:
        - "🔷 AKS Arc on Azure Local" (blue badge)
        - "⚙️ Kubernetes" (gray badge)
        - "🐳 k3s" (light blue badge)
        -->
    </div>
</div>
```

#### AKS Arc Status Panel
```html
<!-- New panel when AKS Arc detected -->
<div class="aks-arc-panel card" id="aksArcPanel" style="display: none;">
    <h3>🔷 AKS Arc Information</h3>
    <div class="arc-info">
        <div class="info-row">
            <span class="label">Cluster Name:</span>
            <span id="arcClusterName">-</span>
        </div>
        <div class="info-row">
            <span class="label">Azure Location:</span>
            <span id="arcLocation">-</span>
        </div>
        <div class="info-row">
            <span class="label">Arc Resource ID:</span>
            <span id="arcResourceId">-</span>
        </div>
    </div>
    <div class="arc-actions">
        <button onclick="runArcDiagnostics()">🔍 Run Diagnostics</button>
        <button onclick="checkArcHealth()">💊 Health Check</button>
        <button onclick="viewArcLogs()">📋 View Logs</button>
    </div>
</div>
```

### CSS for Platform Badges
```css
.platform-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    margin-top: 6px;
}

.platform-badge.aks-arc {
    background: rgba(0, 120, 212, 0.2);
    color: #0078d4;
    border: 1px solid #0078d4;
}

.platform-badge.kubernetes {
    background: rgba(102, 126, 234, 0.2);
    color: var(--accent-primary);
    border: 1px solid var(--accent-primary);
}

.platform-badge.k3s {
    background: rgba(52, 211, 153, 0.2);
    color: #34d399;
    border: 1px solid #34d399;
}

.aks-arc-panel {
    grid-column: span 2;
}

.arc-info {
    margin: 10px 0;
    font-size: 12px;
}

.info-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid var(--border-color);
}

.info-row .label {
    color: var(--text-secondary);
    font-weight: 600;
}

.arc-actions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
}

.arc-actions button {
    flex: 1;
    padding: 8px;
    font-size: 11px;
    background: var(--accent-primary);
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}
```

---

## 3. AKS Arc Diagnostic Integration

### Support Module Integration

#### Backend Service: `aks_arc_diagnostics.py`
```python
"""
AKS Arc diagnostic service.

Integrates with Microsoft's Support.AksArc PowerShell module for
diagnostic checks and remediation.
"""

import asyncio
import json
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class AksArcDiagnostics:
    """Service for running AKS Arc diagnostics."""
    
    def __init__(self):
        """Initialize diagnostic service."""
        self._ps_available = False
        self._module_installed = False
    
    async def check_prerequisites(self) -> bool:
        """Check if PowerShell and Support.AksArc module are available."""
        try:
            # Check if PowerShell is available
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', 'Get-Module -ListAvailable -Name Support.AksArc',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            self._ps_available = True
            self._module_installed = b'Support.AksArc' in stdout
            
            return self._module_installed
            
        except Exception as e:
            logger.error("failed_to_check_prerequisites", error=str(e))
            return False
    
    async def install_support_module(self) -> Dict:
        """Install Support.AksArc PowerShell module."""
        try:
            ps_script = """
            Install-Module -Name Support.AksArc -Force -AllowClobber
            Import-Module Support.AksArc -Force
            """
            
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self._module_installed = True
                return {
                    'success': True,
                    'message': 'Support.AksArc module installed successfully'
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to install: {stderr.decode()}'
                }
                
        except Exception as e:
            logger.error("failed_to_install_module", error=str(e))
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    async def run_diagnostic_checks(self) -> List[Dict]:
        """Run Test-SupportAksArcKnownIssues diagnostic checks."""
        if not self._module_installed:
            return [{
                'test_name': 'Prerequisites',
                'status': 'Failed',
                'message': 'Support.AksArc module not installed'
            }]
        
        try:
            ps_script = """
            Import-Module Support.AksArc -Force
            $results = Test-SupportAksArcKnownIssues
            $results | ConvertTo-Json -Depth 10
            """
            
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                results = json.loads(stdout.decode())
                return self._parse_diagnostic_results(results)
            else:
                logger.error("diagnostic_check_failed", stderr=stderr.decode())
                return []
                
        except Exception as e:
            logger.error("failed_to_run_diagnostics", error=str(e))
            return []
    
    def _parse_diagnostic_results(self, raw_results: Dict) -> List[Dict]:
        """Parse PowerShell diagnostic results into standardized format."""
        parsed = []
        
        if isinstance(raw_results, list):
            for item in raw_results:
                parsed.append({
                    'test_name': item.get('Test Name', 'Unknown'),
                    'status': item.get('Status', 'Unknown'),
                    'message': item.get('Message', ''),
                    'recommendation': self._get_recommendation(item.get('Test Name', ''))
                })
        
        return parsed
    
    def _get_recommendation(self, test_name: str) -> str:
        """Get recommendation based on test name."""
        recommendations = {
            'Validate MOC is on Latest Patch Version': 
                'Update MOC to the latest version using Update-Module',
            'Validate Failover Cluster Service Responsiveness':
                'Check cluster health with Get-ClusterResource',
            'Validate MOC Cloud Agent Running':
                'Restart MOC Cloud Agent service or run Invoke-SupportAksArcRemediation',
            'Validate Expired Certificates':
                'Renew certificates using Repair-Certificate cmdlet',
        }
        return recommendations.get(test_name, 'Check AKS Arc documentation for resolution steps')
    
    async def run_remediation(self) -> Dict:
        """Run Invoke-SupportAksArcRemediation to fix common issues."""
        if not self._module_installed:
            return {
                'success': False,
                'message': 'Support.AksArc module not installed'
            }
        
        try:
            ps_script = """
            Import-Module Support.AksArc -Force
            Invoke-SupportAksArcRemediation -Verbose
            """
            
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            return {
                'success': result.returncode == 0,
                'message': stdout.decode() if result.returncode == 0 else stderr.decode()
            }
            
        except Exception as e:
            logger.error("failed_to_run_remediation", error=str(e))
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
```

#### API Routes
```python
# backend/src/api/routes.py

@router.get("/api/aksarc/detect")
async def detect_aks_arc():
    """Detect if cluster is AKS Arc enabled."""
    detection = await k8s_client.detect_aks_arc()
    return detection

@router.get("/api/aksarc/diagnostics/check")
async def check_aks_arc_prerequisites():
    """Check if AKS Arc diagnostic tools are available."""
    diagnostics = AksArcDiagnostics()
    available = await diagnostics.check_prerequisites()
    return {
        'available': available,
        'message': 'Support.AksArc module is installed' if available else 'Module not found'
    }

@router.post("/api/aksarc/diagnostics/install")
async def install_aks_arc_tools():
    """Install AKS Arc diagnostic tools."""
    diagnostics = AksArcDiagnostics()
    result = await diagnostics.install_support_module()
    return result

@router.get("/api/aksarc/diagnostics/run")
async def run_aks_arc_diagnostics():
    """Run AKS Arc diagnostic checks."""
    diagnostics = AksArcDiagnostics()
    results = await diagnostics.run_diagnostic_checks()
    return {
        'total_tests': len(results),
        'passed': sum(1 for r in results if r['status'] == 'Passed'),
        'failed': sum(1 for r in results if r['status'] == 'Failed'),
        'results': results
    }

@router.post("/api/aksarc/diagnostics/remediate")
async def remediate_aks_arc_issues():
    """Run automatic remediation for common issues."""
    diagnostics = AksArcDiagnostics()
    result = await diagnostics.run_remediation()
    return result
```

---

## 4. Troubleshooting Guide Integration

### Contextual Help System

#### Troubleshooting Guide Data Structure
```javascript
// index.html - Add troubleshooting guide data
const aksArcTroubleshootingGuides = {
    'network_validation_errors': {
        title: 'Network Validation Errors',
        symptoms: [
            'Cluster creation fails with network errors',
            'Cloud agent connectivity issues',
            'Gateway unreachable errors'
        ],
        diagnostics: [
            'Run diagnostic checker',
            'Test cloud agent connectivity',
            'Verify gateway configuration'
        ],
        solutions: [
            'Check logical network IP addresses can reach management pool',
            'Verify DNS server resolution',
            'Check firewall rules for required ports',
            'Ensure cross-vlan connectivity if needed'
        ],
        docs_url: 'https://learn.microsoft.com/en-us/azure/aks/aksarc/aks-network-validation-errors'
    },
    'control_plane_config': {
        title: 'Control Plane Configuration Validation',
        symptoms: [
            'K8sVersionValidation error',
            'Control plane creation fails',
            'Invalid configuration parameters'
        ],
        diagnostics: [
            'Check K8s version compatibility',
            'Validate control plane settings',
            'Review configuration parameters'
        ],
        solutions: [
            'Use supported Kubernetes versions',
            'Verify control plane node count',
            'Check VM size requirements',
            'Validate network settings'
        ],
        docs_url: 'https://learn.microsoft.com/en-us/azure/aks/aksarc/aks-troubleshoot-control-plane-configuration'
    },
    'storage_volume_deletion': {
        title: 'Out-of-Band Storage Volume Deletion',
        symptoms: [
            'Pods stuck in pending state',
            'PVC provisioning failures',
            'Storage mount errors'
        ],
        diagnostics: [
            'Check PVC status',
            'Verify storage class',
            'Check for orphaned volumes'
        ],
        solutions: [
            'Recreate PVC if volume was deleted',
            'Use storage validation tools',
            'Verify storage provider health',
            'Check storage capacity'
        ],
        docs_url: 'https://learn.microsoft.com/en-us/azure/aks/aksarc/aks-troubleshoot-storage'
    },
    'bgp_frr': {
        title: 'BGP with FRR Troubleshooting',
        symptoms: [
            'Network routing issues',
            'Service endpoints unreachable',
            'LoadBalancer services not working'
        ],
        diagnostics: [
            'Check BGP peering status',
            'Verify FRR configuration',
            'Test route advertisements'
        ],
        solutions: [
            'Verify BGP peer addresses',
            'Check AS numbers',
            'Validate network policies',
            'Review FRR logs'
        ],
        docs_url: 'https://learn.microsoft.com/en-us/azure/aks/aksarc/aks-troubleshoot-bgp-frr'
    }
};

// Function to show troubleshooting guide
function showTroubleshootingGuide(guideKey) {
    const guide = aksArcTroubleshootingGuides[guideKey];
    if (!guide) return;
    
    const modal = document.createElement('div');
    modal.className = 'troubleshooting-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close" onclick="this.parentElement.parentElement.remove()">×</span>
            <h2>${guide.title}</h2>
            
            <div class="guide-section">
                <h3>🔍 Symptoms</h3>
                <ul>
                    ${guide.symptoms.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
            
            <div class="guide-section">
                <h3>🩺 Diagnostics</h3>
                <ul>
                    ${guide.diagnostics.map(d => `<li>${d}</li>`).join('')}
                </ul>
                <button onclick="runArcDiagnostics()">Run Diagnostics Now</button>
            </div>
            
            <div class="guide-section">
                <h3>✅ Solutions</h3>
                <ul>
                    ${guide.solutions.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
            
            <div class="guide-section">
                <h3>📚 Documentation</h3>
                <a href="${guide.docs_url}" target="_blank">View Full Documentation</a>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}
```

#### AI System Prompt Enhancement
```python
# Add AKS Arc context to system prompt when detected
if cluster_info.get('is_aks_arc'):
    system_prompt += """

You are working with an AKS Arc (Azure Kubernetes Service enabled by Azure Arc) cluster running on Azure Local.

AKS Arc SPECIFIC CONSIDERATIONS:
1. Architecture: This is a hybrid cloud K8s running on-premises with Azure management
2. Components: Includes Arc Resource Bridge, MOC (Microsoft On-premises Cloud) agents
3. Networking: Uses logical networks, management IP pools, and may have cross-vlan requirements
4. Troubleshooting: Has specific diagnostic tools (Support.AksArc, diagnostic checker)
5. Common Issues:
   - Cloud agent connectivity (port 55000)
   - Gateway reachability (ICMP)
   - Required URL accessibility
   - Certificate expiration
   - MOC version mismatches

When diagnosing issues, consider AKS Arc specific causes:
- Is the MOC cloud agent reachable from control plane nodes?
- Are logical network IPs able to reach management pool IPs?
- Are required Azure URLs accessible?
- Is cross-vlan connectivity properly configured?
- Are certificates up to date?

Recommend running: "Run AKS Arc Diagnostics" button for automated checks.
"""
```

---

## 5. Enhanced Topology with Network Dependencies

### Objective
Visualize pod-to-pod communication, namespace boundaries, network policies, and service dependencies.

### Data Collection

#### Network Policy Analysis
```python
# backend/src/services/network_analyzer.py
"""
Network analysis and topology mapping service.

Analyzes Kubernetes network policies, services, and endpoints to build
a communication dependency graph.
"""

import asyncio
from typing import Dict, List, Set, Tuple
import structlog
from kubernetes import client

logger = structlog.get_logger(__name__)


class NetworkAnalyzer:
    """Analyzes network topology and dependencies."""
    
    def __init__(self, k8s_client):
        """Initialize with Kubernetes client."""
        self.core_v1 = k8s_client.core_v1
        self.networking_v1 = client.NetworkingV1Api()
    
    async def analyze_topology(self) -> Dict:
        """Build complete network topology with dependencies."""
        
        # Collect all data in parallel
        pods, services, endpoints, network_policies = await asyncio.gather(
            self._get_pods(),
            self._get_services(),
            self._get_endpoints(),
            self._get_network_policies()
        )
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(pods, services, endpoints)
        
        # Analyze network policies
        policy_analysis = self._analyze_network_policies(network_policies, pods)
        
        # Calculate namespace connectivity
        namespace_connectivity = self._calculate_namespace_connectivity(
            pods, services, network_policies
        )
        
        return {
            'pods': pods,
            'services': services,
            'dependencies': dependencies,
            'network_policies': policy_analysis,
            'namespace_connectivity': namespace_connectivity,
            'communication_matrix': self._build_communication_matrix(dependencies)
        }
    
    async def _get_pods(self) -> List[Dict]:
        """Get all pods with networking details."""
        pods_list = await asyncio.to_thread(
            self.core_v1.list_pod_for_all_namespaces
        )
        
        pods = []
        for pod in pods_list.items:
            pods.append({
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'ip': pod.status.pod_ip,
                'node': pod.spec.node_name,
                'labels': pod.metadata.labels or {},
                'ports': self._extract_pod_ports(pod),
                'service_account': pod.spec.service_account_name
            })
        
        return pods
    
    def _extract_pod_ports(self, pod) -> List[Dict]:
        """Extract container ports from pod."""
        ports = []
        for container in pod.spec.containers:
            if container.ports:
                for port in container.ports:
                    ports.append({
                        'container': container.name,
                        'port': port.container_port,
                        'protocol': port.protocol or 'TCP',
                        'name': port.name
                    })
        return ports
    
    async def _get_services(self) -> List[Dict]:
        """Get all services with endpoints."""
        services_list = await asyncio.to_thread(
            self.core_v1.list_service_for_all_namespaces
        )
        
        services = []
        for svc in services_list.items:
            services.append({
                'name': svc.metadata.name,
                'namespace': svc.metadata.namespace,
                'type': svc.spec.type,
                'cluster_ip': svc.spec.cluster_ip,
                'external_ip': svc.status.load_balancer.ingress[0].ip 
                    if svc.status.load_balancer and svc.status.load_balancer.ingress 
                    else None,
                'ports': [
                    {
                        'port': p.port,
                        'target_port': str(p.target_port),
                        'protocol': p.protocol,
                        'name': p.name
                    } for p in svc.spec.ports
                ],
                'selector': svc.spec.selector or {}
            })
        
        return services
    
    async def _get_endpoints(self) -> List[Dict]:
        """Get all service endpoints."""
        endpoints_list = await asyncio.to_thread(
            self.core_v1.list_endpoints_for_all_namespaces
        )
        
        endpoints = []
        for ep in endpoints_list.items:
            if ep.subsets:
                for subset in ep.subsets:
                    endpoints.append({
                        'service': ep.metadata.name,
                        'namespace': ep.metadata.namespace,
                        'addresses': [addr.ip for addr in (subset.addresses or [])],
                        'ports': [
                            {
                                'port': p.port,
                                'protocol': p.protocol,
                                'name': p.name
                            } for p in (subset.ports or [])
                        ]
                    })
        
        return endpoints
    
    async def _get_network_policies(self) -> List[Dict]:
        """Get all network policies."""
        policies_list = await asyncio.to_thread(
            self.networking_v1.list_network_policy_for_all_namespaces
        )
        
        policies = []
        for policy in policies_list.items:
            policies.append({
                'name': policy.metadata.name,
                'namespace': policy.metadata.namespace,
                'pod_selector': policy.spec.pod_selector.match_labels or {},
                'policy_types': policy.spec.policy_types or [],
                'ingress': self._parse_ingress_rules(policy.spec.ingress),
                'egress': self._parse_egress_rules(policy.spec.egress)
            })
        
        return policies
    
    def _parse_ingress_rules(self, ingress_rules) -> List[Dict]:
        """Parse ingress network policy rules."""
        if not ingress_rules:
            return []
        
        rules = []
        for rule in ingress_rules:
            rule_data = {
                'from': [],
                'ports': []
            }
            
            if rule._from:
                for from_rule in rule._from:
                    if from_rule.pod_selector:
                        rule_data['from'].append({
                            'type': 'pod_selector',
                            'selector': from_rule.pod_selector.match_labels or {}
                        })
                    if from_rule.namespace_selector:
                        rule_data['from'].append({
                            'type': 'namespace_selector',
                            'selector': from_rule.namespace_selector.match_labels or {}
                        })
            
            if rule.ports:
                rule_data['ports'] = [
                    {
                        'protocol': p.protocol,
                        'port': str(p.port) if p.port else 'all'
                    } for p in rule.ports
                ]
            
            rules.append(rule_data)
        
        return rules
    
    def _parse_egress_rules(self, egress_rules) -> List[Dict]:
        """Parse egress network policy rules."""
        if not egress_rules:
            return []
        
        rules = []
        for rule in egress_rules:
            rule_data = {
                'to': [],
                'ports': []
            }
            
            if rule.to:
                for to_rule in rule.to:
                    if to_rule.pod_selector:
                        rule_data['to'].append({
                            'type': 'pod_selector',
                            'selector': to_rule.pod_selector.match_labels or {}
                        })
                    if to_rule.namespace_selector:
                        rule_data['to'].append({
                            'type': 'namespace_selector',
                            'selector': to_rule.namespace_selector.match_labels or {}
                        })
            
            if rule.ports:
                rule_data['ports'] = [
                    {
                        'protocol': p.protocol,
                        'port': str(p.port) if p.port else 'all'
                    } for p in rule.ports
                ]
            
            rules.append(rule_data)
        
        return rules
    
    def _build_dependency_graph(
        self, 
        pods: List[Dict], 
        services: List[Dict], 
        endpoints: List[Dict]
    ) -> List[Dict]:
        """Build service-to-pod dependency graph."""
        dependencies = []
        
        for service in services:
            # Find pods that match service selector
            matching_pods = []
            for pod in pods:
                if pod['namespace'] == service['namespace']:
                    if self._labels_match(pod['labels'], service['selector']):
                        matching_pods.append(pod['name'])
            
            if matching_pods:
                dependencies.append({
                    'service': service['name'],
                    'namespace': service['namespace'],
                    'service_type': service['type'],
                    'service_ip': service['cluster_ip'],
                    'service_ports': service['ports'],
                    'target_pods': matching_pods,
                    'communication_type': 'service-to-pod'
                })
        
        return dependencies
    
    def _labels_match(self, pod_labels: Dict, selector: Dict) -> bool:
        """Check if pod labels match service selector."""
        if not selector:
            return False
        
        for key, value in selector.items():
            if pod_labels.get(key) != value:
                return False
        
        return True
    
    def _analyze_network_policies(
        self, 
        policies: List[Dict], 
        pods: List[Dict]
    ) -> Dict:
        """Analyze which pods are affected by network policies."""
        analysis = {
            'total_policies': len(policies),
            'affected_pods': [],
            'unrestricted_namespaces': []
        }
        
        # Find pods affected by policies
        for policy in policies:
            for pod in pods:
                if pod['namespace'] == policy['namespace']:
                    if self._labels_match(pod['labels'], policy['pod_selector']):
                        analysis['affected_pods'].append({
                            'pod': pod['name'],
                            'namespace': pod['namespace'],
                            'policy': policy['name'],
                            'ingress_restricted': 'Ingress' in policy['policy_types'],
                            'egress_restricted': 'Egress' in policy['policy_types']
                        })
        
        # Find namespaces without policies
        all_namespaces = set(pod['namespace'] for pod in pods)
        policy_namespaces = set(policy['namespace'] for policy in policies)
        unrestricted = all_namespaces - policy_namespaces
        
        analysis['unrestricted_namespaces'] = list(unrestricted)
        
        return analysis
    
    def _calculate_namespace_connectivity(
        self,
        pods: List[Dict],
        services: List[Dict],
        policies: List[Dict]
    ) -> Dict:
        """Calculate which namespaces can communicate with each other."""
        namespaces = set(pod['namespace'] for pod in pods)
        connectivity = {}
        
        for ns1 in namespaces:
            connectivity[ns1] = {
                'can_access': [],
                'restrictions': []
            }
            
            # Check if namespace has restrictive policies
            ns_policies = [p for p in policies if p['namespace'] == ns1]
            
            if not ns_policies:
                # No policies = can access all
                connectivity[ns1]['can_access'] = list(namespaces)
            else:
                # Analyze policies to determine allowed namespaces
                for policy in ns_policies:
                    if policy['egress']:
                        for rule in policy['egress']:
                            for to_rule in rule['to']:
                                if to_rule['type'] == 'namespace_selector':
                                    # Find matching namespaces
                                    for ns2 in namespaces:
                                        # In real implementation, match namespace labels
                                        connectivity[ns1]['can_access'].append(ns2)
        
        return connectivity
    
    def _build_communication_matrix(self, dependencies: List[Dict]) -> List[Dict]:
        """Build a communication matrix showing all connections."""
        matrix = []
        
        for dep in dependencies:
            for target_pod in dep['target_pods']:
                for port_info in dep['service_ports']:
                    matrix.append({
                        'source_type': 'service',
                        'source': f"{dep['namespace']}/{dep['service']}",
                        'target_type': 'pod',
                        'target': f"{dep['namespace']}/{target_pod}",
                        'protocol': port_info['protocol'],
                        'port': port_info['port'],
                        'target_port': port_info['target_port']
                    })
        
        return matrix
```

### Enhanced Topology Visualization

#### Frontend Implementation
```javascript
// index.html - Enhanced topology rendering
async function renderEnhancedTopology() {
    const response = await fetch('/api/topology/analyze');
    const data = await response.json();
    
    const svg = d3.select('#topologyVisualization');
    svg.selectAll('*').remove(); // Clear existing
    
    const width = svg.node().clientWidth;
    const height = svg.node().clientHeight;
    
    // Create force simulation
    const simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(40));
    
    // Build nodes and links
    const nodes = [];
    const links = [];
    
    // Add namespace nodes
    const namespaces = new Set();
    data.pods.forEach(pod => namespaces.add(pod.namespace));
    namespaces.forEach(ns => {
        nodes.push({
            id: `ns-${ns}`,
            name: ns,
            type: 'namespace',
            group: ns
        });
    });
    
    // Add pod nodes
    data.pods.forEach(pod => {
        nodes.push({
            id: `pod-${pod.namespace}-${pod.name}`,
            name: pod.name,
            type: 'pod',
            group: pod.namespace,
            ip: pod.ip,
            ports: pod.ports
        });
        
        // Link pod to namespace
        links.push({
            source: `ns-${pod.namespace}`,
            target: `pod-${pod.namespace}-${pod.name}`,
            type: 'contains'
        });
    });
    
    // Add service nodes and dependencies
    data.dependencies.forEach(dep => {
        const svcId = `svc-${dep.namespace}-${dep.service}`;
        nodes.push({
            id: svcId,
            name: dep.service,
            type: 'service',
            group: dep.namespace,
            ports: dep.service_ports
        });
        
        // Link service to namespace
        links.push({
            source: `ns-${dep.namespace}`,
            target: svcId,
            type: 'contains'
        });
        
        // Link service to target pods with port info
        dep.target_pods.forEach(pod => {
            const podId = `pod-${dep.namespace}-${pod}`;
            dep.service_ports.forEach(port => {
                links.push({
                    source: svcId,
                    target: podId,
                    type: 'routes-to',
                    protocol: port.protocol,
                    port: port.port,
                    targetPort: port.target_port
                });
            });
        });
    });
    
    // Create link elements with protocol/port labels
    const link = svg.append('g')
        .selectAll('line')
        .data(links)
        .enter().append('g');
    
    link.append('line')
        .attr('class', d => `link link-${d.type}`)
        .attr('stroke', d => {
            if (d.type === 'contains') return '#3a3f58';
            if (d.type === 'routes-to') return '#667eea';
            return '#94a3b8';
        })
        .attr('stroke-width', d => d.type === 'routes-to' ? 2 : 1)
        .attr('stroke-dasharray', d => d.type === 'contains' ? '5,5' : '0');
    
    // Add link labels for routes-to connections
    const linkLabels = svg.append('g')
        .selectAll('text')
        .data(links.filter(l => l.type === 'routes-to'))
        .enter().append('text')
        .attr('class', 'link-label')
        .attr('font-size', '9px')
        .attr('fill', '#94a3b8')
        .text(d => `${d.protocol}:${d.port}→${d.targetPort}`);
    
    // Create node elements
    const node = svg.append('g')
        .selectAll('g')
        .data(nodes)
        .enter().append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add shapes based on node type
    node.each(function(d) {
        const g = d3.select(this);
        
        if (d.type === 'namespace') {
            // Rectangle for namespace
            g.append('rect')
                .attr('width', 120)
                .attr('height', 60)
                .attr('x', -60)
                .attr('y', -30)
                .attr('fill', 'rgba(102, 126, 234, 0.1)')
                .attr('stroke', '#667eea')
                .attr('stroke-width', 2)
                .attr('rx', 5);
        } else if (d.type === 'service') {
            // Diamond for service
            g.append('path')
                .attr('d', 'M 0,-20 L 20,0 L 0,20 L -20,0 Z')
                .attr('fill', 'rgba(16, 185, 129, 0.2)')
                .attr('stroke', '#10b981')
                .attr('stroke-width', 2);
        } else if (d.type === 'pod') {
            // Circle for pod
            g.append('circle')
                .attr('r', 15)
                .attr('fill', 'rgba(239, 68, 68, 0.2)')
                .attr('stroke', '#ef4444')
                .attr('stroke-width', 2);
        }
    });
    
    // Add labels
    node.append('text')
        .attr('dy', d => d.type === 'namespace' ? 5 : 30)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11px')
        .attr('fill', '#e2e8f0')
        .text(d => d.name.length > 15 ? d.name.substring(0, 12) + '...' : d.name);
    
    // Add tooltips on hover
    node.append('title')
        .text(d => {
            let tooltip = `${d.type.toUpperCase()}: ${d.name}\n`;
            if (d.ip) tooltip += `IP: ${d.ip}\n`;
            if (d.ports && d.ports.length > 0) {
                tooltip += `Ports: ${d.ports.map(p => `${p.protocol}:${p.port}`).join(', ')}`;
            }
            return tooltip;
        });
    
    // Update positions on tick
    simulation
        .nodes(nodes)
        .on('tick', () => {
            link.selectAll('line')
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            linkLabels
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2);
            
            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });
    
    simulation.force('link').links(links);
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    // Add legend
    const legend = svg.append('g')
        .attr('transform', 'translate(20, 20)');
    
    const legendItems = [
        { type: 'namespace', label: 'Namespace', shape: 'rect' },
        { type: 'service', label: 'Service', shape: 'diamond' },
        { type: 'pod', label: 'Pod', shape: 'circle' },
        { type: 'routes-to', label: 'Traffic Flow', shape: 'line' }
    ];
    
    legendItems.forEach((item, i) => {
        const g = legend.append('g')
            .attr('transform', `translate(0, ${i * 25})`);
        
        if (item.shape === 'rect') {
            g.append('rect')
                .attr('width', 15)
                .attr('height', 15)
                .attr('fill', 'rgba(102, 126, 234, 0.1)')
                .attr('stroke', '#667eea');
        } else if (item.shape === 'diamond') {
            g.append('path')
                .attr('d', 'M 8,0 L 15,8 L 8,15 L 0,8 Z')
                .attr('fill', 'rgba(16, 185, 129, 0.2)')
                .attr('stroke', '#10b981');
        } else if (item.shape === 'circle') {
            g.append('circle')
                .attr('r', 7)
                .attr('cx', 7)
                .attr('cy', 7)
                .attr('fill', 'rgba(239, 68, 68, 0.2)')
                .attr('stroke', '#ef4444');
        } else if (item.shape === 'line') {
            g.append('line')
                .attr('x1', 0)
                .attr('y1', 7)
                .attr('x2', 15)
                .attr('y2', 7)
                .attr('stroke', '#667eea')
                .attr('stroke-width', 2);
        }
        
        g.append('text')
            .attr('x', 20)
            .attr('y', 11)
            .attr('font-size', '11px')
            .attr('fill', '#e2e8f0')
            .text(item.label);
    });
}
```

---

## Implementation Priority

### Phase 1 (Week 1): Platform Detection & UI
1. Implement AKS Arc detection in `kubernetes.py`
2. Add platform badge to UI header
3. Create AKS Arc info panel
4. Update API route for platform detection
5. Test with AKS Arc, k8s, and k3s clusters

**Deliverable:** Platform-aware UI that shows appropriate badges

### Phase 2 (Week 2): Diagnostic Integration
1. Create `aks_arc_diagnostics.py` service
2. Add API routes for diagnostic checks
3. Implement diagnostic results UI
4. Add "Run Diagnostics" button
5. Test PowerShell module integration

**Deliverable:** Working diagnostic checker accessible from UI

### Phase 3 (Week 3): Troubleshooting Guides
1. Create troubleshooting guide data structure
2. Implement modal display system
3. Enhance AI system prompt with AKS Arc context
4. Add contextual help buttons
5. Link diagnostic failures to guides

**Deliverable:** Contextual help system with automated guidance

### Phase 4 (Week 4): Network Topology Enhancement
1. Implement `NetworkAnalyzer` class
2. Add network policy parsing
3. Create dependency graph builder
4. Implement enhanced D3.js visualization
5. Add protocol/port labels to connections

**Deliverable:** Interactive topology with communication flows

### Phase 5 (Week 5): Testing & Documentation
1. Test all features with AKS Arc cluster
2. Verify backward compatibility with k8s/k3s
3. Update PROJECT_OVERVIEW.md
4. Create AKS_ARC_USER_GUIDE.md
5. Performance testing and optimization

**Deliverable:** Production-ready enhanced tool

---

## Success Criteria

### Functional Requirements
- ✅ Tool works with AKS Arc, k8s, and k3s without configuration changes
- ✅ AKS Arc clusters show specialized UI elements
- ✅ Diagnostic checks can be run from UI
- ✅ Troubleshooting guides are contextually accessible
- ✅ Topology shows network dependencies with protocols/ports

### UX Requirements
- ✅ Platform type is immediately visible in UI
- ✅ AKS Arc features don't clutter non-Arc clusters
- ✅ Diagnostic results are easy to understand
- ✅ Topology visualization is interactive and informative

### Performance Requirements
- ✅ Platform detection adds < 500ms to startup
- ✅ Diagnostic checks complete within 30 seconds
- ✅ Topology analysis completes within 5 seconds
- ✅ UI remains responsive during all operations

---

## Next Steps

1. **Review this plan** - Confirm approach aligns with vision
2. **Choose starting phase** - Recommend starting with Phase 1
3. **Set up AKS Arc test environment** - Need access to test cluster
4. **Begin implementation** - Start with platform detection
5. **Iterate based on feedback** - Adjust as needed during development

---

*This document provides a comprehensive roadmap for enhancing the K8s AI Assistant with AKS Arc capabilities while maintaining universal compatibility.*
