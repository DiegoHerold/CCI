# MinIO

Storage local compatível com S3. `buckets/buckets.txt` é a lista canônica e `infra/scripts/create-minio-buckets.sh` cria os buckets de forma idempotente.

Os buckets alvo são `cci-documents-original`, `cci-documents-preview`, `cci-extraction-artifacts`, `cci-reports` e `cci-temp`. O Compose também preserva os buckets históricos durante a migração para não quebrar componentes já entregues.

Policies de produção devem usar menor privilégio e separar leitura, escrita e administração por serviço. Nenhuma credencial local deve ser reutilizada fora de desenvolvimento.
