"""
Reasoning Loop: Observe → Reason → Act

Orchestrates the AI-driven diagnostic cycle for AKS Arc clusters.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional

import structlog
from pydantic import BaseModel

from src.models.diagnostic_result import DiagnosticReport, DiagnosticCheck, DiagnosticStatus
from src.models.topology_graph import TopologyGraph

logger = structlog.get_logger(__name__)


class LoopPhase(str, Enum):
    """Phases of the reasoning loop."""
    OBSERVE = "observe"
    REASON = "reason"
    ACT = "act"
    IDLE = "idle"


class Observation(BaseModel):
    """Structured observation from cluster monitoring."""
    timestamp: datetime
    topology: TopologyGraph
    metrics: dict
    events: list[dict]
    logs: Optional[dict] = None


class Reasoning(BaseModel):
    """AI-driven analysis of observations."""
    timestamp: datetime
    anomalies: list[str]
    root_causes: list[str]
    confidence: float
    reasoning_chain: list[str]  # Step-by-step thought process
    diagnostic_report: DiagnosticReport


class ActionPlan(BaseModel):
    """Recommended remediation actions."""
    timestamp: datetime
    priority: int  # 1=critical, 2=high, 3=medium, 4=low
    actions: list[dict]  # {"type": "kubectl", "command": "..."}
    expected_outcome: str
    rollback_plan: Optional[str] = None


class ReasoningLoop:
    """
    Continuous reasoning loop for AKS Arc cluster health.
    
    Cycle:
    1. OBSERVE: Collect topology, metrics, events, logs
    2. REASON: Analyze using diagnostic checks + AI reasoning
    3. ACT: Generate remediation commands or support bundles
    """
    
    def __init__(
        self,
        topology_builder,
        diagnostic_runner,
        action_generator,
        interval_seconds: int = 60
    ):
        """Initialize reasoning loop.
        
        Args:
            topology_builder: TopologyGraphBuilder instance
            diagnostic_runner: DiagnosticRunner instance
            action_generator: ActionGenerator instance
            interval_seconds: Loop cycle interval
        """
        self.topology_builder = topology_builder
        self.diagnostic_runner = diagnostic_runner
        self.action_generator = action_generator
        self.interval = interval_seconds
        
        self.phase = LoopPhase.IDLE
        self.last_observation: Optional[Observation] = None
        self.last_reasoning: Optional[Reasoning] = None
        self.last_action_plan: Optional[ActionPlan] = None
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the reasoning loop."""
        if self._running:
            logger.warning("reasoning_loop_already_running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("reasoning_loop_started", interval=self.interval)
    
    async def stop(self):
        """Stop the reasoning loop."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("reasoning_loop_stopped")
    
    async def _loop(self):
        """Main reasoning loop."""
        while self._running:
            try:
                cycle_start = datetime.utcnow()
                
                # Phase 1: OBSERVE
                observation = await self._observe()
                self.last_observation = observation
                
                # Phase 2: REASON
                reasoning = await self._reason(observation)
                self.last_reasoning = reasoning
                
                # Phase 3: ACT
                if reasoning.diagnostic_report.overall_health != DiagnosticStatus.PASS:
                    action_plan = await self._act(reasoning)
                    self.last_action_plan = action_plan
                else:
                    logger.info("cluster_healthy_no_action_needed")
                    self.last_action_plan = None
                
                # Wait for next cycle
                cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                wait_time = max(0, self.interval - cycle_duration)
                
                logger.info(
                    "reasoning_cycle_complete",
                    duration_seconds=cycle_duration,
                    next_cycle_in=wait_time,
                    overall_health=reasoning.diagnostic_report.overall_health
                )
                
                await asyncio.sleep(wait_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("reasoning_loop_error", error=str(e), exc_info=True)
                await asyncio.sleep(self.interval)
    
    async def _observe(self) -> Observation:
        """Phase 1: Collect observations from cluster."""
        self.phase = LoopPhase.OBSERVE
        logger.info("observe_phase_started")
        
        try:
            # Build topology graph
            topology = await self.topology_builder.build_topology()
            
            # Collect metrics (placeholder - would integrate with Prometheus/Azure Monitor)
            metrics = {
                "node_cpu_usage": [],
                "node_memory_usage": [],
                "pod_restart_count": [],
                "network_errors": []
            }
            
            # Collect events (placeholder - would query K8s events)
            events = []
            
            observation = Observation(
                timestamp=datetime.utcnow(),
                topology=topology,
                metrics=metrics,
                events=events
            )
            
            logger.info(
                "observe_phase_complete",
                pods=len(topology.pods),
                services=len(topology.services),
                flows=len(topology.communication_flows)
            )
            
            return observation
            
        except Exception as e:
            logger.error("observe_phase_failed", error=str(e))
            raise
    
    async def _reason(self, observation: Observation) -> Reasoning:
        """Phase 2: Analyze observations and generate insights."""
        self.phase = LoopPhase.REASON
        logger.info("reason_phase_started")
        
        try:
            # Run diagnostic checks
            diagnostic_report = await self.diagnostic_runner.run_all_checks(observation.topology)
            
            # Extract anomalies from failed checks
            anomalies = [
                f"{check.name}: {check.message}"
                for check in diagnostic_report.checks
                if check.status == DiagnosticStatus.FAIL
            ]
            
            # Identify root causes (simple heuristics - would use AI/ML in production)
            root_causes = []
            reasoning_chain = []
            
            for check in diagnostic_report.checks:
                if check.status == DiagnosticStatus.FAIL:
                    root_causes.append(check.name)
                    reasoning_chain.append(
                        f"Detected issue: {check.name} - {check.message}"
                    )
                    if check.remediation:
                        reasoning_chain.append(
                            f"Recommended action: {check.remediation.description}"
                        )
            
            # Calculate confidence based on check results
            total_checks = len(diagnostic_report.checks)
            failed_checks = diagnostic_report.summary.get("fail", 0)
            confidence = 1.0 - (failed_checks / total_checks) if total_checks > 0 else 1.0
            
            reasoning = Reasoning(
                timestamp=datetime.utcnow(),
                anomalies=anomalies,
                root_causes=root_causes,
                confidence=confidence,
                reasoning_chain=reasoning_chain,
                diagnostic_report=diagnostic_report
            )
            
            logger.info(
                "reason_phase_complete",
                anomalies_count=len(anomalies),
                confidence=confidence,
                overall_health=diagnostic_report.overall_health
            )
            
            return reasoning
            
        except Exception as e:
            logger.error("reason_phase_failed", error=str(e))
            raise
    
    async def _act(self, reasoning: Reasoning) -> ActionPlan:
        """Phase 3: Generate remediation action plan."""
        self.phase = LoopPhase.ACT
        logger.info("act_phase_started")
        
        try:
            # Determine priority based on severity
            critical_count = sum(
                1 for check in reasoning.diagnostic_report.checks
                if check.severity == "critical" and check.status == DiagnosticStatus.FAIL
            )
            priority = 1 if critical_count > 0 else 2
            
            # Generate actions from remediation steps
            actions = []
            for check in reasoning.diagnostic_report.checks:
                if check.status == DiagnosticStatus.FAIL and check.remediation:
                    for cmd in check.remediation.kubectl_commands:
                        actions.append({
                            "type": "kubectl",
                            "command": cmd,
                            "reason": check.name
                        })
                    for cmd in check.remediation.az_commands:
                        actions.append({
                            "type": "az",
                            "command": cmd,
                            "reason": check.name
                        })
            
            # Generate expected outcome
            expected_outcome = (
                f"Resolve {len(reasoning.root_causes)} identified issues: " +
                ", ".join(reasoning.root_causes[:3])
            )
            
            action_plan = ActionPlan(
                timestamp=datetime.utcnow(),
                priority=priority,
                actions=actions,
                expected_outcome=expected_outcome,
                rollback_plan="Monitor cluster health for 5 minutes after applying changes"
            )
            
            logger.info(
                "act_phase_complete",
                priority=priority,
                actions_count=len(actions)
            )
            
            return action_plan
            
        except Exception as e:
            logger.error("act_phase_failed", error=str(e))
            raise
    
    def get_status(self) -> dict:
        """Get current loop status."""
        return {
            "running": self._running,
            "phase": self.phase,
            "last_observation": self.last_observation.timestamp.isoformat() if self.last_observation else None,
            "last_reasoning": {
                "timestamp": self.last_reasoning.timestamp.isoformat(),
                "overall_health": self.last_reasoning.diagnostic_report.overall_health,
                "anomalies_count": len(self.last_reasoning.anomalies),
                "confidence": self.last_reasoning.confidence
            } if self.last_reasoning else None,
            "last_action_plan": {
                "timestamp": self.last_action_plan.timestamp.isoformat(),
                "priority": self.last_action_plan.priority,
                "actions_count": len(self.last_action_plan.actions)
            } if self.last_action_plan else None
        }
