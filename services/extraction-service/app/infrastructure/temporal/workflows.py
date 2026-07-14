class ExtractionWorkflow:
    """Prepared Temporal workflow marker for Fase 13.

    Real Temporal activities will be wired when extractor workers are implemented.
    """


class ExtractionActivities:
    """Activity names reserved for extraction orchestration."""

    LOAD_DOCUMENT_METADATA = "load_document_metadata_activity"
    LOAD_DOCUMENT_PREVIEW = "load_document_preview_activity"
    LOAD_TEMPLATE_VERSION = "load_template_version_activity"
    VALIDATE_EXTRACTION_INPUTS = "validate_extraction_inputs_activity"
    CHOOSE_WORKER = "choose_worker_activity"
    DISPATCH_WORKER = "dispatch_worker_activity"
    SAVE_ARTIFACT = "save_artifact_activity"
    MARK_JOB_COMPLETED = "mark_job_completed_activity"
    MARK_JOB_FAILED = "mark_job_failed_activity"
    PUBLISH_EXTRACTION_EVENT = "publish_extraction_event_activity"
