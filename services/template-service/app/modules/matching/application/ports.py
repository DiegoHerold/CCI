from typing import Protocol

from app.infrastructure.database.models import Template


class TemplateCatalogPort(Protocol):
    def find_matching_candidates(
        self,
        *,
        file_format: str,
        category_hint: str | None,
    ) -> list[Template]:
        raise NotImplementedError
