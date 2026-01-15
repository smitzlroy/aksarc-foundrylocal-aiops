"""
Mermaid.js graph exporter for network topology visualization.

Generates Mermaid syntax for rendering cluster topology as graphs.
"""

from src.models.topology_graph import TopologyGraph, NodeType, PortProtocol


class MermaidExporter:
    """Export TopologyGraph to Mermaid.js syntax."""
    
    @staticmethod
    def export_flowchart(topology: TopologyGraph) -> str:
        """Generate Mermaid flowchart syntax.
        
        Args:
            topology: TopologyGraph to export
            
        Returns:
            Mermaid flowchart syntax string
        """
        lines = ["graph TB"]
        lines.append("    %% Network Topology")
        lines.append("")
        
        # Add compute nodes
        lines.append("    %% Compute Nodes")
        for node in topology.compute_nodes:
            node_id = node.id.replace("-", "_")
            style = "control" if node.role == "control-plane" else "worker"
            lines.append(f"    {node_id}[\"{node.name}<br/>({node.role})\"]")
            lines.append(f"    class {node_id} {style}Node")
        lines.append("")
        
        # Add pods
        lines.append("    %% Pods")
        for pod in topology.pods[:20]:  # Limit to first 20 to keep graph readable
            pod_id = pod.id.replace("-", "_")
            lines.append(f"    {pod_id}[\"{pod.name}<br/>{pod.namespace}<br/>{pod.phase}\"]")
            
            # Link pod to node
            node_id = pod.node_id.replace("-", "_")
            lines.append(f"    {node_id} --> {pod_id}")
        
        if len(topology.pods) > 20:
            lines.append(f"    more_pods[\"... and {len(topology.pods) - 20} more pods\"]")
        
        lines.append("")
        
        # Add services
        lines.append("    %% Services")
        for svc in topology.services[:15]:  # Limit to keep graph readable
            svc_id = svc.id.replace("-", "_")
            lines.append(f"    {svc_id}{{{{\"<b>{svc.name}</b><br/>{svc.service_type}<br/>{svc.cluster_ip}\"}}}}")
            lines.append(f"    class {svc_id} serviceNode")
            
            # Link service to pods
            for pod_id in svc.endpoint_pod_ids[:5]:
                pod_id_clean = pod_id.replace("-", "_")
                lines.append(f"    {svc_id} -.-> {pod_id_clean}")
        
        if len(topology.services) > 15:
            lines.append(f"    more_svcs[\"... and {len(topology.services) - 15} more services\"]")
        
        lines.append("")
        
        # Add communication flows
        lines.append("    %% Communication Flows")
        for flow in topology.communication_flows[:30]:  # Limit edges
            src_id = flow.source_id.replace("-", "_")
            dst_id = flow.destination_id.replace("-", "_")
            
            if flow.source_id == "*":
                continue  # Skip wildcard sources for cleaner graph
            
            label = f"{flow.protocol.value}:{flow.port}"
            arrow = "==>" if flow.allowed else "-.-x"
            
            lines.append(f"    {src_id} {arrow}|{label}| {dst_id}")
        
        lines.append("")
        
        # Add styling
        lines.append("    %% Styling")
        lines.append("    classDef controlNode fill:#e1f5ff,stroke:#01579b,stroke-width:2px")
        lines.append("    classDef workerNode fill:#f3e5f5,stroke:#4a148c,stroke-width:2px")
        lines.append("    classDef serviceNode fill:#fff9c4,stroke:#f57f17,stroke-width:2px")
        
        return "\n".join(lines)
    
    @staticmethod
    def export_network_diagram(topology: TopologyGraph) -> str:
        """Generate Mermaid network diagram showing connectivity.
        
        Focuses on service-to-pod communication with NetworkPolicy enforcement.
        """
        lines = ["graph LR"]
        lines.append("    %% Service Connectivity Diagram")
        lines.append("")
        
        # Group by namespace
        namespaces = set(pod.namespace for pod in topology.pods)
        
        for ns in sorted(namespaces):
            lines.append(f"    subgraph {ns}[Namespace: {ns}]")
            
            # Add pods in this namespace
            ns_pods = [p for p in topology.pods if p.namespace == ns]
            for pod in ns_pods[:10]:  # Limit per namespace
                pod_id = pod.id.replace("-", "_")
                lines.append(f"        {pod_id}[\"{pod.name}\"]")
            
            # Add services in this namespace
            ns_svcs = [s for s in topology.services if s.namespace == ns]
            for svc in ns_svcs[:5]:
                svc_id = svc.id.replace("-", "_")
                lines.append(f"        {svc_id}{{{{{svc.name}}}}}")
                
                # Connect to endpoints
                for pod_id in svc.endpoint_pod_ids[:3]:
                    pod_id_clean = pod_id.replace("-", "_")
                    lines.append(f"        {svc_id} --> {pod_id_clean}")
            
            lines.append("    end")
            lines.append("")
        
        # Show inter-namespace flows
        lines.append("    %% Cross-Namespace Flows")
        for flow in topology.communication_flows:
            if flow.source_id == "*":
                continue
            
            # Extract namespaces from IDs
            src_parts = flow.source_id.split("-")
            dst_parts = flow.destination_id.split("-")
            
            if len(src_parts) > 2 and len(dst_parts) > 2:
                src_ns = src_parts[1]
                dst_ns = dst_parts[1]
                
                if src_ns != dst_ns:
                    src_id = flow.source_id.replace("-", "_")
                    dst_id = flow.destination_id.replace("-", "_")
                    arrow = "==>" if flow.allowed else "-.-x"
                    label = f"{flow.protocol.value}:{flow.port}"
                    
                    lines.append(f"    {src_id} {arrow}|{label}| {dst_id}")
        
        return "\n".join(lines)
    
    @staticmethod
    def export_sequence_diagram(topology: TopologyGraph) -> str:
        """Generate Mermaid sequence diagram for request flow.
        
        Shows typical request path: External -> Service -> Pod
        """
        lines = ["sequenceDiagram"]
        lines.append("    participant Client")
        lines.append("    participant LoadBalancer")
        
        # Find LoadBalancer services
        lb_services = [s for s in topology.services if s.service_type == "LoadBalancer"]
        
        if not lb_services:
            lines.append("    Note right of Client: No LoadBalancer services found")
            return "\n".join(lines)
        
        # Show first LB service flow
        svc = lb_services[0]
        lines.append(f"    participant {svc.name}")
        
        if svc.endpoint_pod_ids:
            first_pod_id = svc.endpoint_pod_ids[0]
            pod = next((p for p in topology.pods if p.id == first_pod_id), None)
            
            if pod:
                lines.append(f"    participant {pod.name}")
                lines.append("")
                lines.append("    Client->>+LoadBalancer: HTTP Request")
                lines.append(f"    LoadBalancer->>+{svc.name}: Route to Service")
                lines.append(f"    {svc.name}->>+{pod.name}: Forward to Pod")
                lines.append(f"    {pod.name}-->>-{svc.name}: Response")
                lines.append(f"    {svc.name}-->>-LoadBalancer: Response")
                lines.append("    LoadBalancer-->>-Client: HTTP Response")
        
        return "\n".join(lines)
    
    @staticmethod
    def export_namespace_connectivity_matrix(topology: TopologyGraph) -> str:
        """Generate Mermaid diagram showing namespace-to-namespace connectivity.
        
        Uses a matrix-style visualization.
        """
        lines = ["graph TD"]
        lines.append("    %% Namespace Connectivity Matrix")
        lines.append("")
        
        if not topology.namespace_connectivity:
            lines.append("    no_data[\"No connectivity data available\"]")
            return "\n".join(lines)
        
        # Get unique namespaces
        namespaces = set()
        for conn in topology.namespace_connectivity:
            namespaces.add(conn.source_namespace)
            namespaces.add(conn.destination_namespace)
        
        ns_list = sorted(namespaces)
        
        # Create nodes for each namespace
        for ns in ns_list:
            ns_id = ns.replace("-", "_")
            lines.append(f"    {ns_id}[\"{ns}\"]")
        
        lines.append("")
        
        # Add connectivity edges
        for conn in topology.namespace_connectivity:
            src_id = conn.source_namespace.replace("-", "_")
            dst_id = conn.destination_namespace.replace("-", "_")
            
            if src_id == dst_id:
                continue  # Skip self-connections
            
            arrow = "-->" if conn.allowed else "-.-x"
            style = "green" if conn.allowed else "red"
            
            lines.append(f"    {src_id} {arrow} {dst_id}")
            lines.append(f"    linkStyle {len([l for l in lines if 'linkStyle' in l])} stroke:{style}")
        
        return "\n".join(lines)
