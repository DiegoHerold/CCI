# Fase 7 — Document Service

## Objetivo

Implementar o `document-service` como dono dos documentos brutos enviados à plataforma. Esta fase registra arquivos, calcula hash, detecta duplicidade, salva originais no MinIO e persiste metadados no PostgreSQL.

## Escopo implementado

- `services/document-service` em FastAPI seguindo o padrão dos serviços existentes.
- Schema PostgreSQL `document` com tabelas `documents`, `document_upload_batches` e `document_status_history`.
- Upload de arquivo único via multipart.
- Upload de ZIP com extração segura de entradas suportadas.
- Rejeição de extensão inválida, arquivo vazio, ZIP inválido, ZIP com path traversal, ZIP dentro de ZIP e arquivo acima do limite.
- Hash SHA-256 pelo conteúdo real.
- Duplicidade por `client_id`, `competence_id` e `content_hash`.
- Storage MinIO/S3 no bucket `MINIO_BUCKET_DOCUMENTS_ORIGINAL`.
- Validação desacoplada de cliente/competência via Client Service.
- BFF proxy para `/api/v1/documents`.
- Contrato `packages/document-schema/upload.schema.json` atualizado.
- Eventos de documento adicionados a `packages/shared-events`.

## Endpoints

```text
POST  /documents/upload
POST  /documents/upload-zip
GET   /documents/{document_id}
GET   /documents?client_id=&competence_id=&status=&fileFormat=
PATCH /documents/{document_id}/status
```

No BFF:

```text
POST  /api/v1/documents/upload
POST  /api/v1/documents/upload-zip
GET   /api/v1/documents/{document_id}
GET   /api/v1/documents?client_id=&competence_id=
PATCH /api/v1/documents/{document_id}/status
```

## Decisões

- O `document-service` não lê o banco do `client-service`; valida contexto via HTTP interno.
- Duplicidade não cria novo documento ativo. A resposta aponta para o documento original com `status=duplicate`.
- Arquivos com mesmo hash são permitidos em outro cliente ou outra competência.
- ZIP dentro de ZIP fica fora do escopo.
- Mensageria real fica preparada por abstração/no-op, sem publicar em RabbitMQ nesta fase.

## Variáveis

```env
DOCUMENT_SERVICE_URL=http://document-service:8110
CLIENT_SERVICE_TIMEOUT_SECONDS=5
DOCUMENT_MAX_FILE_SIZE_MB=50
DOCUMENT_MAX_ZIP_SIZE_MB=200
DOCUMENT_MAX_FILES_PER_ZIP=100
DOCUMENT_ALLOWED_EXTENSIONS=.pdf,.xlsx,.xls,.csv,.txt,.docx,.xml,.zip
MINIO_BUCKET_DOCUMENTS_ORIGINAL=cci-documents-original
```

## Testes

```bash
docker compose --profile test run --rm document-service-test
```

A suíte cobre upload válido, extensão inválida, hash, duplicidade no mesmo cliente/competência, hash igual em outro contexto, ZIP válido, ZIP com arquivo inválido, path traversal em ZIP, persistência e falha simulada de storage.

## Fora do escopo

Parser visual, preview, OCR, IA, template matching, classificação, extração, normalização, revisão visual, Rule Builder, execução de regras, conferência contábil e relatórios finais.
