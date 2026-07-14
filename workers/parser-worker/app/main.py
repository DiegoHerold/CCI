from fastapi import Depends, FastAPI, HTTPException

from app.config import Settings, get_settings
from app.parsers import PARSER_VERSION, parse_document, serialize_preview
from app.schemas import ParseRequest, ParseResult
from app.storage import S3Storage


def get_storage(settings: Settings = Depends(get_settings)) -> S3Storage:
    return S3Storage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="CCI Parser Worker",
        version=PARSER_VERSION,
        description="Internal worker control API for structured document previews.",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "parser-worker"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready", "service": "parser-worker"}

    @app.post("/parse", response_model=ParseResult)
    async def parse(
        request: ParseRequest,
        storage: S3Storage = Depends(get_storage),
    ) -> ParseResult:
        try:
            content = storage.download_bytes(bucket=request.storage_bucket, key=request.storage_key)
            if len(content) > request.max_file_size_bytes:
                raise ValueError("File exceeds parser size limit")
            preview = parse_document(
                document_id=request.document_id,
                original_filename=request.original_filename,
                file_format=request.file_format,
                content=content,
            )
            preview_bytes = serialize_preview(preview, request.max_preview_json_size_bytes)
            summary = preview.get("summary", {})
            storage.upload_bytes(
                bucket=request.preview_bucket,
                key=request.preview_storage_key,
                content=preview_bytes,
                content_type="application/json",
                metadata={
                    "document_id": request.document_id,
                    "client_id": request.client_id,
                    "competence_id": request.competence_id,
                    "parser_version": PARSER_VERSION,
                },
            )
            return ParseResult(
                document_id=request.document_id,
                file_format=str(preview.get("file_format", request.file_format)),
                parser_version=PARSER_VERSION,
                storage_bucket=request.preview_bucket,
                storage_key=request.preview_storage_key,
                page_count=int(summary.get("page_count", 0)),
                sheet_count=int(summary.get("sheet_count", 0)),
                text_block_count=int(summary.get("text_block_count", 0)),
                table_count=int(summary.get("table_count", 0)),
                requires_ocr=bool(preview.get("requires_ocr", False)),
                metadata={"ocr_reason": preview.get("ocr_reason")},
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Parser worker storage failure") from exc

    return app


app = create_app()
