"""
API v1: Reasoning Loop endpoints

Control and monitor the Observe → Reason → Act cycle.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

import structlog

from src.reasoning.loop import ReasoningLoop

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/reasoning", tags=["reasoning"])

# Global instance
_reasoning_loop: Optional[ReasoningLoop] = None


def set_reasoning_loop(loop: ReasoningLoop):
    """Inject reasoning loop dependency."""
    global _reasoning_loop
    _reasoning_loop = loop


@router.post("/start")
async def start_reasoning_loop():
    """Start the continuous reasoning loop.
    
    Begins the Observe → Reason → Act cycle at configured intervals.
    
    Returns:
        Confirmation message
    """
    if not _reasoning_loop:
        raise HTTPException(status_code=503, detail="Reasoning loop not initialized")
    
    try:
        await _reasoning_loop.start()
        return {
            "status": "started",
            "message": "Reasoning loop is now running",
            "interval_seconds": _reasoning_loop.interval
        }
    except Exception as e:
        logger.error("reasoning_loop_start_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_reasoning_loop():
    """Stop the reasoning loop.
    
    Returns:
        Confirmation message
    """
    if not _reasoning_loop:
        raise HTTPException(status_code=503, detail="Reasoning loop not initialized")
    
    try:
        await _reasoning_loop.stop()
        return {
            "status": "stopped",
            "message": "Reasoning loop has been stopped"
        }
    except Exception as e:
        logger.error("reasoning_loop_stop_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_reasoning_loop_status():
    """Get current status of the reasoning loop.
    
    Returns:
        Current phase, last observation/reasoning/action timestamps, health
    """
    if not _reasoning_loop:
        raise HTTPException(status_code=503, detail="Reasoning loop not initialized")
    
    try:
        status = _reasoning_loop.get_status()
        return status
    except Exception as e:
        logger.error("reasoning_loop_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last-observation")
async def get_last_observation():
    """Get the last observation from the loop.
    
    Returns:
        Observation with topology, metrics, events
    """
    if not _reasoning_loop:
        raise HTTPException(status_code=503, detail="Reasoning loop not initialized")
    
    if not _reasoning_loop.last_observation:
        raise HTTPException(status_code=404, detail="No observations yet")
    
    return _reasoning_loop.last_observation


@router.get("/last-reasoning")
async def get_last_reasoning():
    """Get the last reasoning analysis from the loop.
    
    Returns:
        Reasoning with anomalies, root causes, diagnostic report
    """
    if not _reasoning_loop:
        raise HTTPException(status_code=503, detail="Reasoning loop not initialized")
    
    if not _reasoning_loop.last_reasoning:
        raise HTTPException(status_code=404, detail="No reasoning results yet")
    
    return _reasoning_loop.last_reasoning


@router.get("/last-action-plan")
async def get_last_action_plan():
    """Get the last generated action plan.
    
    Returns:
        ActionPlan with recommended remediation steps
    """
    if not _reasoning_loop:
        raise HTTPException(status_code=503, detail="Reasoning loop not initialized")
    
    if not _reasoning_loop.last_action_plan:
        return {
            "message": "No action plan - cluster is healthy",
            "last_reasoning_health": _reasoning_loop.last_reasoning.diagnostic_report.overall_health if _reasoning_loop.last_reasoning else None
        }
    
    return _reasoning_loop.last_action_plan


@router.get("/reasoning-chain")
async def get_reasoning_chain():
    """Get the step-by-step reasoning chain from last analysis.
    
    Returns:
        List of reasoning steps showing AI's thought process
    """
    if not _reasoning_loop:
        raise HTTPException(status_code=503, detail="Reasoning loop not initialized")
    
    if not _reasoning_loop.last_reasoning:
        raise HTTPException(status_code=404, detail="No reasoning results yet")
    
    return {
        "reasoning_chain": _reasoning_loop.last_reasoning.reasoning_chain,
        "confidence": _reasoning_loop.last_reasoning.confidence,
        "timestamp": _reasoning_loop.last_reasoning.timestamp
    }
