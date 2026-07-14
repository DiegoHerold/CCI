# Fase 15 - Normalizacao e Resultados da Extracao

## Objetivo

Transformar o output bruto dos extractor workers em resultados persistidos, consultaveis e preparados para revisao.

Fluxo implementado:

```text
worker raw output
-> worker_raw_output artifact
-> normalizacao no extraction-service
-> extraction_results / extracted_field_values / evidences
-> status final do resultado
-> eventos de normalizacao e resultado
```

## Limites de dominio

- `extraction-service` e dono de jobs, artefatos, normalizacao, resultados, evidencias, confianca e status.
- `document-service` continua dono dos arquivos, previews e status do documento.
- `template-service` continua dono de templates, campos e regras tecnicas.
- Workers continuam responsaveis apenas pela extracao bruta.

Nao foi criado `normalization-service`, `result-service`, `evidence-service` ou `audit-service`.

## Modulos internos

Criados no `extraction-service`:

- `modules/normalization`
- `modules/results`
- `modules/evidence`
- `modules/confidence`

## Normalizadores

Implementados:

- `text`
- `number`
- `money`
- `date`
- `month` / `competence`
- `cnpj`
- `cpf`
- `boolean`
- `percentage`
- `account_code`

Preparados por fallback/texto ou metadados para evolucao:

- `currency`
- `account_description`
- `debit_credit_indicator`

## Persistencia

Migration `0002_extraction_results` cria:

- `extraction.extraction_results`
- `extraction.extracted_objects`
- `extraction.extracted_field_values`
- `extraction.extracted_array_items`
- `extraction.extraction_evidences`
- `extraction.normalization_runs`

O `raw_value` e preservado em JSON. O valor normalizado fica em `normalized_value` e tambem em `normalized_json`, com metadados em `metadata_json`.

## Evidencias

Persistidas para PDF:

- `page_number`
- `bbox_json`
- `source_text`
- `rule_id`
- `rule_strategy`
- `confidence`

Persistidas para Excel:

- `sheet_name`
- `cell_range`
- `source_value`
- `rule_id`
- `rule_strategy`
- `confidence`

## Status

Campos:

- `normalized`
- `not_found`
- `normalization_failed`
- `low_confidence`
- `ambiguous`
- `evidence_missing`
- `requires_review`

Resultado:

- `completed`
- `completed_with_warnings`
- `requires_review`
- `failed`

## Endpoints

No `extraction-service`:

- `GET /extractions/jobs/{job_id}/result`
- `GET /extractions/documents/{document_id}/result/latest`
- `GET /extractions/results/{result_id}/fields`
- `GET /extractions/results/{result_id}/fields/{field_value_id}`
- `GET /extractions/results/{result_id}/objects`
- `GET /extractions/results/{result_id}/array-items?field_path=contas[]`
- `GET /extractions/fields/{field_value_id}/evidence`
- `POST /extractions/jobs/{job_id}/normalize/reprocess`

No BFF:

- `GET /api/v1/documents/{document_id}/extraction-result`
- `GET /api/v1/extractions/jobs/{job_id}/result`
- `GET /api/v1/extractions/results/{result_id}/fields`
- `GET /api/v1/extractions/results/{result_id}/objects`
- `GET /api/v1/extractions/results/{result_id}/array-items`
- `GET /api/v1/extractions/fields/{field_value_id}/evidence`
- `POST /api/v1/extractions/jobs/{job_id}/normalize/reprocess`

## Eventos

Adicionados ao catalogo:

- `ExtractionNormalizationStarted`
- `ExtractionNormalizationCompleted`
- `ExtractionNormalizationFailed`
- `ExtractionResultsSaved`
- `ExtractionRequiresReview`

A mensageria real ainda usa publisher abstrato/no-op no ambiente atual.

## Fora do escopo

Nao implementa revisao visual completa, correcao manual, aprovacao/rejeicao final, OCR, IA, Rule Builder, Rule Worker, Conference Service, Report Service, relatorios ou validacoes contabeis.
