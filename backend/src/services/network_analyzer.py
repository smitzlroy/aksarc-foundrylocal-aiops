"""
Network analysis and topology mapping service.

Analyzes Kubernetes network policies, services, and endpoints to build
a communication dependency graph.
"""

import asyncio
from typing import Dict, List, Set, Tuple, Optional
import structlog
from kubernetes import client

logger = structlog.get_logger(__name__)


class NetworkAnalyzer:
    """Analyzes network topology and dependencies."""
    
    def __init__(self, k8s_client):
        """Initialize with Kubernetes client.
        
        Args:
            k8s_client: KubernetesClient instance with established connection
        """
        self.core_v1 = k8s_client.core_v1
        self.networking_v1 = k8s_client.networking_v1
    
    async def analyze_topology(self) -> Dict:
        """Build complete network topology with dependencies.
        
        Returns:
            dict: Complete topology data including pods, services, dependencies
        """
        try:
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
        except Exception as e:
            logger.error("topology_analysis_failed", error=str(e))
            raise
    
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
                'service_account': pod.spec.service_account_name,
                'status': pod.status.phase,  # Frontend expects 'status'
                'phase': pod.status.phase    # Keep for backwards compatibility
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
            external_ip = None
            if svc.status.load_balancer and svc.status.load_balancer.ingress:
                ingress = svc.status.load_balancer.ingress[0]
                external_ip = ingress.ip if hasattr(ingress, 'ip') else ingress.hostname
            
            services.append({
                'name': svc.metadata.name,
                'namespace': svc.metadata.namespace,
                'type': svc.spec.type,
                'cluster_ip': svc.spec.cluster_ip,
                'external_ip': external_ip,
                'ports': [
                    {
                        'port': p.port,
                        'target_port': str(p.target_port) if p.target_port else '',
                        'protocol': p.protocol,
                        'name': p.name
                    } for p in (svc.spec.ports or [])
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
        try:
            policies_list = await asyncio.to_thread(
                self.networking_v1.list_network_policy_for_all_namespaces
            )
            
            policies = []
            for policy in policies_list.items:
                policies.append({
                    'name': policy.metadata.name,
                    'namespace': policy.metadata.namespace,
                    'pod_selector': policy.spec.pod_selector.match_labels or {} if policy.spec.pod_selector else {},
                    'policy_types': policy.spec.policy_types or [],
                    'ingress': self._parse_ingress_rules(policy.spec.ingress),
                    'egress': self._parse_egress_rules(policy.spec.egress)
                })
            
            return policies
        except Exception as e:
            logger.warning("failed_to_get_network_policies", error=str(e))
            return []
    
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
        
        for ns in namespaces:
            connectivity[ns] = {
                'can_access': list(namespaces),  # Default: all unless restricted
                'has_policies': False,
                'pod_count': len([p for p in pods if p['namespace'] == ns])
            }
            
            # Check if namespace has policies
            ns_policies = [p for p in policies if p['namespace'] == ns]
            if ns_policies:
                connectivity[ns]['has_policies'] = True
        
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
