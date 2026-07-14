from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class RequestContext:
    correlation_id: str
    ip_address: str | None
    user_agent: str | None


def context_from_request(request: Request) -> RequestContext:
    return RequestContext(
        correlation_id=getattr(request.state, "correlation_id", "system"),
        ip_address=request.headers.get("X-Client-IP")
        or (request.client.host if request.client else None),
        user_agent=request.headers.get("User-Agent"),
    )
