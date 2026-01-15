"""
API v1: Topology endpoints

Graph-based network topology queries and visualizations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

import structlog

from src.models.topology_graph import TopologyGraph
from src.reasoning.topology_analyzer import TopologyGraphBuilder
from src.exporters.mermaid import MermaidExporter

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/topology", tags=["topology"])

# Global instance (will be injected via dependency injection in production)
_topology_builder: Optional[TopologyGraphBuilder] = None


def set_topology_builder(builder: TopologyGraphBuilder):
    """Inject topology builder dependency."""
    global _topology_builder
    _topology_builder = builder


@router.get("", response_model=TopologyGraph)
async def get_topology():
    """Get complete network topology graph.
    
    Returns graph with nodes (compute, pods, services), edges (communication flows),
    and NetworkPolicy enforcement analysis.
    
    Returns:
        TopologyGraph: Complete topology with metadata
    """
    if not _topology_builder:
        raise HTTPException(status_code=503, detail="Topology builder not initialized")
    
    try:
        topology = await _topology_builder.build_topology()
        return topology
    except Exception as e:
        logger.error("topology_query_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build topology: {str(e)}")


@router.get("/namespace/{namespace}")
async def get_topology_for_namespace(namespace: str):
    """Get topology filtered to specific namespace.
    
    Args:
        namespace: Kubernetes namespace to filter
        
    Returns:
        Filtered topology graph
    """
    if not _topology_builder:
        raise HTTPException(status_code=503, detail="Topology builder not initialized")
    
    try:
        topology = await _topology_builder.build_topology()
        
        # Filter to namespace
        filtered_topology = TopologyGraph(
            metadata=topology.metadata,
            compute_nodes=topology.compute_nodes,
            pods=[p for p in topology.pods if p.namespace == namespace],
            services=[s for s in topology.services if s.namespace == namespace],
            network_policies=[np for np in topology.network_policies if np.namespace == namespace],
            communication_flows=[
                f for f in topology.communication_flows
                if namespace in f.source_id or namespace in f.destination_id
            ],
            namespace_connectivity=[
                nc for nc in topology.namespace_connectivity
                if nc.source_namespace == namespace or nc.destination_namespace == namespace
            ]
        )
        
        return filtered_topology
    except Exception as e:
        logger.error("namespace_topology_failed", namespace=namespace, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/mermaid")
async def export_mermaid_flowchart(
    diagram_type: str = Query("flowchart", description="Type of diagram: flowchart, network, sequence, matrix")
):
    """Export topology as Mermaid.js syntax.
    
    Args:
        diagram_type: Type of Mermaid diagram to generate
        
    Returns:
        Mermaid syntax string
    """
    if not _topology_builder:
        raise HTTPException(status_code=503, detail="Topology builder not initialized")
    
    try:
        topology = await _topology_builder.build_topology()
        
        exporter = MermaidExporter()
        
        if diagram_type == "flowchart":
            mermaid_syntax = exporter.export_flowchart(topology)
        elif diagram_type == "network":
            mermaid_syntax = exporter.export_network_diagram(topology)
        elif diagram_type == "sequence":
            mermaid_syntax = exporter.export_sequence_diagram(topology)
        elif diagram_type == "matrix":
            mermaid_syntax = exporter.export_namespace_connectivity_matrix(topology)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown diagram type: {diagram_type}")
        
        return {"mermaid": mermaid_syntax, "diagram_type": diagram_type}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("mermaid_export_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows")
async def get_communication_flows(
    source_type: Optional[str] = None,
    destination_type: Optional[str] = None,
    allowed_only: bool = False
):
    """Get communication flows with optional filtering.
    
    Args:
        source_type: Filter by source node type (pod, service, compute)
        destination_type: Filter by destination node type
        allowed_only: Only return flows allowed by NetworkPolicies
        
    Returns:
        List of NetworkFlow objects
    """
    if not _topology_builder:
        raise HTTPException(status_code=503, detail="Topology builder not initialized")
    
    try:
        topology = await _topology_builder.build_topology()
        flows = topology.communication_flows
        
        # Apply filters
        if source_type:
            flows = [f for f in flows if f.source_type.value == source_type.lower()]
        
        if destination_type:
            flows = [f for f in flows if f.destination_type.value == destination_type.lower()]
        
        if allowed_only:
            flows = [f for f in flows if f.allowed]
        
        return {"flows": flows, "count": len(flows)}
    except Exception as e:
        logger.error("flows_query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/namespace-connectivity")
async def get_namespace_connectivity():
    """Get namespace-to-namespace connectivity matrix.
    
    Shows which namespaces can communicate with each other based on NetworkPolicies.
    
    Returns:
        List of NamespaceConnectivity objects
    """
    if not _topology_builder:
        raise HTTPException(status_code=503, detail="Topology builder not initialized")
    
    try:
        topology = await _topology_builder.build_topology()
        return {
            "connectivity": topology.namespace_connectivity,
            "count": len(topology.namespace_connectivity)
        }
    except Exception as e:
        logger.error("namespace_connectivity_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
