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
    node: str = Field(..., description="Node where pod is running")
    containers: list[str] = Field(default_factory=list, description="Container names")
    ready: int = Field(default=0, description="Number of ready containers")
    total: int = Field(default=0, description="Total number of containers")
    restarts: int = Field(default=0, description="Total container restarts")
    created_at: datetime = Field(..., description="Pod creation timestamp")
    ip: str | None = Field(default=None, description="Pod IP address")
    labels: dict[str, str] = Field(default_factory=dict, description="Pod labels")


class Event(BaseModel):
    """Kubernetes event."""

    timestamp: datetime = Field(..., description="Event timestamp")
    namespace: str = Field(..., description="Event namespace")
    name: str = Field(..., description="Event name")
    type: str = Field(..., description="Event type (Normal, Warning)")
    reason: str = Field(..., description="Event reason")
    message: str = Field(..., description="Event message")
    involved_object: str = Field(..., description="Kind/Name of involved object")


class ClusterStatus(BaseModel):
    """Overall cluster status."""

    timestamp: datetime = Field(..., description="Status snapshot timestamp")
    pods: list[PodStatus] = Field(default_factory=list, description="All pods")
    events: list[Event] = Field(default_factory=list, description="Recent events")
