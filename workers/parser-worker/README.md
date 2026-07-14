# Parser Worker

Worker interno responsável por gerar preview estruturado de documentos para seleção visual futura.

Nesta fase ele oferece um endpoint interno de controle (`POST /parse`) para ser chamado pelo `document-service`.
O estado de preview, jobs e status continua pertencendo ao `document-service`.

## Formatos

- PDF: páginas, dimensões, rotação, blocos de texto, linhas, tokens, candidatos simples de tabela e detecção de ausência de camada de texto.
- XLSX: abas, células, endereços, tipos básicos, células mescladas, cabeçalhos prováveis e áreas tabulares simples.
- XLS: leitura básica de células/abas via `xlrd`.
- CSV, TXT, DOCX e XML: rejeição controlada nesta fase.

## Variáveis principais

- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `PARSER_WORKER_CONCURRENCY`
- `PARSER_MAX_FILE_SIZE_MB`
- `PARSER_PREVIEW_MAX_JSON_SIZE_MB`

## Rotas internas

- `GET /health`
- `GET /ready`
- `POST /parse`

O payload de `/parse` contém a localização do arquivo original no MinIO e o destino do JSON de preview.
