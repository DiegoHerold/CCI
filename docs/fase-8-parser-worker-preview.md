# Fase 8 — Parser Worker e Preview

Esta fase adiciona a base de preview estruturado de documentos da CCI.

O objetivo é preparar um modelo selecionável para o futuro Web Document Viewer e Template Builder, sem executar OCR, template matching, extração final de variáveis ou IA.

## Arquitetura implementada

```text
Document Service
  cria job de preview
  controla status e histórico
  chama parser-worker
  consulta JSON de preview no MinIO

Parser Worker
  lê arquivo original no MinIO
  parseia PDF/XLSX/XLS
  salva JSON estruturado no bucket de preview
  devolve metadados ao Document Service
```

O worker expõe um endpoint interno de controle (`POST /parse`) nesta fase. Ele não concentra domínio de negócio; o estado segue no `document-service`.

## Status

Fluxo feliz:

```text
uploaded -> preview_pending -> preview_processing -> preview_ready
```

Fluxo com falha:

```text
uploaded -> preview_pending -> preview_processing -> preview_failed
```

## Banco de dados

Migration criada:

```text
services/document-service/migrations/versions/0002_document_preview.py
```

Tabelas:

- `document.document_previews`
- `document.document_parsing_jobs`

`document_previews` guarda metadados, contagens e ponteiro para o JSON no MinIO. `document_parsing_jobs` guarda cada execução, solicitante, status e erro.

## APIs do Document Service

No serviço:

```text
POST /documents/{document_id}/preview
GET  /documents/{document_id}/preview/status
GET  /documents/{document_id}/preview
POST /documents/{document_id}/preview/reprocess
```

No BFF, as mesmas rotas ficam sob:

```text
/api/v1/documents/{document_id}/preview
```

## Modelo PDF

O preview PDF contém páginas, dimensões, rotação, blocos de texto, linhas, tokens, coordenadas e candidatos simples de tabela.

Quando o PDF não tem camada de texto, o preview marca:

```json
{"requires_ocr": true, "ocr_reason": "no_text_layer_detected"}
```

## Modelo Excel

O preview Excel contém abas, células, endereços, tipos básicos, células mescladas, cabeçalho provável e área tabular provável.

Macros não são executadas e fórmulas não são avaliadas ativamente.

## Storage

Originais:

```text
MINIO_BUCKET_DOCUMENTS_ORIGINAL=cci-documents-original
```

Previews:

```text
MINIO_BUCKET_DOCUMENTS_PREVIEW=cci-documents-preview
```

Chave do preview:

```text
clients/{client_id}/competences/{competence_id}/documents/{document_id}/preview/{preview_id}.json
```

## Eventos

O publisher ainda é abstrato/no-op no Document Service, mas os eventos estão modelados:

- `DocumentPreviewRequested`
- `DocumentPreviewStarted`
- `DocumentPreviewGenerated`
- `DocumentPreviewFailed`

## Testes

```bash
docker-compose --profile test run --rm document-service-test
docker-compose run --rm --no-deps parser-worker pytest -q
```

Cobertura principal:

- job de preview;
- status `preview_ready`;
- falha `preview_failed`;
- busca do preview salvo;
- reprocessamento;
- PDF com texto;
- PDF sem texto e `requires_ocr`;
- XLSX com abas, células e mesclagem.

## Fora do escopo

- OCR real;
- viewer web;
- template matching;
- extração final;
- normalização contábil;
- revisão visual;
- IA;
- execução de regras.
