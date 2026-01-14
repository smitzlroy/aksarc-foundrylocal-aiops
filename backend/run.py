"""Run the FastAPI application."""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Suppress all application logs (only show critical errors)
os.environ['LOG_LEVEL'] = 'CRITICAL'

if __name__ == "__main__":
    import uvicorn
    from src.main import app
    from src.core.config import settings
    
    # Run server with minimal output
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="critical",
        access_log=False,
    )
