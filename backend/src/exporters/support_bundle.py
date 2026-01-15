"""
Support bundle generator for AKS Arc troubleshooting.

Collects logs, manifests, events, and diagnostic reports into a ZIP archive.
"""

import asyncio
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog

from src.models.diagnostic_result import SupportBundle, SupportBundleMetadata
from src.models.topology_graph import TopologyGraph

logger = structlog.get_logger(__name__)


class SupportBundleGenerator:
    """Generate comprehensive support bundles for troubleshooting."""
    
    def __init__(self, k8s_client, topology_builder, diagnostic_runner):
        """Initialize with required services.
        
        Args:
            k8s_client: KubernetesClient instance
            topology_builder: TopologyGraphBuilder instance
            diagnostic_runner: DiagnosticRunner instance
        """
        self.core_v1 = k8s_client.core_v1
        self.apps_v1 = k8s_client.apps_v1
        self.topology_builder = topology_builder
        self.diagnostic_runner = diagnostic_runner
    
    async def generate_bundle(
        self,
        problem_statement: str,
        include_logs: bool = True,
        include_events: bool = True,
        include_manifests: bool = True,
        log_tail_lines: int = 1000
    ) -> SupportBundle:
        """Generate comprehensive support bundle.
        
        Args:
            problem_statement: Description of the issue
            include_logs: Whether to collect pod logs
            include_events: Whether to collect cluster events
            include_manifests: Whether to collect resource manifests
            log_tail_lines: Number of log lines to collect per pod
            
        Returns:
            SupportBundle with ZIP file data
        """
        logger.info(
            "generating_support_bundle",
            problem=problem_statement,
            include_logs=include_logs,
            include_events=include_events
        )
        
        try:
            # Build current topology
            topology = await self.topology_builder.build_topology()
            
            # Run diagnostics
            diagnostic_report = await self.diagnostic_runner.run_all_checks(topology)
            
            # Create ZIP in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add metadata
                metadata = SupportBundleMetadata(
                    cluster_name=topology.metadata.cluster_name,
                    k8s_version=topology.metadata.k8s_version,
                    platform=topology.metadata.platform,
                    problem_statement=problem_statement
                )
                zf.writestr("metadata.json", json.dumps(metadata.dict(), indent=2, default=str))
                
                # Add topology graph
                zf.writestr("topology.json", topology.json(indent=2))
                
                # Add diagnostic report
                zf.writestr("diagnostics.json", diagnostic_report.json(indent=2))
                
                # Collect logs
                if include_logs:
                    await self._collect_logs(zf, topology, log_tail_lines)
                
                # Collect events
                if include_events:
                    await self._collect_events(zf)
                
                # Collect manifests
                if include_manifests:
                    await self._collect_manifests(zf, topology)
                
                # Add cluster info
                await self._collect_cluster_info(zf)
            
            # Get ZIP data
            zip_data = zip_buffer.getvalue()
            
            bundle = SupportBundle(
                metadata=metadata,
                topology=topology,
                diagnostic_report=diagnostic_report,
                logs={},  # Not storing in memory, only in ZIP
                events=[],
                manifests={},
                zip_file_base64=zip_data.hex()  # Convert to hex for transport
            )
            
            logger.info(
                "support_bundle_generated",
                size_bytes=len(zip_data),
                files=len([name for name in zipfile.ZipFile(io.BytesIO(zip_data)).namelist()])
            )
            
            return bundle
            
        except Exception as e:
            logger.error("support_bundle_generation_failed", error=str(e), exc_info=True)
            raise
    
    async def _collect_logs(self, zf: zipfile.ZipFile, topology: TopologyGraph, tail_lines: int):
        """Collect pod logs."""
        logger.info("collecting_logs", pod_count=len(topology.pods))
        
        logs_dir = "logs/"
        
        for pod in topology.pods:
            try:
                # Get logs for each container
                for container in pod.containers:
                    log_data = await asyncio.to_thread(
                        self.core_v1.read_namespaced_pod_log,
                        name=pod.name,
                        namespace=pod.namespace,
                        container=container["name"],
                        tail_lines=tail_lines
                    )
                    
                    filename = f"{logs_dir}{pod.namespace}/{pod.name}/{container['name']}.log"
                    zf.writestr(filename, log_data)
                    
            except Exception as e:
                logger.warning(
                    "pod_log_collection_failed",
                    pod=pod.name,
                    namespace=pod.namespace,
                    error=str(e)
                )
                # Add error marker file
                filename = f"{logs_dir}{pod.namespace}/{pod.name}/ERROR.txt"
                zf.writestr(filename, f"Failed to collect logs: {str(e)}")
        
        logger.info("logs_collected")
    
    async def _collect_events(self, zf: zipfile.ZipFile):
        """Collect cluster events."""
        logger.info("collecting_events")
        
        try:
            events_list = await asyncio.to_thread(
                self.core_v1.list_event_for_all_namespaces
            )
            
            events_data = []
            for event in events_list.items:
                events_data.append({
                    "namespace": event.metadata.namespace,
                    "name": event.metadata.name,
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "first_timestamp": str(event.first_timestamp),
                    "last_timestamp": str(event.last_timestamp),
                    "count": event.count,
                    "involved_object": {
                        "kind": event.involved_object.kind,
                        "name": event.involved_object.name,
                        "namespace": event.involved_object.namespace
                    }
                })
            
            zf.writestr("events.json", json.dumps(events_data, indent=2))
            logger.info("events_collected", count=len(events_data))
            
        except Exception as e:
            logger.error("event_collection_failed", error=str(e))
            zf.writestr("events_ERROR.txt", f"Failed to collect events: {str(e)}")
    
    async def _collect_manifests(self, zf: zipfile.ZipFile, topology: TopologyGraph):
        """Collect resource manifests."""
        logger.info("collecting_manifests")
        
        manifests_dir = "manifests/"
        
        # Collect node manifests
        for node in topology.compute_nodes:
            try:
                node_obj = await asyncio.to_thread(
                    self.core_v1.read_node,
                    name=node.name
                )
                filename = f"{manifests_dir}nodes/{node.name}.yaml"
                zf.writestr(filename, str(node_obj))
            except Exception as e:
                logger.warning("node_manifest_failed", node=node.name, error=str(e))
        
        # Collect pod manifests (sample - first 50)
        for pod in topology.pods[:50]:
            try:
                pod_obj = await asyncio.to_thread(
                    self.core_v1.read_namespaced_pod,
                    name=pod.name,
                    namespace=pod.namespace
                )
                filename = f"{manifests_dir}pods/{pod.namespace}/{pod.name}.yaml"
                zf.writestr(filename, str(pod_obj))
            except Exception as e:
                logger.warning("pod_manifest_failed", pod=pod.name, error=str(e))
        
        # Collect service manifests
        for svc in topology.services:
            try:
                svc_obj = await asyncio.to_thread(
                    self.core_v1.read_namespaced_service,
                    name=svc.name,
                    namespace=svc.namespace
                )
                filename = f"{manifests_dir}services/{svc.namespace}/{svc.name}.yaml"
                zf.writestr(filename, str(svc_obj))
            except Exception as e:
                logger.warning("service_manifest_failed", service=svc.name, error=str(e))
        
        # Collect NetworkPolicy manifests
        for np in topology.network_policies:
            try:
                np_obj = await asyncio.to_thread(
                    self.core_v1.api_client.call_api,
                    f'/apis/networking.k8s.io/v1/namespaces/{np.namespace}/networkpolicies/{np.name}',
                    'GET'
                )
                filename = f"{manifests_dir}networkpolicies/{np.namespace}/{np.name}.yaml"
                zf.writestr(filename, str(np_obj))
            except Exception as e:
                logger.warning("netpol_manifest_failed", netpol=np.name, error=str(e))
        
        logger.info("manifests_collected")
    
    async def _collect_cluster_info(self, zf: zipfile.ZipFile):
        """Collect general cluster information."""
        logger.info("collecting_cluster_info")
        
        cluster_info = {}
        
        try:
            # Get version
            version_info = await asyncio.to_thread(
                self.core_v1.api_client.call_api,
                '/version',
                'GET'
            )
            cluster_info["version"] = version_info[0]
            
            # Get API resources
            api_resources = await asyncio.to_thread(
                self.core_v1.api_client.call_api,
                '/api/v1',
                'GET'
            )
            cluster_info["api_resources"] = str(api_resources[0])
            
            # Get storage classes
            try:
                storage_classes = await asyncio.to_thread(
                    self.core_v1.api_client.call_api,
                    '/apis/storage.k8s.io/v1/storageclasses',
                    'GET'
                )
                cluster_info["storage_classes"] = [
                    sc["metadata"]["name"] for sc in storage_classes[0].get("items", [])
                ]
            except Exception:
                cluster_info["storage_classes"] = "N/A"
            
            zf.writestr("cluster_info.json", json.dumps(cluster_info, indent=2, default=str))
            logger.info("cluster_info_collected")
            
        except Exception as e:
            logger.error("cluster_info_collection_failed", error=str(e))
            zf.writestr("cluster_info_ERROR.txt", f"Failed to collect cluster info: {str(e)}")
    
    async def save_bundle_to_file(self, bundle: SupportBundle, output_dir: Path) -> Path:
        """Save support bundle to local file.
        
        Args:
            bundle: SupportBundle to save
            output_dir: Directory to save bundle
            
        Returns:
            Path to saved ZIP file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = f"support-bundle-{bundle.metadata.cluster_name}-{timestamp}.zip"
        filepath = output_dir / filename
        
        # Write ZIP data
        zip_bytes = bytes.fromhex(bundle.zip_file_base64)
        filepath.write_bytes(zip_bytes)
        
        logger.info("support_bundle_saved", path=str(filepath), size=len(zip_bytes))
        
        return filepath
