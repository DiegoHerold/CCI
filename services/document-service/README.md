# Document Service

Serviço canônico responsável por documentos brutos da CCI.

## Responsabilidades

- upload manual de arquivos;
- upload de ZIP sem extração recursiva de ZIP;
- validação de extensão, tamanho e caminhos internos de ZIP;
- cálculo de hash SHA-256;
- detecção de duplicidade por `client_id`, `competence_id` e `content_hash`;
- armazenamento dos originais no MinIO;
- criaÃ§Ã£o e controle de jobs de preview;
- armazenamento e consulta de preview estruturado no MinIO;
- metadados no schema PostgreSQL `document`;
- status inicial do documento e histórico básico.

Fora do escopo desta fase: OCR real, IA, template matching, classificação, extração final, normalização, revisão visual, regras e conferência.

## Integração com Client Service

O serviço não acessa tabelas do `client-service`. Ele valida cliente, competência e acesso chamando o Client Service via HTTP interno com o mesmo Bearer token recebido.

## Endpoints internos

```text
POST  /documents/upload
POST  /documents/upload-zip
GET   /documents/{document_id}
GET   /documents?client_id=&competence_id=&status=&fileFormat=
PATCH /documents/{document_id}/status
POST  /documents/{document_id}/preview
GET   /documents/{document_id}/preview/status
GET   /documents/{document_id}/preview
POST  /documents/{document_id}/preview/reprocess
GET   /health
GET   /ready
```

No BFF, essas rotas ficam disponíveis sob `/api/v1`.

## Storage

Bucket de originais configurável por `MINIO_BUCKET_DOCUMENTS_ORIGINAL`, com padrão `cci-documents-original`.
Bucket de preview configurável por `MINIO_BUCKET_DOCUMENTS_PREVIEW`, com padrão `cci-documents-preview`.

Chave de armazenamento:

```text
clients/{client_id}/competences/{competence_id}/documents/{document_id}/{stored_filename}
```

Chave de preview:

```text
clients/{client_id}/competences/{competence_id}/documents/{document_id}/preview/{preview_id}.json
```

## Eventos

O serviço modela eventos com publisher abstrato/no-op nesta fase:

- `DocumentUploaded`
- `DocumentDuplicateDetected`
- `DocumentRejected`
- `DocumentStorageFailed`
- `DocumentPreviewRequested`
- `DocumentPreviewStarted`
- `DocumentPreviewGenerated`
- `DocumentPreviewFailed`

RabbitMQ não é publicado diretamente ainda.

## Testes

```bash
docker compose --profile test run --rm document-service-test
```
