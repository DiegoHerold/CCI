from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class RequestContext:
    correlation_id: str
    ip_address: str | None
    user_agent: str | None


def context_from_request(request: Request) -> RequestContext:
    forwarded = request.headers.get("X-Client-IP")
    client_ip = request.client.host if request.client else None
    return RequestContext(
        correlation_id=getattr(request.state, "correlation_id", "system"),
        ip_address=forwarded or client_ip,
        user_agent=request.headers.get("User-Agent"),
    )

