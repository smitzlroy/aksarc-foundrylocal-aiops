"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.api.routes import initialize_services, router
from src.api.v1.topology import router as topology_router, set_topology_builder
from src.api.v1.diagnostics import router as diagnostics_router, set_diagnostic_services
from src.api.v1.reasoning import router as reasoning_router, set_reasoning_loop
from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.services.context import ContextBuffer
from src.services.foundry import FoundryClient
from src.services.kubernetes import KubernetesClient
from src.services.ai_detector import detect_ai_endpoint
from src.reasoning.topology_analyzer import TopologyGraphBuilder
from src.diagnostics.runner import DiagnosticRunner
from src.reasoning.loop import ReasoningLoop
from src.exporters.support_bundle import SupportBundleGenerator

# Configure logging
configure_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
)

logger = get_logger(__name__)

# Global service instances
k8s_client: KubernetesClient | None = None
context_buffer: ContextBuffer | None = None
foundry_client: FoundryClient | None = None
watcher_task: asyncio.Task | None = None
topology_builder: TopologyGraphBuilder | None = None
diagnostic_runner: DiagnosticRunner | None = None
reasoning_loop: ReasoningLoop | None = None
support_bundle_generator: SupportBundleGenerator | None = None


async def cluster_watcher() -> None:
    """Background task to watch cluster and update context buffer."""
    global k8s_client, context_buffer
    
    if not k8s_client or not context_buffer:
        logger.error("cluster_watcher_services_not_initialized")
        return
    
    logger.info("cluster_watcher_started")
    
    try:
        while True:
            try:
                # Get cluster status and add to buffer
                status = await k8s_client.get_cluster_status()
                context_buffer.add(status)
                
                # Wait before next poll (30 seconds)
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.info("cluster_watcher_cancelled")
                raise  # Re-raise to properly handle cancellation
            except Exception as e:
                logger.error("cluster_watcher_error", error=str(e), exc_info=True)
                # Wait before retrying
                await asyncio.sleep(5)
                
    except asyncio.CancelledError:
        logger.info("cluster_watcher_cancelled_outer")
        pass
    finally:
        logger.info("cluster_watcher_stopped")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    global k8s_client, context_buffer, foundry_client, watcher_task
    global topology_builder, diagnostic_runner, reasoning_loop, support_bundle_generator
    
    # Startup
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        foundry_endpoint=settings.foundry_endpoint,
    )

    try:
        # Auto-detect AI endpoint (Foundry Local, Ollama, etc.)
        logger.info("detecting_ai_endpoint")
        ai_config = await detect_ai_endpoint()
        
        if ai_config:
            logger.info(
                "ai_endpoint_detected",
                service=ai_config["service"],
                endpoint=ai_config["endpoint"],
                models_count=len(ai_config.get("models", [])),
                default_model=ai_config.get("default_model", "unknown")
            )
            foundry_endpoint = ai_config["endpoint"]
            foundry_model = ai_config.get("default_model", settings.foundry_model)
        else:
            logger.warning("no_ai_endpoint_detected_using_config")
            foundry_endpoint = settings.foundry_endpoint
            foundry_model = settings.foundry_model
        
        # Initialize Kubernetes client (optional - continue if unavailable)
        k8s_client = KubernetesClient()
        try:
            await k8s_client.connect()
            logger.info("kubernetes_client_initialized")
        except Exception as e:
            logger.warning(
                "kubernetes_unavailable_continuing_without_cluster",
                error=str(e)
            )
            k8s_client = None  # Continue without k8s
        
        # Initialize context buffer
        context_buffer = ContextBuffer(
            retention_hours=settings.context_buffer_hours,
            max_snapshots=1000,
        )
        logger.info("context_buffer_initialized")
        
        # Initialize Foundry client
        foundry_client = FoundryClient(
            endpoint=foundry_endpoint,
            model=foundry_model,
        )
        logger.info("foundry_client_initialized", endpoint=foundry_endpoint, model=foundry_model)
        
        # Initialize API routes with services
        initialize_services(k8s_client, context_buffer, foundry_client)
        
        # Initialize new graph-based services (only if k8s available)
        if k8s_client:
            topology_builder = TopologyGraphBuilder(k8s_client)
            diagnostic_runner = DiagnosticRunner(k8s_client)
            support_bundle_generator = SupportBundleGenerator(
                k8s_client,
                topology_builder,
                diagnostic_runner
            )
            logger.info("graph_services_initialized")
            
            # Initialize reasoning loop (but don't start it automatically)
            reasoning_loop = ReasoningLoop(
                topology_builder=topology_builder,
                diagnostic_runner=diagnostic_runner,
                action_generator=None,  # Placeholder for future action generator
                interval_seconds=60
            )
            logger.info("reasoning_loop_initialized")
            
            # Inject dependencies into API routers
            set_topology_builder(topology_builder)
            set_diagnostic_services(diagnostic_runner, support_bundle_generator, topology_builder)
            set_reasoning_loop(reasoning_loop)
            logger.info("api_dependencies_injected")
            
            # Start background cluster watcher
            watcher_task = asyncio.create_task(cluster_watcher())
            logger.info("cluster_watcher_task_created")
        else:
            logger.warning("kubernetes_services_disabled_cluster_unavailable")
        
    except Exception as e:
        logger.error("initialization_error", error=str(e), exc_info=True)
        raise

    logger.info("lifespan_yielding_control")
    yield
    logger.info("lifespan_after_yield_shutting_down")

    # Shutdown
    logger.info("application_shutting_down")

    # Stop reasoning loop
    if reasoning_loop:
        await reasoning_loop.stop()
    
    # Cancel watcher task
    if watcher_task:
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass
    
    # Disconnect Kubernetes client
    if k8s_client:
        await k8s_client.disconnect()
    
    # Clear context buffer
    if context_buffer:
        context_buffer.clear()
    
    logger.info("application_shutdown_complete")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Operations Assistant for Azure AKS Arc clusters",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)
app.include_router(topology_router)
app.include_router(diagnostics_router)
app.include_router(reasoning_router)


@app.get("/")
async def root():
    """Serve the UI."""
    # Get path to index.html (go up from backend/src to workspace root)
    html_path = Path(__file__).parent.parent.parent / "index.html"
    return FileResponse(
        html_path,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/modern-theme.css")
async def serve_css():
    """Serve the CSS file."""
    css_path = Path(__file__).parent.parent.parent / "modern-theme.css"
    return FileResponse(
        css_path,
        media_type="text/css",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
