"""Data models for cluster state."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PodPhase(str, Enum):
    """Kubernetes pod phase."""

    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class PodStatus(BaseModel):
    """Kubernetes pod status information."""

    name: str = Field(..., description="Pod name")
    namespace: str = Field(..., description="Pod namespace")
    phase: PodPhase = Field(..., description="Current phase")
    node_name: str | None = Field(None, description="Node where pod is running")
    restart_count: int = Field(default=0, description="Container restart count")
    created_at: datetime = Field(..., description="Pod creation timestamp")
    conditions: dict[str, Any] = Field(default_factory=dict, description="Pod conditions")


class Event(BaseModel):
    """Kubernetes event."""

    name: str = Field(..., description="Event name")
    namespace: str = Field(..., description="Event namespace")
    type: str = Field(..., description="Event type (Normal, Warning)")
    reason: str = Field(..., description="Event reason")
    message: str = Field(..., description="Event message")
    timestamp: datetime = Field(..., description="Event timestamp")
    involved_object: dict[str, Any] = Field(
        default_factory=dict, description="Object that triggered event"
    )


class ClusterStatus(BaseModel):
    """Overall cluster status."""

    healthy: bool = Field(..., description="Overall health status")
    total_pods: int = Field(..., description="Total number of pods")
    running_pods: int = Field(..., description="Number of running pods")
    failed_pods: int = Field(..., description="Number of failed pods")
    recent_warnings: int = Field(..., description="Recent warning events count")
    last_updated: datetime = Field(..., description="Last update timestamp")
