# Scripts de infraestrutura

Utilitários simples para bootstrap e diagnóstico local. Execute a partir da raiz do repositório.

- `wait-for.sh`: aguarda host/porta com timeout.
- `create-postgres-schemas.sh`: reaplica o SQL idempotente no PostgreSQL.
- `create-minio-buckets.sh`: cria a lista canônica de buckets sem sobrescrever dados.
- `check-infra.sh`: valida o estado dos containers essenciais.
- `reset-local-env.sh`: remove volumes somente após confirmação explícita.
