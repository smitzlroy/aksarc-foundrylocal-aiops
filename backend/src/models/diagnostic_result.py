"""Diagnostic result models for AKS Arc troubleshooting."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DiagnosticStatus(str, Enum):
    """Status of a diagnostic check."""
    
    PASS = "pass"
    WARN = "warning"
    FAIL = "fail"
    ERROR = "error"
    UNKNOWN = "unknown"


class DiagnosticSeverity(str, Enum):
    """Severity level for diagnostic findings."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RemediationAction(BaseModel):
    """Suggested action to remediate an issue."""
    
    type: str = Field(..., description="Type of action: kubectl, az-cli, manual")
    command: Optional[str] = Field(None, description="Command to execute")
    description: str = Field(..., description="Human-readable description")
    documentation_url: Optional[str] = None


class DiagnosticCheck(BaseModel):
    """Individual diagnostic check result."""
    
    name: str
    category: str = Field(..., description="control-plane, networking, authentication, etc.")
    status: DiagnosticStatus
    severity: DiagnosticSeverity = DiagnosticSeverity.INFO
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    remediation_actions: list[RemediationAction] = Field(default_factory=list)


class DiagnosticReport(BaseModel):
    """Complete diagnostic report for cluster health."""
    
    cluster_name: str
    platform: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: list[DiagnosticCheck] = Field(default_factory=list)
    summary: dict[str, int] = Field(
        default_factory=lambda: {
            "total": 0,
            "passed": 0,
            "warnings": 0,
            "failed": 0,
            "errors": 0
        }
    )
    overall_health: DiagnosticStatus = DiagnosticStatus.UNKNOWN
    
    def add_check(self, check: DiagnosticCheck) -> None:
        """Add a diagnostic check and update summary."""
        self.checks.append(check)
        self.summary["total"] += 1
        
        if check.status == DiagnosticStatus.PASS:
            self.summary["passed"] += 1
        elif check.status == DiagnosticStatus.WARN:
            self.summary["warnings"] += 1
        elif check.status == DiagnosticStatus.FAIL:
            self.summary["failed"] += 1
        elif check.status == DiagnosticStatus.ERROR:
            self.summary["errors"] += 1
        
        # Update overall health (worst status wins)
        if self.overall_health == DiagnosticStatus.UNKNOWN:
            self.overall_health = check.status
        elif check.status == DiagnosticStatus.FAIL or check.status == DiagnosticStatus.ERROR:
            self.overall_health = DiagnosticStatus.FAIL
        elif check.status == DiagnosticStatus.WARN and self.overall_health == DiagnosticStatus.PASS:
            self.overall_health = DiagnosticStatus.WARN


class SupportBundleMetadata(BaseModel):
    """Metadata for support bundle generation."""
    
    cluster_name: str
    platform: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = "AKS Arc AI Ops Assistant"
    version: str = "0.1.0"
    namespaces_included: list[str] = Field(default_factory=list)
    time_range_hours: int = 24


class SupportBundle(BaseModel):
    """Support bundle for Microsoft support cases."""
    
    metadata: SupportBundleMetadata
    diagnostic_report: DiagnosticReport
    problem_statement: str = Field(..., description="AI-generated summary of the issue")
    logs: dict[str, str] = Field(default_factory=dict, description="Component name -> log content")
    manifests: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Resource type -> manifests")
    bundle_path: Optional[str] = Field(None, description="Path to generated ZIP file")
