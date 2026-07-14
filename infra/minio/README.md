# MinIO

Storage local compativel com S3. `buckets/buckets.txt` e a lista canonica e `infra/scripts/create-minio-buckets.sh` cria os buckets de forma idempotente.

Buckets:

- `cci-documents-original`
- `cci-documents-preview`
- `cci-extraction-artifacts`
- `cci-reports`
- `cci-temp`

Policies de producao devem usar menor privilegio e separar leitura, escrita e administracao por servico. Credenciais locais nao devem ser reutilizadas fora de desenvolvimento.
