import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse


router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


def _sse_event(event_type: str, payload: dict[str, str]) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _placeholder_events(correlation_id: str) -> AsyncIterator[str]:
    events = [
        (
            "connected",
            {
                "type": "connected",
                "message": "SSE connection established.",
                "correlation_id": correlation_id,
            },
        ),
        (
            "heartbeat",
            {
                "type": "heartbeat",
                "message": "BFF placeholder heartbeat.",
                "correlation_id": correlation_id,
            },
        ),
        (
            "placeholder_log",
            {
                "type": "placeholder_log",
                "message": "SSE endpoint is ready. Real log-service integration will be implemented later.",
                "correlation_id": correlation_id,
            },
        ),
    ]
    for event_type, payload in events:
        yield _sse_event(event_type, payload)


@router.get("/stream")
async def stream_logs(request: Request) -> StreamingResponse:
    correlation_id = request.state.correlation_id
    return StreamingResponse(
        _placeholder_events(correlation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
