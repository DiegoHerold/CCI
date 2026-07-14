from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class WorkflowStartResult:
    workflow_id: str
    workflow_run_id: str | None = None


class TemporalClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def start_extraction_workflow(self, payload: dict) -> WorkflowStartResult:
        workflow_id = f"extraction-document-{payload['document_id']}-job-{payload['extraction_job_id']}"
        return WorkflowStartResult(workflow_id=workflow_id)

    async def cancel_workflow(self, workflow_id: str) -> None:
        return None
