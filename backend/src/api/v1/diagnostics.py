"""
API v1: Diagnostics endpoints

Microsoft-aligned health checks and support bundle generation.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pathlib import Path
from typing import Optional

import structlog

from src.models.diagnostic_result import DiagnosticReport, SupportBundle
from src.diagnostics.runner import DiagnosticRunner
from src.exporters.support_bundle import SupportBundleGenerator
from src.reasoning.topology_analyzer import TopologyGraphBuilder

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/diagnostics", tags=["diagnostics"])

# Global instances (will be injected via dependency injection in production)
_diagnostic_runner: Optional[DiagnosticRunner] = None
_support_bundle_generator: Optional[SupportBundleGenerator] = None
_topology_builder: Optional[TopologyGraphBuilder] = None


def set_diagnostic_services(runner: DiagnosticRunner, bundle_gen: SupportBundleGenerator, topo_builder: TopologyGraphBuilder):
    """Inject diagnostic service dependencies."""
    global _diagnostic_runner, _support_bundle_generator, _topology_builder
    _diagnostic_runner = runner
    _support_bundle_generator = bundle_gen
    _topology_builder = topo_builder


@router.get("/health", response_model=DiagnosticReport)
async def run_health_checks():
    """Run comprehensive diagnostic checks.
    
    Executes all Microsoft-aligned health checks:
    - Control plane health
    - Arc agents connectivity
    - Networking configuration
    - Node conditions
    - Pod health
    
    Returns:
        DiagnosticReport with all check results and summary
    """
    if not _diagnostic_runner or not _topology_builder:
        raise HTTPException(status_code=503, detail="Diagnostic services not initialized")
    
    try:
        # Build topology first
        topology = await _topology_builder.build_topology()
        
        # Run diagnostics
        report = await _diagnostic_runner.run_all_checks(topology)
        
        return report
    except Exception as e:
        logger.error("health_check_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/health/category/{category}")
async def run_health_checks_by_category(category: str):
    """Run health checks filtered by category.
    
    Args:
        category: Check category (control_plane, arc, networking, nodes, workloads)
        
    Returns:
        Filtered diagnostic checks
    """
    if not _diagnostic_runner or not _topology_builder:
        raise HTTPException(status_code=503, detail="Diagnostic services not initialized")
    
    try:
        topology = await _topology_builder.build_topology()
        report = await _diagnostic_runner.run_all_checks(topology)
        
        # Filter by category
        filtered_checks = [c for c in report.checks if c.category == category]
        
        if not filtered_checks:
            raise HTTPException(status_code=404, detail=f"No checks found for category: {category}")
        
        return {
            "category": category,
            "checks": filtered_checks,
            "count": len(filtered_checks)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("category_check_failed", category=category, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/failed")
async def get_failed_checks():
    """Get only failed health checks.
    
    Returns:
        List of failed DiagnosticCheck objects with remediation actions
    """
    if not _diagnostic_runner or not _topology_builder:
        raise HTTPException(status_code=503, detail="Diagnostic services not initialized")
    
    try:
        topology = await _topology_builder.build_topology()
        report = await _diagnostic_runner.run_all_checks(topology)
        
        failed_checks = [
            c for c in report.checks
            if c.status in ["fail", "error"]
        ]
        
        return {
            "failed_checks": failed_checks,
            "count": len(failed_checks),
            "overall_health": report.overall_health
        }
    except Exception as e:
        logger.error("failed_checks_query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/support-bundle", response_model=SupportBundle)
async def generate_support_bundle(
    problem_statement: str = Query(..., description="Description of the issue"),
    include_logs: bool = True,
    include_events: bool = True,
    include_manifests: bool = True,
    log_tail_lines: int = 1000
):
    """Generate comprehensive support bundle for troubleshooting.
    
    Collects:
    - Current topology graph
    - Diagnostic report
    - Pod logs (configurable)
    - Cluster events
    - Resource manifests
    - Cluster info
    
    Args:
        problem_statement: Description of the issue being investigated
        include_logs: Whether to collect pod logs
        include_events: Whether to collect cluster events
        include_manifests: Whether to collect resource manifests
        log_tail_lines: Number of log lines per pod
        
    Returns:
        SupportBundle with ZIP file data
    """
    if not _support_bundle_generator:
        raise HTTPException(status_code=503, detail="Support bundle service not initialized")
    
    try:
        bundle = await _support_bundle_generator.generate_bundle(
            problem_statement=problem_statement,
            include_logs=include_logs,
            include_events=include_events,
            include_manifests=include_manifests,
            log_tail_lines=log_tail_lines
        )
        
        return bundle
    except Exception as e:
        logger.error("support_bundle_generation_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate support bundle: {str(e)}")


@router.post("/support-bundle/download")
async def download_support_bundle(
    problem_statement: str = Query(..., description="Description of the issue"),
    include_logs: bool = True,
    include_events: bool = True,
    include_manifests: bool = True
):
    """Generate and download support bundle as ZIP file.
    
    Same as /support-bundle but returns the ZIP file directly for download.
    
    Returns:
        ZIP file with all collected data
    """
    if not _support_bundle_generator:
        raise HTTPException(status_code=503, detail="Support bundle service not initialized")
    
    try:
        bundle = await _support_bundle_generator.generate_bundle(
            problem_statement=problem_statement,
            include_logs=include_logs,
            include_events=include_events,
            include_manifests=include_manifests
        )
        
        # Convert hex back to bytes
        zip_bytes = bytes.fromhex(bundle.zip_file_base64)
        
        # Generate filename
        filename = f"support-bundle-{bundle.metadata.cluster_name}-{bundle.metadata.timestamp.strftime('%Y%m%d-%H%M%S')}.zip"
        
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error("support_bundle_download_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/remediation/{check_name}")
async def get_remediation_actions(check_name: str):
    """Get remediation actions for a specific failed check.
    
    Args:
        check_name: Name of the diagnostic check
        
    Returns:
        RemediationAction with kubectl/az-cli commands
    """
    if not _diagnostic_runner or not _topology_builder:
        raise HTTPException(status_code=503, detail="Diagnostic services not initialized")
    
    try:
        topology = await _topology_builder.build_topology()
        report = await _diagnostic_runner.run_all_checks(topology)
        
        # Find matching check
        check = next((c for c in report.checks if c.name == check_name), None)
        
        if not check:
            raise HTTPException(status_code=404, detail=f"Check not found: {check_name}")
        
        if not check.remediation:
            return {
                "check_name": check_name,
                "status": check.status,
                "message": "No remediation actions available (check may have passed)"
            }
        
        return {
            "check_name": check_name,
            "status": check.status,
            "severity": check.severity,
            "remediation": check.remediation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("remediation_query_failed", check_name=check_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
