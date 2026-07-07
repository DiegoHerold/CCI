from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class RequestContext:
    ip_address: str | None
    user_agent: str | None


def context_from_request(request: Request) -> RequestContext:
    forwarded_ip = request.headers.get("X-Client-IP")
    direct_ip = request.client.host if request.client else None
    return RequestContext(
        ip_address=(forwarded_ip or direct_ip or "unknown")[:64],
        user_agent=(request.headers.get("User-Agent") or "unknown")[:512],
    )
