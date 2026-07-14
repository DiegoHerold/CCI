from dataclasses import dataclass


@dataclass(frozen=True)
class MatchDocumentCommand:
    document_id: str
    force_reprocess: bool = False
    category_hint: str | None = None
    max_candidates: int | None = None


@dataclass(frozen=True)
class ConfirmTemplateMatchCommand:
    document_id: str
    template_id: str
    template_version_id: str
    reason: str
