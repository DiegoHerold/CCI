# Fase 13 - Extraction Service

## Objetivo

Implementar o `services/extraction-service` como dono do ciclo operacional de extracao:

```text
documento + preview + matching/template publicado
-> extraction_job
-> workflow Temporal preparado
-> dispatch para worker por formato
-> status, tentativa, erro e artefato bruto
-> eventos de extracao
```

O servico nao executa extracao pesada. PDF/Excel workers reais entram na Fase 14.

## Responsabilidade de dominio

O `extraction-service` controla jobs, historico de status, tentativas, limite de retry, workflow Temporal preparado, contrato de dispatch, referencias de artefatos brutos e eventos oficiais da extracao.

Ele nao e dono de arquivo original, preview, template, campos, annotations, extraction rules, matching, normalizacao final, revisao visual, regras contabeis, conferencia ou relatorios.

## Rotas internas

```text
POST /extractions/documents/{document_id}
GET /extractions/jobs/{job_id}
GET /extractions/jobs/{job_id}/status
GET /extractions/documents/{document_id}/jobs
GET /extractions/documents/{document_id}/latest
POST /extractions/documents/{document_id}/reprocess
POST /extractions/jobs/{job_id}/retry
POST /extractions/jobs/{job_id}/cancel
```

## Rotas BFF

```text
POST /api/v1/documents/{document_id}/extract
GET /api/v1/documents/{document_id}/extractions
GET /api/v1/documents/{document_id}/extractions/latest
GET /api/v1/extractions/jobs/{job_id}
GET /api/v1/extractions/jobs/{job_id}/status
POST /api/v1/extractions/jobs/{job_id}/retry
POST /api/v1/extractions/jobs/{job_id}/cancel
POST /api/v1/documents/{document_id}/extract/reprocess
```

## Status suportados

```text
pending
queued
starting
running
waiting_worker
worker_running
completed
failed
cancelled
retrying
requires_review
```

## Workflow Temporal preparado

O adapter `TemporalClient` cria `workflow_id` deterministico:

```text
extraction-document-{document_id}-job-{extraction_job_id}
```

Activities reservadas:

```text
load_document_metadata_activity
load_document_preview_activity
load_template_version_activity
validate_extraction_inputs_activity
choose_worker_activity
dispatch_worker_activity
save_artifact_activity
mark_job_completed_activity
mark_job_failed_activity
publish_extraction_event_activity
```

Enquanto os workers reais nao existem, o dispatcher padrao falha claramente com `EXTRACTION_WORKER_UNAVAILABLE`. Fakes sao usados apenas em testes.

## Dispatch de workers

```text
PDF  -> pdf-extractor-worker
XLSX -> excel-extractor-worker
XLS  -> excel-extractor-worker
CSV/TXT/DOCX/XML/IMAGE -> unsupported nesta fase
```

## Banco

Schema:

```text
extraction
```

Tabelas:

```text
extraction.extraction_jobs
extraction.extraction_job_status_history
extraction.extraction_attempts
extraction.extraction_artifacts
```

## Eventos

```text
ExtractionRequested
ExtractionStarted
ExtractionWorkerDispatched
ExtractionCompleted
ExtractionFailed
ExtractionRetryScheduled
ExtractionCancelled
```

## Variaveis principais

```text
EXTRACTION_SERVICE_PORT=8130
EXTRACTION_DATABASE_SCHEMA=extraction
TEMPORAL_ADDRESS=temporal:7233
TEMPORAL_NAMESPACE=default
EXTRACTION_TASK_QUEUE=extraction-task-queue
EXTRACTION_MAX_ATTEMPTS=3
EXTRACTION_RETRY_INITIAL_INTERVAL_SECONDS=5
EXTRACTION_RETRY_BACKOFF_COEFFICIENT=2
EXTRACTION_RETRY_MAX_INTERVAL_SECONDS=60
EXTRACTION_WORKFLOW_TIMEOUT_SECONDS=900
EXTRACTION_ACTIVITY_TIMEOUT_SECONDS=300
MINIO_BUCKET_EXTRACTION_ARTIFACTS=cci-extraction-artifacts
PDF_EXTRACTOR_WORKER_TASK_QUEUE=pdf-extractor-task-queue
EXCEL_EXTRACTOR_WORKER_TASK_QUEUE=excel-extractor-task-queue
```

## Como testar

```bash
make extraction-test
make bff-test
make packages-test
```

## Fora do escopo

- `pdf-extractor-worker` real;
- `excel-extractor-worker` real;
- OCR;
- extracao assistida por IA;
- normalizacao final;
- persistencia final de valores extraidos normalizados;
- UI de revisao;
- Rule Service, Conference Service e Report Service.
