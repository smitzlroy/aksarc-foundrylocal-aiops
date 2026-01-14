"""
Kubernetes client and watcher service.

This module provides functionality to connect to Kubernetes clusters and watch
for changes in pods, events, and logs.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

import structlog
from kubernetes import client, config, watch
from kubernetes.client.exceptions import ApiException

from src.core.exceptions import KubernetesConnectionError, KubernetesPermissionError
from src.models.cluster import ClusterStatus, Event, PodPhase, PodStatus

logger = structlog.get_logger(__name__)


class KubernetesClient:
    """Kubernetes client for cluster interaction."""

    def __init__(self):
        """Initialize Kubernetes client."""
        self.core_v1: Optional[client.CoreV1Api] = None
        self.apps_v1: Optional[client.AppsV1Api] = None
        self.networking_v1: Optional[client.NetworkingV1Api] = None
        self._connected = False
        self._platform_info: Optional[dict] = None

    async def connect(self) -> None:
        """Connect to Kubernetes cluster using kubeconfig."""
        try:
            # Load kubeconfig (from default location or KUBECONFIG env var)
            config.load_kube_config()

            # Initialize API clients
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()

            # Test connection
            await asyncio.to_thread(self.core_v1.get_api_resources)
            
            # Detect platform type
            self._platform_info = await self._detect_platform()

            self._connected = True
            logger.info("kubernetes_connected", message="Successfully connected to Kubernetes cluster")

        except config.ConfigException as e:
            logger.error("kubernetes_config_error", error=str(e))
            raise KubernetesConnectionError(f"Failed to load kubeconfig: {e}") from e
        except ApiException as e:
            if e.status == 403:
                logger.error("kubernetes_permission_error", error=str(e))
                raise KubernetesPermissionError("Insufficient permissions to access cluster") from e
            logger.error("kubernetes_api_error", error=str(e))
            raise KubernetesConnectionError(f"Failed to connect to cluster: {e}") from e
        except Exception as e:
            logger.error("kubernetes_connection_error", error=str(e))
            raise KubernetesConnectionError(f"Unexpected error connecting to cluster: {e}") from e

    async def get_cluster_status(self) -> ClusterStatus:
        """Get current cluster status with all pods and recent events.
        
        Returns:
            ClusterStatus with pods and events
            
        Raises:
            KubernetesConnectionError: If not connected or API call fails
        """
        if not self._connected:
            raise KubernetesConnectionError("Not connected to cluster")

        try:
            # Get all pods across all namespaces
            pods_list = await asyncio.to_thread(
                self.core_v1.list_pod_for_all_namespaces
            )

            # Convert to our PodStatus model
            pods = []
            for pod in pods_list.items:
                pod_status = PodStatus(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    phase=PodPhase(pod.status.phase) if pod.status.phase else PodPhase.UNKNOWN,
                    node=pod.spec.node_name or "unscheduled",
                    containers=[c.name for c in pod.spec.containers],
                    ready=sum(1 for c in (pod.status.container_statuses or []) if c.ready),
                    total=len(pod.spec.containers),
                    restarts=sum(c.restart_count for c in (pod.status.container_statuses or [])),
                    created_at=pod.metadata.creation_timestamp,
                    ip=pod.status.pod_ip,
                    labels=pod.metadata.labels or {},
                )
                pods.append(pod_status)

            # Get recent events (last hour)
            events_list = await asyncio.to_thread(
                self.core_v1.list_event_for_all_namespaces
            )

            # Convert to our Event model and filter recent
            now = datetime.now(timezone.utc)
            events = []
            for event in events_list.items:
                if event.last_timestamp:
                    age_seconds = (now - event.last_timestamp).total_seconds()
                    if age_seconds <= 3600:  # Last hour
                        evt = Event(
                            timestamp=event.last_timestamp,
                            namespace=event.metadata.namespace,
                            name=event.metadata.name,
                            type=event.type or "Normal",
                            reason=event.reason or "Unknown",
                            message=event.message or "",
                            involved_object=f"{event.involved_object.kind}/{event.involved_object.name}",
                        )
                        events.append(evt)

            # Sort events by timestamp descending
            events.sort(key=lambda x: x.timestamp, reverse=True)

            cluster_status = ClusterStatus(
                timestamp=datetime.now(timezone.utc),
                pods=pods,
                events=events,
            )

            logger.info(
                "cluster_status_retrieved",
                pod_count=len(pods),
                event_count=len(events),
            )

            return cluster_status

        except ApiException as e:
            logger.error("kubernetes_api_error", error=str(e))
            raise KubernetesConnectionError(f"Failed to get cluster status: {e}") from e

    async def watch_pods(self, namespace: str = "default") -> AsyncGenerator[PodStatus, None]:
        """Watch for pod changes in real-time.
        
        Args:
            namespace: Namespace to watch (default: "default")
            
        Yields:
            PodStatus objects as pods change
            
        Raises:
            KubernetesConnectionError: If not connected or watch fails
        """
        if not self._connected:
            raise KubernetesConnectionError("Not connected to cluster")

        logger.info("starting_pod_watch", namespace=namespace)

        w = watch.Watch()
        try:
            # Watch pods in the specified namespace
            for event in w.stream(
                self.core_v1.list_namespaced_pod,
                namespace=namespace,
                timeout_seconds=0,  # Infinite watch
            ):
                pod = event["object"]
                event_type = event["type"]  # ADDED, MODIFIED, DELETED

                pod_status = PodStatus(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    phase=PodPhase(pod.status.phase) if pod.status.phase else PodPhase.UNKNOWN,
                    node=pod.spec.node_name or "unscheduled",
                    containers=[c.name for c in pod.spec.containers],
                    ready=sum(1 for c in (pod.status.container_statuses or []) if c.ready),
                    total=len(pod.spec.containers),
                    restarts=sum(c.restart_count for c in (pod.status.container_statuses or [])),
                    created_at=pod.metadata.creation_timestamp,
                    ip=pod.status.pod_ip,
                    labels=pod.metadata.labels or {},
                )

                logger.debug(
                    "pod_watch_event",
                    event_type=event_type,
                    pod=pod_status.name,
                    phase=pod_status.phase.value,
                )

                yield pod_status

        except ApiException as e:
            logger.error("pod_watch_error", error=str(e))
            w.stop()
            raise KubernetesConnectionError(f"Pod watch failed: {e}") from e
        finally:
            w.stop()

    async def watch_events(self, namespace: str = "default") -> AsyncGenerator[Event, None]:
        """Watch for Kubernetes events in real-time.
        
        Args:
            namespace: Namespace to watch (default: "default")
            
        Yields:
            Event objects as events occur
            
        Raises:
            KubernetesConnectionError: If not connected or watch fails
        """
        if not self._connected:
            raise KubernetesConnectionError("Not connected to cluster")

        logger.info("starting_event_watch", namespace=namespace)

        w = watch.Watch()
        try:
            for event in w.stream(
                self.core_v1.list_namespaced_event,
                namespace=namespace,
                timeout_seconds=0,
            ):
                k8s_event = event["object"]
                event_type = event["type"]

                evt = Event(
                    timestamp=k8s_event.last_timestamp or datetime.now(timezone.utc),
                    namespace=k8s_event.metadata.namespace,
                    name=k8s_event.metadata.name,
                    type=k8s_event.type or "Normal",
                    reason=k8s_event.reason or "Unknown",
                    message=k8s_event.message or "",
                    involved_object=f"{k8s_event.involved_object.kind}/{k8s_event.involved_object.name}",
                )

                logger.debug(
                    "event_watch_event",
                    event_type=event_type,
                    k8s_type=evt.type,
                    reason=evt.reason,
                )

                yield evt

        except ApiException as e:
            logger.error("event_watch_error", error=str(e))
            w.stop()
            raise KubernetesConnectionError(f"Event watch failed: {e}") from e
        finally:
            w.stop()

    async def get_pod_logs(
        self,
        pod_name: str,
        namespace: str = "default",
        container: Optional[str] = None,
        tail_lines: int = 100,
    ) -> str:
        """Get logs from a pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            container: Specific container (if pod has multiple)
            tail_lines: Number of lines to retrieve
            
        Returns:
            Pod logs as string
            
        Raises:
            KubernetesConnectionError: If not connected or API call fails
        """
        if not self._connected:
            raise KubernetesConnectionError("Not connected to cluster")

        try:
            logs = await asyncio.to_thread(
                self.core_v1.read_namespaced_pod_log,
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
            )

            logger.debug(
                "pod_logs_retrieved",
                pod=pod_name,
                namespace=namespace,
                lines=len(logs.splitlines()),
            )

            return logs

        except ApiException as e:
            logger.error("pod_logs_error", pod=pod_name, error=str(e))
            raise KubernetesConnectionError(f"Failed to get pod logs: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from cluster and cleanup resources."""
        self._connected = False
        self.core_v1 = None
        self.apps_v1 = None
        self.networking_v1 = None
        logger.info("kubernetes_disconnected")
    
    async def _detect_platform(self) -> dict:
        """Detect Kubernetes platform type (AKS Arc, k3s, vanilla k8s).
        
        Returns:
            dict: Platform information including type and metadata
        """
        try:
            nodes = await asyncio.to_thread(self.core_v1.list_node)
            
            # Check for AKS Arc
            for node in nodes.items:
                labels = node.metadata.labels or {}
                annotations = node.metadata.annotations or {}
                
                # AKS Arc detection via labels
                if 'kubernetes.azure.com/cluster' in labels:
                    logger.info("platform_detected", platform="AKS Arc")
                    return {
                        'type': 'aks-arc',
                        'name': 'AKS enabled by Azure Arc',
                        'cluster_name': labels.get('kubernetes.azure.com/cluster', 'unknown'),
                        'location': labels.get('kubernetes.azure.com/location', 'unknown'),
                        'arc_resource_id': labels.get('kubernetes.azure.com/arc-resource-id', ''),
                        'is_arc': True
                    }
                
                # AKS Arc detection via annotations
                if 'management.azure.com/arc-enabled' in annotations:
                    logger.info("platform_detected", platform="AKS Arc (annotation)")
                    return {
                        'type': 'aks-arc',
                        'name': 'AKS enabled by Azure Arc',
                        'cluster_name': 'unknown',
                        'location': 'unknown',
                        'arc_resource_id': '',
                        'is_arc': True
                    }
            
            # Check for AKS Arc namespaces
            namespaces = await asyncio.to_thread(self.core_v1.list_namespace)
            arc_namespaces = {'azure-arc', 'azurehybridcompute', 'azure-arc-release', 'arc-system'}
            found_arc_ns = [ns.metadata.name for ns in namespaces.items if ns.metadata.name in arc_namespaces]
            
            if found_arc_ns:
                logger.info("platform_detected", platform="AKS Arc (namespace)", namespaces=found_arc_ns)
                return {
                    'type': 'aks-arc',
                    'name': 'AKS enabled by Azure Arc',
                    'cluster_name': 'unknown',
                    'location': 'unknown',
                    'arc_resource_id': '',
                    'is_arc': True,
                    'arc_namespaces': found_arc_ns
                }
            
            # Check for k3s
            for node in nodes.items:
                labels = node.metadata.labels or {}
                if 'k3s.io/hostname' in labels or 'node.kubernetes.io/instance-type' in labels and 'k3s' in labels.get('node.kubernetes.io/instance-type', ''):
                    logger.info("platform_detected", platform="k3s")
                    return {
                        'type': 'k3s',
                        'name': 'k3s - Lightweight Kubernetes',
                        'is_arc': False
                    }
            
            # Default to vanilla Kubernetes
            logger.info("platform_detected", platform="Kubernetes")
            return {
                'type': 'kubernetes',
                'name': 'Kubernetes',
                'is_arc': False
            }
            
        except Exception as e:
            logger.error("platform_detection_error", error=str(e))
            return {
                'type': 'kubernetes',
                'name': 'Kubernetes',
                'is_arc': False
            }
    
    async def get_platform_info(self) -> dict:
        """Get detected platform information.
        
        Returns:
            dict: Platform information
        """
        if not self._platform_info:
            self._platform_info = await self._detect_platform()
        return self._platform_info
        logger.info("kubernetes_disconnected")
