"""API routes for cluster operations and AI chat."""

from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.models.chat import ChatMessage, ChatResponse
from src.models.cluster import ClusterStatus, Event, PodStatus
from src.services.context import ContextBuffer
from src.services.foundry import FoundryClient
from src.services.kubernetes import KubernetesClient
from src.services.foundry_manager import get_foundry_manager
from src.services.aks_arc_diagnostics import AksArcDiagnostics
from src.services.network_analyzer import NetworkAnalyzer

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api", tags=["api"])

# Global service instances (initialized in main.py)
k8s_client: Optional[KubernetesClient] = None
context_buffer: Optional[ContextBuffer] = None
foundry_client: Optional[FoundryClient] = None


def initialize_services(
    k8s: KubernetesClient,
    context: ContextBuffer,
    foundry: FoundryClient,
) -> None:
    """Initialize global service instances.
    
    Args:
        k8s: Kubernetes client instance
        context: Context buffer instance
        foundry: Foundry client instance
    """
    global k8s_client, context_buffer, foundry_client
    k8s_client = k8s
    context_buffer = context
    foundry_client = foundry
    logger.info("api_services_initialized")


@router.get("/cluster/status", response_model=ClusterStatus)
async def get_cluster_status() -> ClusterStatus:
    """Get current cluster status with all pods and recent events.
    
    Returns:
        ClusterStatus with pods and events
        
    Raises:
        HTTPException: If Kubernetes client not initialized or connection fails
    """
    if not k8s_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not initialized")
    
    try:
        status = await k8s_client.get_cluster_status()
        
        # Store in context buffer
        if context_buffer:
            context_buffer.add(status)
        
        logger.info(
            "cluster_status_retrieved",
            pod_count=len(status.pods),
            event_count=len(status.events),
        )
        
        return status
        
    except Exception as e:
        logger.error("cluster_status_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cluster status: {e}")


@router.get("/cluster/pods", response_model=list[PodStatus])
async def get_pods(
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    phase: Optional[str] = Query(None, description="Filter by phase (Running, Pending, etc.)"),
) -> list[PodStatus]:
    """Get all pods with optional filters.
    
    Args:
        namespace: Filter by namespace
        phase: Filter by phase
        
    Returns:
        List of PodStatus
        
    Raises:
        HTTPException: If services not initialized or query fails
    """
    if not k8s_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not initialized")
    
    try:
        status = await k8s_client.get_cluster_status()
        pods = status.pods
        
        # Apply filters
        if namespace:
            pods = [p for p in pods if p.namespace == namespace]
        if phase:
            pods = [p for p in pods if p.phase.value == phase]
        
        logger.info("pods_retrieved", count=len(pods), namespace=namespace, phase=phase)
        
        return pods
        
    except Exception as e:
        logger.error("pods_query_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get pods: {e}")


@router.get("/cluster/events", response_model=list[Event])
async def get_events(
    hours: int = Query(1, ge=1, le=24, description="Hours to look back"),
    event_type: Optional[str] = Query(None, description="Filter by type (Normal, Warning)"),
) -> list[Event]:
    """Get recent cluster events.
    
    Args:
        hours: Hours to look back (1-24)
        event_type: Filter by event type
        
    Returns:
        List of Events
        
    Raises:
        HTTPException: If services not initialized or query fails
    """
    if not context_buffer:
        raise HTTPException(status_code=503, detail="Context buffer not initialized")
    
    try:
        # Get events from context buffer
        if event_type:
            events = context_buffer.get_events_by_type(event_type, hours)
        else:
            # Get all recent events
            snapshots = context_buffer.get_recent(hours)
            events = []
            seen = set()
            for snapshot in reversed(snapshots):
                for event in snapshot.events:
                    if event.name not in seen:
                        seen.add(event.name)
                        events.append(event)
        
        logger.info("events_retrieved", count=len(events), hours=hours, type=event_type)
        
        return events
        
    except Exception as e:
        logger.error("events_query_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get events: {e}")


