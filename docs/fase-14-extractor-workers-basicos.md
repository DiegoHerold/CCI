# Fase 14 - Extractor Workers basicos

## Objetivo

Implementar os workers tecnicos que aplicam templates publicados sobre previews estruturados de PDF e Excel para gerar resultado bruto de extracao.

Fluxo desta fase:

```text
Extraction Service
-> Worker PDF ou Excel
-> preview estruturado + template version snapshot + extraction_rules
-> raw_extracted_fields/raw_extracted_objects com evidencias
-> Extraction Service salva artifact e publica eventos oficiais
```

## Limites de dominio

- `document-service` continua dono dos arquivos originais e previews.
- `template-service` continua dono de templates, campos, anotacoes, matching e regras tecnicas.
- `extraction-service` continua dono de jobs, status, attempts, artifacts e eventos de extracao.
- `pdf-extractor-worker` e `excel-extractor-worker` nao acessam banco e nao buscam documentos/templates diretamente em servicos de dominio.

## Task queues

As filas configuradas para encaixe com Temporal sao:

- `pdf-extractor-task-queue`
- `excel-extractor-task-queue`

Nesta implementacao local, o dispatcher do `extraction-service` chama os workers por HTTP interno em `/extract`. O nome da task queue permanece no contrato e nos eventos de dispatch.

## Input do worker

Campos principais:

- `extraction_job_id`
- `correlation_id`
- `document.document_id`, `client_id`, `competence_id`, `file_format`, `original_filename`, `storage_bucket`, `storage_key`
- `preview.preview_json` ou `preview.storage_bucket`/`storage_key`
- `template.template_id`, `template_version_id`, `version_number`, `file_format`, `structure_type`, `fields`, `extraction_rules`
- `options.strict_mode`, `options.include_debug`

Se `preview_json` existir, o worker usa o JSON recebido. Se nao existir, carrega o preview do MinIO pelo bucket/key informado.

## Output bruto

O worker retorna:

- `status`: `completed`, `completed_with_warnings`, `failed` ou `unsupported`
- `raw_extracted_fields`
- `raw_extracted_objects`
- `warnings`
- `errors`

Status por campo:

- `extracted`
- `not_found`
- `ambiguous`
- `failed`
- `partial`

O output ainda nao e normalizado. A Fase 15 transforma estes valores brutos em resultados finais revisaveis.

## Estrategias PDF

Suportadas:

- `find_near_label`
- `fixed_bbox`
- `regex_from_text`
- `pdf_area_table`
- `pdf_column_by_x_position`
- `hierarchical_lines`

Evidencia PDF gerada:

- `evidence_type = pdf`
- `document_id`
- `page_number`
- `bbox` com `x0`, `y0`, `x1`, `y1`
- `source_text`
- `rule_id`
- `rule_strategy`
- `confidence`

## Estrategias Excel

Suportadas:

- `excel_cell_address`
- `excel_column_by_header`
- `excel_range_table`
- `excel_sheet_by_name`

Preparadas como erro controlado nesta fase:

- `excel_named_range`
- `excel_header_row_detection`
- `excel_hierarchical_rows`

Evidencia Excel gerada:

- `evidence_type = excel`
- `document_id`
- `sheet_name`
- `cell_range`
- `source_value`
- `rule_id`
- `rule_strategy`
- `confidence`

## Seguranca

- nao executa macros;
- nao executa codigo vindo de template;
- nao executa formulas de planilha;
- limita regex e tamanho de texto no PDF worker;
- limita tamanho de preview carregado do MinIO;
- retorna erros/warnings controlados para regra invalida, aba ausente, campo ausente e estrategia nao suportada.

## Testes

Com Docker:

```bash
make pdf-extractor-test
make excel-extractor-test
make extraction-test
make packages-test
```

Localmente, em cada worker:

```bash
pytest -q
```

## Fora do escopo

Nao implementa normalizacao final, revisao visual, OCR, IA, Rule Builder, Rule Worker, Conference Service, Report Service ou validacoes contabeis.
