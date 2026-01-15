"""API v1 router initialization."""

from src.api.v1.topology import router as topology_router
from src.api.v1.diagnostics import router as diagnostics_router
from src.api.v1.reasoning import router as reasoning_router

__all__ = ["topology_router", "diagnostics_router", "reasoning_router"]
