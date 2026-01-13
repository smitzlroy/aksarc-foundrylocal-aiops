"""Placeholder for WebSocket handlers."""

from fastapi import APIRouter, WebSocket

router = APIRouter(tags=["websocket"])

# TODO: Implement WebSocket endpoint
# - /ws/chat - Streaming chat interface


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming chat.

    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()

    # TODO: Implement chat streaming
    # 1. Receive user message
    # 2. Retrieve context from buffer
    # 3. Query Foundry Local
    # 4. Stream response back to client

    await websocket.close()
