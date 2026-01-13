"""Data models for chat interactions."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Chat message role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Chat message."""

    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ChatRequest(BaseModel):
    """Chat query request."""

    message: str = Field(..., description="User's question", min_length=1)
    include_context: bool = Field(
        default=True, description="Include cluster context in query"
    )
    temperature: float = Field(
        default=0.7, description="Model temperature", ge=0.0, le=1.0
    )
    max_tokens: int = Field(
        default=2048, description="Maximum response tokens", ge=1, le=4096
    )


class ChatResponse(BaseModel):
    """Chat query response."""

    response: str = Field(..., description="AI-generated response")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    context_used: bool = Field(..., description="Whether cluster context was used")
    model: str = Field(..., description="Model used for generation")


class StreamToken(BaseModel):
    """Streaming response token."""

    token: str = Field(..., description="Response token")
    done: bool = Field(default=False, description="Whether streaming is complete")
