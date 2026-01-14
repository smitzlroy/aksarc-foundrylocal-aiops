"""Auto-detect local AI endpoints."""

import httpx
import asyncio
import structlog
from typing import Optional, Dict, Any

logger = structlog.get_logger(__name__)


async def _detect_foundry_from_process() -> Optional[Dict[str, Any]]:
    """Detect Foundry Local by checking running processes and output."""
    try:
        import subprocess
        import re
        
        # Run foundry model list to get the endpoint
        result = subprocess.run(
            ["foundry", "model", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            # Look for "Service is Started on http://..." in output
            match = re.search(r'Service is Started on (http://[^,]+)', result.stdout)
            if match:
                endpoint = match.group(1).rstrip('/')
                logger.info("foundry_detected_from_cli", endpoint=endpoint)
                
                # Test the endpoint
                async with httpx.AsyncClient(timeout=3.0) as client:
                    try:
                        response = await client.get(f"{endpoint}/v1/models")
                        if response.status_code == 200:
                            data = response.json()
                            models = []
                            if "data" in data and isinstance(data["data"], list):
                                models = [m.get("id", "") for m in data["data"] if "id" in m]
                            
                            # Get the first available model
                            default_model = models[0] if models else "phi-3.5-mini"
                            
                            return {
                                "endpoint": endpoint,
                                "service": "Azure AI Foundry Local",
                                "models": models,
                                "default_model": default_model,
                                "detected": True
                            }
                    except:
                        pass
    except Exception as e:
        logger.debug("foundry_detection_failed", error=str(e))
    
    return None


async def detect_ai_endpoint() -> Optional[Dict[str, Any]]:
    """Auto-detect running AI service endpoints.
    
    Tests common endpoints for:
    - Azure AI Foundry Local (via CLI detection)
    - Ollama (default port 11434)
    - LM Studio (default port 1234)
    - LocalAI
    
    Returns:
        Dict with endpoint, type, and available models, or None if not found
    """
    # First, try to detect Foundry Local from CLI
    foundry_endpoint = await _detect_foundry_from_process()
    if foundry_endpoint:
        return foundry_endpoint
    
    # Fallback to common AI service configurations
    endpoints_to_test = [
        {"url": "http://localhost:11434", "name": "Ollama", "health": "/api/tags", "models": "/api/tags"},
        {"url": "http://localhost:1234", "name": "LM Studio", "health": "/v1/models", "models": "/v1/models"},
        {"url": "http://localhost:5000", "name": "LocalAI", "health": "/v1/models", "models": "/v1/models"},
        {"url": "http://127.0.0.1:11434", "name": "Ollama", "health": "/api/tags", "models": "/api/tags"},
        {"url": "http://127.0.0.1:1234", "name": "LM Studio", "health": "/v1/models", "models": "/v1/models"},
    ]
    
    async with httpx.AsyncClient(timeout=2.0) as client:
        for config in endpoints_to_test:
            try:
                # Test health endpoint
                response = await client.get(f"{config['url']}{config['health']}")
                
                if response.status_code == 200:
                    logger.info(
                        "ai_endpoint_detected",
                        endpoint=config['url'],
                        service=config['name'],
                        status_code=response.status_code
                    )
                    
                    # Get available models
                    models = []
                    try:
                        models_response = await client.get(f"{config['url']}{config['models']}")
                        if models_response.status_code == 200:
                            data = models_response.json()
                            
                            # Parse based on response format
                            if "models" in data and isinstance(data["models"], list):
                                # Ollama format
                                models = [m.get("name") for m in data["models"] if "name" in m]
                            elif "data" in data and isinstance(data["data"], list):
                                # OpenAI format
                                models = [m.get("id") for m in data["data"] if "id" in m]
                                
                    except Exception as e:
                        logger.warning("failed_to_get_models", error=str(e))
                    
                    return {
                        "endpoint": config['url'],
                        "service": config['name'],
                        "models": models,
                        "detected": True
                    }
                    
            except (httpx.RequestError, httpx.TimeoutException):
                # Endpoint not available, continue testing
                continue
            except Exception as e:
                logger.debug("endpoint_test_error", endpoint=config['url'], error=str(e))
                continue
    
    logger.warning("no_ai_endpoint_detected")
    return None


async def test_endpoint_connection(endpoint: str, model: str = None) -> bool:
    """Test if a specific endpoint is accessible.
    
    Args:
        endpoint: Full URL of the AI endpoint
        model: Optional model name to test
        
    Returns:
        True if accessible, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try common health check paths
            health_paths = ["/v1/models", "/api/tags", "/health", "/"]
            
            for path in health_paths:
                try:
                    response = await client.get(f"{endpoint.rstrip('/')}{path}")
                    if response.status_code in (200, 404):  # 404 means server is up
                        logger.info(
                            "endpoint_connection_test_passed",
                            endpoint=endpoint,
                            path=path,
                            status_code=response.status_code
                        )
                        return True
                except:
                    continue
                    
        return False
        
    except Exception as e:
        logger.error("endpoint_connection_test_failed", endpoint=endpoint, error=str(e))
        return False


if __name__ == "__main__":
    # Test detection
    result = asyncio.run(detect_ai_endpoint())
    if result:
        print(f"\n✅ Detected: {result['service']}")
        print(f"📍 Endpoint: {result['endpoint']}")
        if result['models']:
            print(f"🤖 Available Models: {', '.join(result['models'][:5])}")
            if len(result['models']) > 5:
                print(f"   ... and {len(result['models']) - 5} more")
    else:
        print("\n❌ No AI service detected on common ports")
        print("\n💡 Make sure one of these is running:")
        print("   - Ollama (port 11434)")
        print("   - LM Studio (port 1234)")
        print("   - LocalAI (port 5000)")
        print("   - Azure AI Foundry Local")
