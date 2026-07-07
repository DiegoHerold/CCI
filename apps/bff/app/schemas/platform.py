from typing import Literal

from pydantic import BaseModel


class PlatformStatusResponse(BaseModel):
    platform: Literal["cci-platform"] = "cci-platform"
    status: Literal["bootstrapped"] = "bootstrapped"
    phase: Literal["fase-3-bff-inicial"] = "fase-3-bff-inicial"
    services: dict[str, Literal["not_connected"]]
