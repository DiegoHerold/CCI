from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MatchCandidateView:
    template_id: str
    template_version_id: str | None
    category_id: str | None
    score: float
    rank_position: int
    matched_signals: list[str] = field(default_factory=list)
    missing_required_signals: list[str] = field(default_factory=list)
    negative_matches: list[str] = field(default_factory=list)
    score_details: dict[str, Any] = field(default_factory=dict)
