from pathlib import PurePosixPath
import re
from uuid import uuid4

from app.domain.enums import EXTENSION_FORMATS, FileFormat
from app.errors import BusinessRuleError


_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    raw = filename.replace("\\", "/").split("/")[-1].strip()
    if not raw:
        raise BusinessRuleError("INVALID_FILENAME", "Filename is required")
    if raw.startswith("."):
        raise BusinessRuleError("UNSUPPORTED_FILE_TYPE", "Hidden files are not supported")
    candidate = _SAFE_CHARS.sub("_", raw).strip("._")
    if not candidate:
        raise BusinessRuleError("INVALID_FILENAME", "Filename is required")
    return candidate[:180]


def validate_archive_member_path(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise BusinessRuleError("UNSAFE_ZIP_ENTRY", "ZIP entry path is unsafe")
    if any(part.startswith(".") for part in path.parts if part):
        raise BusinessRuleError("UNSUPPORTED_FILE_TYPE", "Hidden ZIP entries are not supported")
    return sanitize_filename(path.name)


def extension_for(filename: str) -> str:
    safe = sanitize_filename(filename)
    if "." not in safe:
        raise BusinessRuleError("UNSUPPORTED_FILE_TYPE", "File extension is required")
    return "." + safe.rsplit(".", 1)[-1].lower()


def format_for_extension(extension: str) -> FileFormat:
    try:
        return EXTENSION_FORMATS[extension.lower()]
    except KeyError as exc:
        raise BusinessRuleError(
            "UNSUPPORTED_FILE_TYPE",
            f"Unsupported file type: {extension}",
        ) from exc


def make_stored_filename(original_filename: str, document_id: str | None = None) -> str:
    safe = sanitize_filename(original_filename)
    extension = extension_for(safe)
    return f"{document_id or uuid4()}{extension}"


def storage_key(
    client_id: str, competence_id: str, document_id: str, stored_filename: str
) -> str:
    return (
        f"clients/{client_id}/competences/{competence_id}/"
        f"documents/{document_id}/{stored_filename}"
    )
