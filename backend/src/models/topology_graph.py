"""Graph-based network topology models for AKS Arc cluster analysis."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes in the topology graph."""
    
    COMPUTE_NODE = "node"
    POD = "pod"
    SERVICE = "service"
    EXTERNAL = "external"
    NAMESPACE = "namespace"


class PortProtocol(str, Enum):
    """Network protocols."""
    
    TCP = "TCP"
    UDP = "UDP"
    SCTP = "SCTP"


class ContainerPort(BaseModel):
    """Container port specification."""
    
    container: str
    port: int
    protocol: PortProtocol = PortProtocol.TCP
    name: Optional[str] = None


class ServicePort(BaseModel):
    """Service port specification."""
    
    port: int
    target_port: str | int
    protocol: PortProtocol = PortProtocol.TCP
    name: Optional[str] = None


class ComputeNode(BaseModel):
    """Kubernetes compute node in the topology."""
    
    id: str = Field(..., description="Unique identifier: node-<name>")
    name: str
    type: Literal[NodeType.COMPUTE_NODE] = NodeType.COMPUTE_NODE
    ip: str
    role: Literal["control-plane", "worker"] = "worker"
    capacity: dict[str, str] = Field(default_factory=dict)
    allocatable: dict[str, str] = Field(default_factory=dict)
    conditions: list[dict[str, Any]] = Field(default_factory=list)


class PodNode(BaseModel):
    """Pod workload in the topology."""
    
    id: str = Field(..., description="Unique identifier: pod-<namespace>-<name>")
    name: str
    namespace: str
    type: Literal[NodeType.POD] = NodeType.POD
    node_id: str = Field(..., description="References ComputeNode id")
    ip: Optional[str] = None
    phase: str
    labels: dict[str, str] = Field(default_factory=dict)
    service_account: str = "default"
    containers: list[dict[str, Any]] = Field(default_factory=list)
    ports: list[ContainerPort] = Field(default_factory=list)


class ServiceNode(BaseModel):
    """Kubernetes Service in the topology."""
    
    id: str = Field(..., description="Unique identifier: svc-<namespace>-<name>")
    name: str
    namespace: str
    type: Literal[NodeType.SERVICE] = NodeType.SERVICE
    service_type: Literal["ClusterIP", "NodePort", "LoadBalancer", "ExternalName"]
    cluster_ip: Optional[str] = None
    external_ip: Optional[str] = None
    ports: list[ServicePort] = Field(default_factory=list)
    selector: dict[str, str] = Field(default_factory=dict)
    endpoint_pod_ids: list[str] = Field(default_factory=list, description="Pod IDs this service routes to")


class ExternalEndpoint(BaseModel):
    """External endpoint accessed by cluster workloads."""
    
    id: str = Field(..., description="Unique identifier: ext-<hash>")
    type: Literal[NodeType.EXTERNAL] = NodeType.EXTERNAL
    ip: Optional[str] = None
    domain: Optional[str] = None
    port: int
    protocol: PortProtocol = PortProtocol.TCP
    accessed_by_pod_ids: list[str] = Field(default_factory=list)


class NetworkFlow(BaseModel):
    """Communication flow between nodes in the topology."""
    
    id: str
    source_type: NodeType
    source_id: str
    destination_type: NodeType
    destination_id: str
    protocol: PortProtocol
    port: int
    allowed: bool = Field(default=True, description="Based on NetworkPolicy analysis")
    policy_refs: list[str] = Field(default_factory=list, description="NetworkPolicy IDs affecting this flow")
    path: list[str] = Field(default_factory=list, description="Ordered list of node IDs in the path")


class NetworkPolicyRule(BaseModel):
    """Network policy rule definition."""
    
    ports: list[dict[str, Any]] = Field(default_factory=list)
    from_sources: list[dict[str, Any]] = Field(default_factory=list)
    to_destinations: list[dict[str, Any]] = Field(default_factory=list)


class NetworkPolicyNode(BaseModel):
    """Kubernetes NetworkPolicy in the topology."""
    
    id: str = Field(..., description="Unique identifier: netpol-<namespace>-<name>")
    name: str
    namespace: str
    pod_selector: dict[str, str] = Field(default_factory=dict)
    policy_types: list[Literal["Ingress", "Egress"]] = Field(default_factory=list)
    ingress_rules: list[NetworkPolicyRule] = Field(default_factory=list)
    egress_rules: list[NetworkPolicyRule] = Field(default_factory=list)
    affected_pod_ids: list[str] = Field(default_factory=list)


class NamespaceConnectivity(BaseModel):
    """Connectivity status between namespaces."""
    
    source_namespace: str
    destination_namespace: str
    allowed: bool
    blocking_policies: list[str] = Field(default_factory=list)
    allowing_policies: list[str] = Field(default_factory=list)


class TopologyMetadata(BaseModel):
    """Metadata about the topology snapshot."""
    
    cluster_name: str = "unknown"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    k8s_version: str = "unknown"
    platform: Literal["aks-arc", "k3s", "aks", "eks", "gke", "other"] = "other"
    node_count: int = 0
    pod_count: int = 0
    service_count: int = 0
    namespace_count: int = 0


class MermaidExport(BaseModel):
    """Mermaid.js graph syntax export."""
    
    graph_type: Literal["graph", "flowchart"] = "graph"
    direction: Literal["TD", "LR", "TB", "RL"] = "LR"
    syntax: str = Field(..., description="Complete Mermaid.js syntax")


class D3GraphExport(BaseModel):
    """D3.js force-directed graph export."""
    
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    links: list[dict[str, Any]] = Field(default_factory=list)


class TopologyGraph(BaseModel):
    """Complete network topology graph with all nodes and flows."""
    
    metadata: TopologyMetadata
    compute_nodes: list[ComputeNode] = Field(default_factory=list)
    pods: list[PodNode] = Field(default_factory=list)
    services: list[ServiceNode] = Field(default_factory=list)
    external_endpoints: list[ExternalEndpoint] = Field(default_factory=list)
    network_policies: list[NetworkPolicyNode] = Field(default_factory=list)
    communication_flows: list[NetworkFlow] = Field(default_factory=list)
    namespace_connectivity: list[NamespaceConnectivity] = Field(default_factory=list)
    
    # Export formats
    mermaid_export: Optional[MermaidExport] = None
    d3_export: Optional[D3GraphExport] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "cluster_name": "aks-arc-cluster-01",
                    "platform": "aks-arc",
                    "k8s_version": "1.28.0"
                }
            }
        }
