"""
Graph-based network topology analyzer for AKS Arc clusters.

Builds a complete communication graph with pod-to-pod flows, service mappings,
and NetworkPolicy enforcement analysis.
"""

import asyncio
import hashlib
from collections import defaultdict
from typing import Optional

import structlog
from kubernetes import client

from src.models.topology_graph import (
    ComputeNode,
    ExternalEndpoint,
    MermaidExport,
    NamespaceConnectivity,
    NetworkFlow,
    NetworkPolicyNode,
    NetworkPolicyRule,
    NodeType,
    PodNode,
    PortProtocol,
    ServiceNode,
    ServicePort,
    TopologyGraph,
    TopologyMetadata,
    ContainerPort,
)

logger = structlog.get_logger(__name__)


class TopologyGraphBuilder:
    """Builds comprehensive network topology graphs from Kubernetes resources."""
    
    def __init__(self, k8s_client):
        """Initialize with Kubernetes client.
        
        Args:
            k8s_client: KubernetesClient instance with established connection
        """
        self.core_v1 = k8s_client.core_v1
        self.networking_v1 = k8s_client.networking_v1
        self.platform_info = k8s_client._platform_info or {}
    
    async def build_topology(self) -> TopologyGraph:
        """Build complete network topology graph.
        
        Returns:
            TopologyGraph with all nodes, edges, and analysis
        """
        logger.info("building_topology_graph")
        
        try:
            # Collect all resources in parallel
            nodes, pods_raw, services_raw, endpoints_raw, netpols_raw = await asyncio.gather(
                self._get_nodes(),
                self._get_pods(),
                self._get_services(),
                self._get_endpoints(),
                self._get_network_policies()
            )
            
            # Build graph nodes
            compute_nodes = self._build_compute_nodes(nodes)
            pods = self._build_pod_nodes(pods_raw)
            services = self._build_service_nodes(services_raw, endpoints_raw, pods)
            netpols = self._build_network_policy_nodes(netpols_raw, pods)
            
            # Analyze communication flows
            flows = self._build_communication_flows(pods, services, netpols)
            
            # Calculate namespace connectivity matrix
            ns_connectivity = self._calculate_namespace_connectivity(pods, netpols)
            
            # Build metadata
            metadata = TopologyMetadata(
                cluster_name=self.platform_info.get("cluster_name", "unknown"),
                k8s_version=self.platform_info.get("version", "unknown"),
                platform=self.platform_info.get("type", "other"),
                node_count=len(compute_nodes),
                pod_count=len(pods),
                service_count=len(services),
                namespace_count=len(set(p.namespace for p in pods))
            )
            
            topology = TopologyGraph(
                metadata=metadata,
                compute_nodes=compute_nodes,
                pods=pods,
                services=services,
                network_policies=netpols,
                communication_flows=flows,
                namespace_connectivity=ns_connectivity
            )
            
            logger.info(
                "topology_graph_built",
                nodes=len(compute_nodes),
                pods=len(pods),
                services=len(services),
                flows=len(flows)
            )
            
            return topology
            
        except Exception as e:
            logger.error("topology_build_failed", error=str(e))
            raise
    
    async def _get_nodes(self) -> list:
        """Get all compute nodes."""
        nodes_list = await asyncio.to_thread(self.core_v1.list_node)
        return nodes_list.items
    
    async def _get_pods(self) -> list:
        """Get all pods."""
        pods_list = await asyncio.to_thread(self.core_v1.list_pod_for_all_namespaces)
        return pods_list.items
    
    async def _get_services(self) -> list:
        """Get all services."""
        services_list = await asyncio.to_thread(self.core_v1.list_service_for_all_namespaces)
        return services_list.items
    
    async def _get_endpoints(self) -> list:
        """Get all endpoints."""
        endpoints_list = await asyncio.to_thread(self.core_v1.list_endpoints_for_all_namespaces)
        return endpoints_list.items
    
    async def _get_network_policies(self) -> list:
        """Get all network policies."""
        try:
            netpol_list = await asyncio.to_thread(
                self.networking_v1.list_network_policy_for_all_namespaces
            )
            return netpol_list.items
        except Exception as e:
            logger.warning("network_policies_unavailable", error=str(e))
            return []
    
    def _build_compute_nodes(self, nodes: list) -> list[ComputeNode]:
        """Build ComputeNode models from K8s nodes."""
        compute_nodes = []
        
        for node in nodes:
            # Determine role
            role = "control-plane" if "node-role.kubernetes.io/control-plane" in (node.metadata.labels or {}) else "worker"
            
            # Get node IP
            node_ip = "unknown"
            for addr in node.status.addresses or []:
                if addr.type == "InternalIP":
                    node_ip = addr.address
                    break
            
            compute_nodes.append(ComputeNode(
                id=f"node-{node.metadata.name}",
                name=node.metadata.name,
                ip=node_ip,
                role=role,
                capacity={k: str(v) for k, v in (node.status.capacity or {}).items()},
                allocatable={k: str(v) for k, v in (node.status.allocatable or {}).items()},
                conditions=[
                    {"type": c.type, "status": c.status, "reason": c.reason}
                    for c in (node.status.conditions or [])
                ]
            ))
        
        return compute_nodes
    
    def _build_pod_nodes(self, pods: list) -> list[PodNode]:
        """Build PodNode models from K8s pods."""
        pod_nodes = []
        
        for pod in pods:
            # Extract container ports
            ports = []
            containers_info = []
            
            for container in pod.spec.containers:
                containers_info.append({
                    "name": container.name,
                    "image": container.image
                })
                
                if container.ports:
                    for port in container.ports:
                        ports.append(ContainerPort(
                            container=container.name,
                            port=port.container_port,
                            protocol=PortProtocol(port.protocol or "TCP"),
                            name=port.name
                        ))
            
            pod_nodes.append(PodNode(
                id=f"pod-{pod.metadata.namespace}-{pod.metadata.name}",
                name=pod.metadata.name,
                namespace=pod.metadata.namespace,
                node_id=f"node-{pod.spec.node_name}" if pod.spec.node_name else "node-unscheduled",
                ip=pod.status.pod_ip,
                phase=pod.status.phase or "Unknown",
                labels=pod.metadata.labels or {},
                service_account=pod.spec.service_account_name or "default",
                containers=containers_info,
                ports=ports
            ))
        
        return pod_nodes
    
    def _build_service_nodes(
        self, 
        services: list, 
        endpoints: list,
        pods: list[PodNode]
    ) -> list[ServiceNode]:
        """Build ServiceNode models from K8s services."""
        service_nodes = []
        
        # Build endpoints lookup
        endpoints_map = {}
        for ep in endpoints:
            if ep.subsets:
                ips = []
                for subset in ep.subsets:
                    ips.extend([addr.ip for addr in (subset.addresses or [])])
                endpoints_map[f"{ep.metadata.namespace}/{ep.metadata.name}"] = ips
        
        # Build pod IP lookup
        pod_by_ip = {pod.ip: pod.id for pod in pods if pod.ip}
        
        for svc in services:
            # Get external IP
            external_ip = None
            if svc.status.load_balancer and svc.status.load_balancer.ingress:
                ingress = svc.status.load_balancer.ingress[0]
                external_ip = ingress.ip if hasattr(ingress, 'ip') else ingress.hostname
            
            # Map endpoints to pod IDs
            endpoint_key = f"{svc.metadata.namespace}/{svc.metadata.name}"
            endpoint_ips = endpoints_map.get(endpoint_key, [])
            endpoint_pod_ids = [pod_by_ip[ip] for ip in endpoint_ips if ip in pod_by_ip]
            
            # Build service ports
            ports = []
            for p in (svc.spec.ports or []):
                ports.append(ServicePort(
                    port=p.port,
                    target_port=str(p.target_port) if p.target_port else str(p.port),
                    protocol=PortProtocol(p.protocol or "TCP"),
                    name=p.name
                ))
            
            service_nodes.append(ServiceNode(
                id=f"svc-{svc.metadata.namespace}-{svc.metadata.name}",
                name=svc.metadata.name,
                namespace=svc.metadata.namespace,
                service_type=svc.spec.type or "ClusterIP",
                cluster_ip=svc.spec.cluster_ip,
                external_ip=external_ip,
                ports=ports,
                selector=svc.spec.selector or {},
                endpoint_pod_ids=endpoint_pod_ids
            ))
        
        return service_nodes
    
    def _build_network_policy_nodes(
        self, 
        netpols: list,
        pods: list[PodNode]
    ) -> list[NetworkPolicyNode]:
        """Build NetworkPolicyNode models from K8s NetworkPolicies."""
        netpol_nodes = []
        
        for np in netpols:
            # Parse ingress rules
            ingress_rules = []
            for rule in (np.spec.ingress or []):
                ingress_rules.append(NetworkPolicyRule(
                    ports=[{"port": p.port, "protocol": p.protocol} for p in (rule.ports or [])],
                    from_sources=[self._parse_peer(peer) for peer in (rule.from_ or [])]
                ))
            
            # Parse egress rules
            egress_rules = []
            for rule in (np.spec.egress or []):
                egress_rules.append(NetworkPolicyRule(
                    ports=[{"port": p.port, "protocol": p.protocol} for p in (rule.ports or [])],
                    to_destinations=[self._parse_peer(peer) for peer in (rule.to or [])]
                ))
            
            # Find affected pods
            affected_pod_ids = [
                pod.id for pod in pods
                if pod.namespace == np.metadata.namespace and 
                self._matches_selector(pod.labels, np.spec.pod_selector.match_labels or {})
            ]
            
            netpol_nodes.append(NetworkPolicyNode(
                id=f"netpol-{np.metadata.namespace}-{np.metadata.name}",
                name=np.metadata.name,
                namespace=np.metadata.namespace,
                pod_selector=np.spec.pod_selector.match_labels or {},
                policy_types=np.spec.policy_types or [],
                ingress_rules=ingress_rules,
                egress_rules=egress_rules,
                affected_pod_ids=affected_pod_ids
            ))
        
        return netpol_nodes
    
    def _parse_peer(self, peer) -> dict:
        """Parse NetworkPolicyPeer into dict."""
        result = {}
        if hasattr(peer, 'pod_selector') and peer.pod_selector:
            result['pod_selector'] = peer.pod_selector.match_labels or {}
        if hasattr(peer, 'namespace_selector') and peer.namespace_selector:
            result['namespace_selector'] = peer.namespace_selector.match_labels or {}
        if hasattr(peer, 'ip_block') and peer.ip_block:
            result['ip_block'] = {"cidr": peer.ip_block.cidr}
        return result
    
    def _matches_selector(self, labels: dict, selector: dict) -> bool:
        """Check if labels match selector."""
        if not selector:  # Empty selector matches all
            return True
        return all(labels.get(k) == v for k, v in selector.items())
    
    def _build_communication_flows(
        self,
        pods: list[PodNode],
        services: list[ServiceNode],
        netpols: list[NetworkPolicyNode]
    ) -> list[NetworkFlow]:
        """Build communication flows between nodes."""
        flows = []
        
        # Service -> Pod flows
        for service in services:
            for pod_id in service.endpoint_pod_ids:
                for port in service.ports:
                    flow_id = f"flow-{service.id}-{pod_id}-{port.port}"
                    flows.append(NetworkFlow(
                        id=flow_id,
                        source_type=NodeType.SERVICE,
                        source_id=service.id,
                        destination_type=NodeType.POD,
                        destination_id=pod_id,
                        protocol=port.protocol,
                        port=port.port,
                        allowed=True,
                        path=[service.id, pod_id]
                    ))
        
        # Pod -> Pod flows (based on labels and namespace)
        # This is simplified - full implementation would analyze actual connections
        for pod in pods:
            if pod.ports:
                for port in pod.ports:
                    flow_id = f"flow-potential-{pod.id}-{port.port}"
                    flows.append(NetworkFlow(
                        id=flow_id,
                        source_type=NodeType.POD,
                        source_id="*",  # Any pod
                        destination_type=NodeType.POD,
                        destination_id=pod.id,
                        protocol=port.protocol,
                        port=port.port,
                        allowed=self._check_flow_allowed(pod, port, netpols),
                        policy_refs=[np.id for np in netpols if pod.id in np.affected_pod_ids]
                    ))
        
        return flows
    
    def _check_flow_allowed(
        self, 
        pod: PodNode, 
        port: ContainerPort, 
        netpols: list[NetworkPolicyNode]
    ) -> bool:
        """Check if flow to pod:port is allowed by network policies."""
        # If no policies affect this pod, all traffic is allowed
        affecting_policies = [np for np in netpols if pod.id in np.affected_pod_ids]
        if not affecting_policies:
            return True
        
        # If policies exist, check if any allow this port
        for policy in affecting_policies:
            if "Ingress" in policy.policy_types:
                for rule in policy.ingress_rules:
                    if not rule.ports or any(p.get("port") == port.port for p in rule.ports):
                        return True
        
        return False
    
    def _calculate_namespace_connectivity(
        self,
        pods: list[PodNode],
        netpols: list[NetworkPolicyNode]
    ) -> list[NamespaceConnectivity]:
        """Calculate namespace-to-namespace connectivity matrix."""
        namespaces = set(pod.namespace for pod in pods)
        connectivity = []
        
        for src_ns in namespaces:
            for dst_ns in namespaces:
                # Check if any NetworkPolicy blocks this
                blocking_policies = []
                allowing_policies = []
                
                for np in netpols:
                    if np.namespace == dst_ns and "Ingress" in np.policy_types:
                        # Check if policy allows from src_ns
                        allows = any(
                            rule.from_sources and 
                            any(src.get('namespace_selector', {}) for src in rule.from_sources)
                            for rule in np.ingress_rules
                        )
                        if allows:
                            allowing_policies.append(np.id)
                        else:
                            blocking_policies.append(np.id)
                
                connectivity.append(NamespaceConnectivity(
                    source_namespace=src_ns,
                    destination_namespace=dst_ns,
                    allowed=len(blocking_policies) == 0,
                    blocking_policies=blocking_policies,
                    allowing_policies=allowing_policies
                ))
        
        return connectivity
