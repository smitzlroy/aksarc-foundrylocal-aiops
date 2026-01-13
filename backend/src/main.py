"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import configure_logging, get_logger

# Configure logging
configure_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        foundry_endpoint=settings.foundry_endpoint,
    )

    # TODO: Initialize services here
    # - Kubernetes watcher
    # - Context buffer
    # - Foundry client

    yield

    # Shutdown
    logger.info("application_shutting_down")

    # TODO: Cleanup services here
    # - Stop Kubernetes watcher
    # - Close Foundry client
    # - Clear context buffer


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


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    logger.debug("health_check_requested")

    # TODO: Add checks for:
    # - Kubernetes connection
    # - Foundry Local connection
    # - Context buffer status

    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.get("/api/info")
async def get_info() -> dict[str, str | bool]:
    """Get application information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "foundry_endpoint": settings.foundry_endpoint,
        "foundry_model": settings.foundry_model,
        "kubernetes_configured": settings.kubeconfig is not None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
