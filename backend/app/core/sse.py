"""
Server-Sent Events helper for streaming progress to frontend.
"""
import json
from typing import AsyncGenerator


async def sse_event(event: str, data: dict) -> str:
    """Format a single SSE message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def sse_stream(steps: list[dict]) -> AsyncGenerator[str, None]:
    """
    Yield pre-built SSE events. Used for simple non-async streams.
    Each step: {"event": "progress", "data": {...}}
    """
    for step in steps:
        yield await sse_event(step["event"], step["data"])
