from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    client_id: str
    competence_id: str
    file_format: str
    original_filename: str
    storage_bucket: str
    storage_key: str
    preview_bucket: str
    preview_storage_key: str
    max_file_size_bytes: int = Field(gt=0)
    max_preview_json_size_bytes: int = Field(gt=0)


class ParseResult(BaseModel):
    document_id: str
    file_format: str
    parser_version: str
    storage_bucket: str
    storage_key: str
    page_count: int = 0
    sheet_count: int = 0
    text_block_count: int = 0
    table_count: int = 0
    requires_ocr: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
