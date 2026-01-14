"""Foundry Local management service using official SDK."""

import asyncio
import structlog
from typing import Optional, Dict, Any, List
from pathlib import Path
from foundry_local import FoundryLocalManager as FoundrySDK
import openai

logger = structlog.get_logger(__name__)


class FoundryManager:
    """Manage Foundry Local using official SDK."""
    
    def __init__(self):
        self._manager: Optional[FoundrySDK] = None
        self._client: Optional[openai.OpenAI] = None
        self.current_model: Optional[str] = None
        self._is_downloading: bool = False
        self._download_progress: float = 0.0
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Foundry Local status using SDK.
        
        Returns:
            Dict with status, model, endpoint, and available models
        """
        try:
            # Check if we have an active manager
            is_running = self._manager is not None
            
            # Get available models from cache
            available_models = await self._get_available_models()
            
            if is_running:
                logger.info("foundry_running", 
                           endpoint=self._manager.endpoint,
                           model=self.current_model, 
                           model_count=len(available_models))
                
                return {
                    "running": True,
                    "installed": True,
                    "endpoint": self._manager.endpoint,
                    "api_key": self._manager.api_key,
                    "model": self.current_model,
                    "available_models": available_models,
                    "message": "Foundry Local is running"
                }
            
            logger.info("foundry_not_running", model_count=len(available_models))
            
            return {
                "running": False,
                "installed": True,
                "available_models": available_models,
                "message": "Foundry Local is not running"
            }
            
        except Exception as e:
            logger.error("status_error", error=str(e), error_type=type(e).__name__)
            return {
                "running": False,
                "installed": False,
                "message": f"Error checking status: {str(e)}"
            }
    
    async def _get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from cache.
        
        Uses foundry CLI to check catalog and cache.
        """
        try:
            import subprocess
            
            # Get model catalog
            result = subprocess.run(
                ["foundry", "model", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0 or not result.stdout:
                return []
            
            # Parse models from output - format is whitespace-separated table
            models = []
            seen_aliases = set()
            current_alias = None
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line or line.startswith('─') or line.startswith('Alias') or line.startswith('---'):
                    continue
                
                # Split by whitespace and get parts
                parts = [p.strip() for p in line.split() if p.strip()]
                if len(parts) < 4:
                    continue
                
                # Check if this line starts with a new alias (non-indented, not GPU/CPU)
                first_part = parts[0]
                if not line.startswith(' ') and first_part.lower() not in ['gpu', 'cpu', 'npu']:
                    # This is a new alias
                    current_alias = first_part
                    
                    # Skip if we've seen this alias
                    if current_alias in seen_aliases:
                        continue
                    
                    seen_aliases.add(current_alias)
                    
                    # Extract size (look for GB pattern)
                    size = "unknown"
                    for i, part in enumerate(parts):
                        if 'GB' in part.upper() or 'MB' in part.upper():
                            # Get size and unit (e.g., "8.37 GB")
                            if i > 0:
                                size = f"{parts[i-1]} {part}"
                            else:
                                size = part
                            break
                    
                    # Check if actually downloaded in cache
                    is_downloaded = await self._check_model_in_cache(current_alias)
                    
                    models.append({
                        "name": current_alias,
                        "variant": "auto",
                        "size": size,
                        "downloaded": is_downloaded
                    })
            
            logger.debug("models_parsed", count=len(models), downloaded_count=sum(1 for m in models if m["downloaded"]))
            return models
            
        except Exception as e:
            logger.error("get_models_error", error=str(e))
            return []
    
    async def _check_model_in_cache(self, model_name: str) -> bool:
        """Check if model exists in local cache.
        
        Args:
            model_name: Model alias to check
            
        Returns:
            True if model is downloaded in cache
        """
        try:
            # Check common cache locations
            cache_dirs = [
                Path.home() / ".foundry" / "cache" / "models" / "Microsoft",
                Path.home() / ".foundry" / "cache" / "models",
                Path.home() / ".foundry" / "models",
            ]
            
            for cache_dir in cache_dirs:
                if not cache_dir.exists():
                    continue
                
                # Check if any directory matches the model name (partial match, case-insensitive)
                model_lower = model_name.lower().replace("-", "").replace(".", "")
                for item in cache_dir.iterdir():
                    if item.is_dir():
                        item_lower = item.name.lower().replace("-", "").replace(".", "")
                        # Match if model name is contained in directory name
                        if model_lower in item_lower or item_lower in model_lower:
                            logger.debug("model_found_in_cache", model=model_name, path=str(item))
                            return True
            
            return False
            
        except Exception as e:
            logger.error("cache_check_error", model=model_name, error=str(e))
            return False
    
    async def start_model(self, model_name: str) -> Dict[str, Any]:
        """Start Foundry Local with specified model using SDK.
        
        This will:
        1. Initialize FoundryLocalManager with the model
        2. Download the model if not cached (SDK handles this)
        3. Load the model into memory
        4. Start the web service
        
        Args:
            model_name: Model alias (e.g., "qwen2.5-0.5b", "phi-4")
            
        Returns:
            Dict with success status and message
        """
        try:
            logger.info("starting_foundry", model=model_name)
            
            # Stop existing manager if running
            if self._manager:
                await self.stop_model()
            
            # Create manager instance with the model
            # This initializes the service and starts downloading if needed
            self._is_downloading = True
            self._download_progress = 0.0
            
            # Run SDK init in thread pool to avoid blocking
            # Add timeout to prevent hanging
            loop = asyncio.get_event_loop()
            try:
                self._manager = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: FoundrySDK(model_name)
                    ),
                    timeout=60.0  # 60 second timeout for model loading
                )
            except asyncio.TimeoutError:
                raise Exception(f"Model loading timed out after 60 seconds. The model may require GPU acceleration that isn't available.")
            
            # SDK automatically:
            # - Checks if model is cached
            # - Downloads if needed (with progress callback)
            # - Starts the Foundry Local service
            # - Loads the model into memory
            
            self.current_model = model_name
            self._is_downloading = False
            self._download_progress = 100.0
            
            # Create OpenAI client configured for local endpoint
            self._client = openai.OpenAI(
                base_url=self._manager.endpoint,
                api_key=self._manager.api_key
            )
            
            logger.info("foundry_started", 
                       model=model_name,
                       endpoint=self._manager.endpoint)
            
            return {
                "success": True,
                "message": f"Foundry Local started with {model_name}",
                "endpoint": self._manager.endpoint,
                "model": model_name
            }
            
        except Exception as e:
            logger.error("start_error", model=model_name, error=str(e), error_type=type(e).__name__)
            self._manager = None
            self._client = None
            self._is_downloading = False
            
            # Parse common error messages for better user feedback
            error_msg = str(e)
            if "NvTensorRT" in error_msg or "GPU" in error_msg or "trtrtx" in error_msg:
                error_msg = f"{model_name} requires GPU acceleration which isn't available. Try qwen2.5-0.5b or qwen2.5-1.5b instead."
            elif "Failed loading model" in error_msg:
                error_msg = f"Failed to load {model_name}. This model may not be compatible with your hardware."
            elif "timeout" in error_msg.lower():
                error_msg = f"{model_name} took too long to start. Try a smaller model like qwen2.5-0.5b."
            
            return {
                "success": False,
                "message": error_msg
            }
    
    async def stop_model(self) -> Dict[str, Any]:
        """Stop Foundry Local and unload model.
        
        Returns:
            Dict with success status and message
        """
        try:
            if not self._manager:
                return {
                    "success": True,
                    "message": "No model running"
                }
            
            logger.info("stopping_foundry", model=self.current_model)
            
            # SDK cleanup would happen here
            # For now, just clear references
            self._manager = None
            self._client = None
            self.current_model = None
            self._is_downloading = False
            self._download_progress = 0.0
            
            logger.info("foundry_stopped")
            
            return {
                "success": True,
                "message": "Foundry Local stopped"
            }
            
        except Exception as e:
            logger.error("stop_error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to stop: {str(e)}"
            }
    
    async def get_download_progress(self, model_name: str) -> Dict[str, Any]:
        """Get download progress for a model.
        
        Args:
            model_name: Model being downloaded
            
        Returns:
            Dict with progress info
        """
        try:
            if self._is_downloading and self.current_model == model_name:
                return {
                    "downloading": True,
                    "progress": self._download_progress,
                    "message": f"Downloading {model_name}... {self._download_progress:.1f}%"
                }
            
            # Check if already downloaded
            is_cached = await self._check_model_in_cache(model_name)
            if is_cached:
                return {
                    "downloading": False,
                    "progress": 100.0,
                    "message": f"{model_name} is already downloaded"
                }
            
            return {
                "downloading": False,
                "progress": 0.0,
                "message": f"{model_name} not started"
            }
            
        except Exception as e:
            logger.error("progress_error", model=model_name, error=str(e))
            return {
                "downloading": False,
                "progress": 0.0,
                "message": f"Error checking progress: {str(e)}"
            }
    
    async def query_model(self, message: str, stream: bool = False, system_prompt: str = None) -> Any:
        """Send query to loaded model using OpenAI SDK.
        
        Args:
            message: User message
            stream: Whether to stream response
            system_prompt: Optional system prompt to set context
            
        Returns:
            Response from model
        """
        if not self._manager or not self._client:
            raise RuntimeError("No model loaded. Call start_model() first.")
        
        try:
            # Get model info from manager
            model_info = await asyncio.get_event_loop().run_in_executor(
                None,
                self._manager.get_model_info,
                self.current_model
            )
            
            # Build messages with system prompt
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            # Use OpenAI SDK to query
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.chat.completions.create(
                    model=model_info.id,
                    messages=messages,
                    stream=stream
                )
            )
            
            if stream:
                # Return generator for streaming
                return response
            else:
                # Return text response
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error("query_error", message=message, error=str(e))
            raise


# Global instance
_foundry_manager: Optional[FoundryManager] = None


def get_foundry_manager() -> FoundryManager:
    """Get global FoundryManager instance."""
    global _foundry_manager
    if _foundry_manager is None:
        _foundry_manager = FoundryManager()
    return _foundry_manager
