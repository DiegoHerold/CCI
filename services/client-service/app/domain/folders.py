from calendar import monthrange
from datetime import date
import re

from app.errors import BusinessRuleError


ALLOWED_TOKENS = {
    "YYYY",
    "MM",
    "competenceName",
    "previousMonth.MM",
    "previousMonth.YYYY",
}


def validate_folder_pattern(pattern: str) -> str:
    pattern = pattern.strip()
    if not pattern:
        raise ValueError("competence folder pattern cannot be empty")
    if ".." in pattern:
        raise ValueError("path traversal is not allowed")
    if pattern.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", pattern):
        raise ValueError("competence folder pattern must be relative")
    tokens = set(re.findall(r"\{\{([^{}]+)\}\}", pattern))
    if tokens - ALLOWED_TOKENS:
        raise ValueError("unsupported competence folder token")
    if "{{" in re.sub(r"\{\{[^{}]+\}\}", "", pattern):
        raise ValueError("invalid competence folder token")
    return pattern


def resolve_competence_path(
    root: str,
    pattern: str,
    year: int,
    month: int,
) -> str:
    if not root.strip():
        raise BusinessRuleError(
            "CLIENT_FOLDER_NOT_CONFIGURED",
            "A pasta padrão do cliente não está configurada.",
        )
    pattern = validate_folder_pattern(pattern)
    current = date(year, month, 1)
    previous = date(year - 1, 12, 1) if month == 1 else date(year, month - 1, 1)
    competence_name = f"{current.month:02d}-{current.year:04d}"
    values = {
        "YYYY": f"{current.year:04d}",
        "MM": f"{current.month:02d}",
        "competenceName": competence_name,
        "previousMonth.MM": f"{previous.month:02d}",
        "previousMonth.YYYY": f"{previous.year:04d}",
    }
    resolved = pattern
    for token, value in values.items():
        resolved = resolved.replace(f"{{{{{token}}}}}", value)
    separator = "\\" if "\\" in root and not root.startswith("/") else "/"
    relative = re.sub(r"[\\/]", lambda _: separator, resolved).strip("\\/")
    return root.rstrip("\\/") + separator + relative

