"""Run the FastAPI application."""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Import and run
if __name__ == "__main__":
    import uvicorn
    from src.main import app
    from src.core.config import settings
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
