from fastapi import Depends, FastAPI, HTTPException

from app.config import Settings, get_settings
from app.extractor import WORKER_VERSION, extract_pdf
from app.schemas import ExtractRequest, ExtractResponse
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
        title="CCI PDF Extractor Worker",
        version=WORKER_VERSION,
        description="Internal worker API for template-based PDF extraction.",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "pdf-extractor-worker"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready", "service": "pdf-extractor-worker"}

    @app.post("/extract", response_model=ExtractResponse)
    async def extract(
        request: ExtractRequest,
        settings: Settings = Depends(get_settings),
        storage: S3Storage = Depends(get_storage),
    ) -> ExtractResponse:
        payload = request.model_dump()
        if not (payload.get("preview", {}).get("preview_json") or payload.get("preview", {}).get("preview")):
            preview_ref = payload.get("preview", {})
            bucket = preview_ref.get("storage_bucket")
            key = preview_ref.get("storage_key")
            if not bucket or not key:
                raise HTTPException(status_code=422, detail="preview_missing")
            try:
                payload["preview"]["preview_json"] = storage.load_json(
                    bucket=bucket,
                    key=key,
                    max_size_bytes=settings.extractor_max_preview_size_bytes,
                )
            except Exception as exc:
                raise HTTPException(status_code=503, detail="preview_load_failed") from exc
        return ExtractResponse.model_validate(extract_pdf(payload))

    return app


app = create_app()