@router.get("/cluster/pods/{namespace}/{pod_name}/logs")
async def get_pod_logs(
    namespace: str,
    pod_name: str,
    tail_lines: int = Query(100, ge=10, le=1000, description="Number of lines to retrieve"),
) -> dict[str, str]:
    """Get logs from a specific pod.
    
    Args:
        namespace: Pod namespace
        pod_name: Pod name
        tail_lines: Number of lines to retrieve
        
    Returns:
        Dictionary with logs
        
    Raises:
        HTTPException: If services not initialized or query fails
    """
    if not k8s_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not initialized")
    
    try:
        logs = await k8s_client.get_pod_logs(pod_name, namespace, tail_lines=tail_lines)
        
        logger.info("pod_logs_retrieved", pod=pod_name, namespace=namespace)
        
        return {"namespace": namespace, "pod": pod_name, "logs": logs}
        
    except Exception as e:
        logger.error("pod_logs_error", pod=pod_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get pod logs: {e}")


@router.get("/cluster/pods/{namespace}/{pod_name}/history", response_model=list[PodStatus])
async def get_pod_history(
    namespace: str,
    pod_name: str,
    hours: int = Query(1, ge=1, le=24, description="Hours to look back"),
) -> list[PodStatus]:
    """Get historical status of a specific pod.
    
    Args:
        namespace: Pod namespace
        pod_name: Pod name
        hours: Hours to look back
        
    Returns:
        List of PodStatus snapshots
        
    Raises:
        HTTPException: If services not initialized or query fails
    """
    if not context_buffer:
        raise HTTPException(status_code=503, detail="Context buffer not initialized")
    
    try:
        history = context_buffer.get_pod_history(pod_name, namespace, hours)
        
        logger.info("pod_history_retrieved", pod=pod_name, count=len(history))
        
        return history
        
    except Exception as e:
        logger.error("pod_history_error", pod=pod_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get pod history: {e}")


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    include_context: bool = Field(default=True, description="Include cluster context")


@router.post("/chat/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest) -> ChatResponse:
    """Send a query to the AI assistant with fallback to direct mode.
    
    Args:
        request: Chat request with message
        
    Returns:
        ChatResponse with AI response or direct data
        
    Raises:
        HTTPException: If services not initialized or query fails
    """
    # Try AI mode first using SDK, fallback to direct mode
    manager = get_foundry_manager()
    foundry_status = await manager.get_status()
    foundry_available = foundry_status.get("running", False)
    
    if foundry_available:
        # AI Mode - Use Foundry SDK
        try:
            # Get platform info for context-aware system prompt
            platform_info = await k8s_client.get_platform_info() if k8s_client else {'type': 'kubernetes'}
            
            # Build enhanced system prompt with platform awareness
            base_prompt = """You are a Kubernetes operations assistant. Your role is to help users understand and manage their Kubernetes cluster.

When answering questions:
1. Provide direct, actionable information about the cluster
2. If given cluster data, analyze it and answer based on that data
3. Be concise but thorough
4. Format responses clearly with bullet points or tables when appropriate
5. Focus on operational insights, not just commands

DO NOT provide kubectl commands or tutorials unless specifically asked.
ALWAYS use the cluster data provided in the user's message to give specific answers about THEIR cluster."""

            # Add platform-specific guidance
            if platform_info.get('type') == 'aks-arc':
                base_prompt += """

**IMPORTANT: This is an AKS Arc (Azure Kubernetes Service on Azure Arc) cluster.**

When providing assistance:
- Consider AKS Arc-specific features like Azure Arc agents and hybrid connectivity
- Be aware of Azure-integrated monitoring and diagnostics capabilities
- If troubleshooting, mention that specialized AKS Arc diagnostic tools are available via the diagnostics panel
- For persistent issues, recommend checking Azure Arc agent health and connectivity
- Consider that this cluster may have dependencies on Azure services and hybrid networking"""
            elif platform_info.get('type') == 'k3s':
                base_prompt += """

**IMPORTANT: This is a k3s (lightweight Kubernetes) cluster.**

When providing assistance:
- Consider k3s-specific features like Traefik ingress controller and ServiceLB
- Be aware that k3s may use SQLite instead of etcd for small deployments
- Resource constraints may be more relevant on k3s clusters
- k3s-specific namespaces and components (like klipper-lb) are normal"""

            system_prompt = base_prompt

            # Build context from actual cluster state
            context = ""
            if request.include_context and context_buffer:
                latest = context_buffer.get_latest()
                if latest:
                    # Build comprehensive cluster summary
                    running_pods = [p for p in latest.pods if p.phase.value == "Running"]
                    pending_pods = [p for p in latest.pods if p.phase.value == "Pending"]
                    failed_pods = [p for p in latest.pods if p.phase.value == "Failed"]
                    
                    # Get pod details
                    pod_details = []
                    for pod in latest.pods:
                        pod_details.append(
                            f"  - {pod.name} (namespace: {pod.namespace}, node: {pod.node}, "
                            f"status: {pod.phase.value}, restarts: {pod.restarts}, ip: {pod.ip})"
                        )
                    
                    # Get node info
                    nodes = set(p.node for p in latest.pods)
                    node_summary = []
                    for node in nodes:
                        pods_on_node = [p for p in latest.pods if p.node == node]
                        node_summary.append(f"  - {node}: {len(pods_on_node)} pods")
                    
                    # Get namespace info
                    namespaces = set(p.namespace for p in latest.pods)
                    ns_summary = []
                    for ns in namespaces:
                        pods_in_ns = [p for p in latest.pods if p.namespace == ns]
                        ns_summary.append(f"  - {ns}: {len(pods_in_ns)} pods")
                    
                    context = f"""CURRENT CLUSTER STATE (as of {latest.timestamp.isoformat()}):

SUMMARY:
- Total Pods: {len(latest.pods)}
- Running: {len(running_pods)}
- Pending: {len(pending_pods)}
- Failed: {len(failed_pods)}
- Nodes: {len(nodes)}
- Namespaces: {len(namespaces)}

NODES:
{chr(10).join(node_summary)}

NAMESPACES:
{chr(10).join(ns_summary)}

ALL PODS:
{chr(10).join(pod_details)}
"""
                    
                    # Add recent events if any
                    if latest.events:
                        event_lines = []
                        for event in latest.events[:10]:
                            event_lines.append(f"  - [{event.type}] {event.reason}: {event.message}")
                        context += f"\nRECENT EVENTS:\n{chr(10).join(event_lines)}\n"
            
            # Construct user message with context
            if context:
                full_message = f"{context}\nUSER QUESTION: {request.message}\n\nProvide a direct answer using the cluster data above."
            else:
                full_message = request.message
            
            # Use SDK's query_model method with system prompt
            response = await manager.query_model(full_message, stream=False, system_prompt=system_prompt)
            
            logger.info("chat_query_ai_mode", message_length=len(request.message), model=manager.current_model)
            return ChatResponse(response=response, timestamp=datetime.now(timezone.utc), context_used=bool(context), model=manager.current_model)
            
        except Exception as e:
            logger.error("chat_query_ai_error_falling_back", error=str(e))
            # Fall through to direct mode
    
    # Direct Mode - Return formatted K8s data without AI
    if not k8s_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not initialized")
    
    try:
        logger.info("chat_query_direct_mode", message=request.message)
        status = await k8s_client.get_cluster_status()
        
        # Parse user intent from message
        msg_lower = request.message.lower()
        response = "🔧 **Direct Mode** (AI not available)\n\n"
        
        if "pod" in msg_lower or "running" in msg_lower:
            running = [p for p in status.pods if p.phase.value == "Running"]
            response += f"**Running Pods ({len(running)}):**\n"
            for pod in running[:10]:
                response += f"• {pod.name} ({pod.namespace}) - {pod.node}\n"
                
        elif "node" in msg_lower or "pool" in msg_lower:
            nodes = list(set(p.node for p in status.pods))
            response += f"**Nodes ({len(nodes)}):**\n"
            for node in nodes:
                pods_on_node = [p for p in status.pods if p.node == node]
                response += f"• {node} - {len(pods_on_node)} pods\n"
                
        elif "system" in msg_lower or "arc" in msg_lower:
            system_pods = [p for p in status.pods if p.namespace in ["kube-system", "azure-arc"]]
            response += f"**System Pods ({len(system_pods)}):**\n"
            for pod in system_pods[:15]:
                response += f"• {pod.name} ({pod.namespace})\n"
                
        elif "restart" in msg_lower or "fail" in msg_lower:
            restarted = [p for p in status.pods if p.restarts > 0]
            response += f"**Pods with Restarts ({len(restarted)}):**\n"
            for pod in sorted(restarted, key=lambda x: x.restarts, reverse=True)[:10]:
                response += f"• {pod.name} - {pod.restarts} restarts\n"
                
        elif "health" in msg_lower or "status" in msg_lower:
            running = len([p for p in status.pods if p.phase.value == "Running"])
            pending = len([p for p in status.pods if p.phase.value == "Pending"])
            failed = len([p for p in status.pods if p.phase.value == "Failed"])
            nodes = len(set(p.node for p in status.pods))
            namespaces = len(set(p.namespace for p in status.pods))
            
            response += f"**Cluster Health:**\n"
            response += f"• Nodes: {nodes}\n"
            response += f"• Namespaces: {namespaces}\n"
            response += f"• Running Pods: {running}\n"
            response += f"• Pending Pods: {pending}\n"
            response += f"• Failed Pods: {failed}\n"
        else:
            # Default summary
            response += f"**Cluster Summary:**\n"
            response += f"• Total Pods: {len(status.pods)}\n"
            response += f"• Namespaces: {len(set(p.namespace for p in status.pods))}\n"
            response += f"• Nodes: {len(set(p.node for p in status.pods))}\n\n"
            response += "💡 Tip: Start Foundry for AI-powered insights!\n"
        
        return ChatResponse(
            response=response, 
            timestamp=datetime.now(timezone.utc),
            context_used=True,
            model="direct-mode"
        )
        
    except Exception as e:
        logger.error("chat_query_direct_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@router.get("/foundry/download/{model_name}")
async def get_download_progress(model_name: str):
    """Get download progress for a model.
    
    Args:
        model_name: Name of the model to check
        
    Returns:
        Download progress information
    """
    manager = get_foundry_manager()
    
    try:
        progress = await manager.get_download_progress(model_name)
        return progress
    except Exception as e:
        logger.error("download_progress_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get download progress: {e}")


@router.get("/topology")
async def get_topology():
    """Get cluster network topology for visualization.
    
    Returns:
        Network topology with nodes, pods, services, and connections
    """
    if not k8s_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not initialized")
    
    try:
        status = await k8s_client.get_cluster_status()
        
        # Build topology data
        nodes = {}
        namespaces = {}
        pods_data = []
        
        # Group by nodes
        for pod in status.pods:
            if pod.node not in nodes:
                nodes[pod.node] = {
                    "name": pod.node,
                    "pods": [],
                    "total_pods": 0
                }
            nodes[pod.node]["pods"].append(pod.name)
            nodes[pod.node]["total_pods"] += 1
            
            # Group by namespace
            if pod.namespace not in namespaces:
                namespaces[pod.namespace] = {
                    "name": pod.namespace,
                    "pods": [],
                    "pod_count": 0
                }
            namespaces[pod.namespace]["pods"].append(pod.name)
            namespaces[pod.namespace]["pod_count"] += 1
            
            # Pod details with network info
            pods_data.append({
                "name": pod.name,
                "namespace": pod.namespace,
                "node": pod.node,
                "ip": pod.ip,
                "status": pod.phase.value,  # Frontend expects 'status' not 'phase'
                "phase": pod.phase.value,   # Keep for backwards compatibility
                "restarts": pod.restarts,
                "labels": pod.labels
            })
        
        topology = {
            "nodes": list(nodes.values()),
            "namespaces": list(namespaces.values()),
            "pods": pods_data,
            "node_count": len(nodes),
            "namespace_count": len(namespaces),
            "pod_count": len(pods_data)
        }
        
        logger.info("topology_generated", nodes=len(nodes), pods=len(pods_data))
        return topology
        
    except Exception as e:
        logger.error("topology_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate topology: {e}")


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.
    
    Returns:
        Dictionary with service health status
    """
    k8s_healthy = k8s_client is not None and k8s_client._connected
    context_healthy = context_buffer is not None
    foundry_healthy = False
    
    if foundry_client:
        try:
            foundry_healthy = await foundry_client.health_check()
        except Exception:
            foundry_healthy = False
    
    return {
        "status": "healthy" if all([k8s_healthy, context_healthy]) else "degraded",
        "services": {
            "kubernetes": k8s_healthy,
            "context_buffer": context_healthy,
            "foundry": foundry_healthy,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Foundry Management Endpoints

@router.get("/foundry/status")
async def get_foundry_status():
    """Get Foundry Local status and available models."""
    manager = get_foundry_manager()
    status = await manager.get_status()
    logger.info("foundry_status_checked", running=status.get("running"))
    return status


@router.post("/foundry/start")
async def start_foundry(model: str = Query(..., description="Model name to run")):
    """Start Foundry Local with specified model."""
    logger.info("foundry_start_requested", model=model)
    manager = get_foundry_manager()
    result = await manager.start_model(model)
    
    if result.get("success"):
        # Update the global foundry client endpoint if available
        if result.get("endpoint"):
            logger.info("foundry_started_updating_client", endpoint=result["endpoint"])
    
    return result


@router.post("/foundry/stop")
async def stop_foundry():
    """Stop Foundry Local."""
    logger.info("foundry_stop_requested")
    manager = get_foundry_manager()
    return await manager.stop_model()


@router.post("/foundry/restart")
async def restart_foundry(model: str = Query(..., description="Model name to run")):
    """Restart Foundry Local with specified model."""
    logger.info("foundry_restart_requested", model=model)
    manager = get_foundry_manager()
    await manager.stop_model()
    return await manager.start_model(model)


# ============================================================================
# AKS Arc Platform Detection
# ============================================================================

@router.get("/platform/detect")
async def detect_platform():
    """Detect Kubernetes platform type (AKS Arc, k3s, vanilla k8s)."""
    if not k8s_client:
        raise HTTPException(status_code=500, detail="Kubernetes client not initialized")
    
    try:
        platform_info = await k8s_client.get_platform_info()
        logger.info("platform_detected", platform=platform_info.get('type'))
        return platform_info
    except Exception as e:
        logger.error("platform_detection_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AKS Arc Diagnostics
# ============================================================================

@router.get("/aksarc/diagnostics/check")
async def check_aks_arc_prerequisites():
    """Check if AKS Arc diagnostic tools are available."""
    diagnostics = AksArcDiagnostics()
    result = await diagnostics.check_prerequisites()
    return result


@router.post("/aksarc/diagnostics/install")
async def install_aks_arc_tools():
    """Install AKS Arc diagnostic tools (Support.AksArc module)."""
    diagnostics = AksArcDiagnostics()
    result = await diagnostics.install_support_module()
    return result


@router.get("/aksarc/diagnostics/run")
async def run_aks_arc_diagnostics():
    """Run AKS Arc diagnostic checks using Support.AksArc module."""
    diagnostics = AksArcDiagnostics()
    results = await diagnostics.run_diagnostic_checks()
    
    passed = sum(1 for r in results if r['status'] == 'Passed')
    failed = sum(1 for r in results if r['status'] == 'Failed')
    
    return {
        'total_tests': len(results),
        'passed': passed,
        'failed': failed,
        'results': results
    }


@router.post("/aksarc/diagnostics/remediate")
async def remediate_aks_arc_issues():
    """Run automatic remediation for common AKS Arc issues."""
    diagnostics = AksArcDiagnostics()
    result = await diagnostics.run_remediation()
    return result


# ============================================================================
# Network Topology Analysis
# ============================================================================

@router.get("/topology/analyze")
async def analyze_network_topology():
    """Analyze network topology with dependencies and policies."""
    if not k8s_client:
        raise HTTPException(status_code=500, detail="Kubernetes client not initialized")
    
    try:
        analyzer = NetworkAnalyzer(k8s_client)
        topology = await analyzer.analyze_topology()
        
        logger.info(
            "topology_analyzed",
            pods=len(topology['pods']),
            services=len(topology['services']),
            dependencies=len(topology['dependencies'])
        )
        
        return topology
    except Exception as e:
        logger.error("topology_analysis_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
