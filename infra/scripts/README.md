# Scripts de Infraestrutura

Utilitarios simples para bootstrap e diagnostico local. Execute a partir da raiz do repositorio.

Scripts POSIX:

- `wait-for.sh`: aguarda host/porta com timeout.
- `create-postgres-schemas.sh`: reaplica o SQL idempotente no PostgreSQL.
- `create-minio-buckets.sh`: cria a lista canonica de buckets sem sobrescrever dados.
- `check-infra.sh`: valida o estado dos containers essenciais.
- `reset-local-env.sh`: remove volumes somente apos confirmacao explicita.

Scripts PowerShell usados pelo `Makefile` no Windows:

- `create-postgres-schemas.ps1`
- `check-infra.ps1`
- `reset-local-env.ps1`

`reset-local-env.*` e destrutivo e deve ser usado somente em ambiente local/dev.
