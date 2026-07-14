# Recriar Infra Docker Local

Use este roteiro quando o Docker local tiver sido reinstalado, volumes tiverem sido perdidos ou for necessario preparar um ambiente de desenvolvimento limpo.

## Escopo

Esta rotina prepara somente infraestrutura local e os componentes existentes no workspace:

- PostgreSQL da aplicacao com schemas por dominio.
- Redis.
- RabbitMQ com management UI e definitions locais.
- MinIO com buckets canonicos.
- Temporal e Temporal UI.
- Web App, BFF, Identity, Client, Document, Template e Parser Worker.

Servicos futuros (`extraction-service`, `rule-service`, `conference-service`, `report-service` e workers extratores futuros) nao entram no Compose obrigatorio enquanto nao houver codigo e Dockerfile funcional.

## Passo a Passo

```bash
cp .env.example .env
make infra-up
make create-schemas
make create-buckets
make infra-check
make up
docker compose ps
```

Sem `make`:

```bash
cp .env.example .env
docker compose up -d postgres-app redis rabbitmq minio minio-setup temporal-postgres temporal temporal-ui
powershell -NoProfile -ExecutionPolicy Bypass -File infra/scripts/create-postgres-schemas.ps1
docker compose run --rm minio-setup
powershell -NoProfile -ExecutionPolicy Bypass -File infra/scripts/check-infra.ps1
docker compose up -d --build
docker compose ps
```

## Schemas

`infra/postgres/init/001_create_schemas.sql` prepara:

```text
identity
client
document
template
extraction
rule
conference
report
```

O script tambem preserva schemas historicos usados por fases ja entregues. Migrations reais continuam isoladas nos servicos.

## Buckets

`infra/minio/buckets/buckets.txt` prepara:

```text
cci-documents-original
cci-documents-preview
cci-extraction-artifacts
cci-reports
cci-temp
```

`make create-buckets` e idempotente.

## Portas

| Componente | Porta |
| --- | --- |
| Web App | 3000 |
| BFF | 8000 |
| PostgreSQL App | 5432 |
| Redis | 6379 |
| RabbitMQ AMQP | 5672 |
| RabbitMQ Management | 15672 |
| MinIO API | 9000 |
| MinIO Console | 9001 |
| Temporal | 7233 |
| Temporal UI | 8233 |
| Identity Service | 8101 |
| Client Service | 8102 |
| Document Service | 8110 |
| Template Service | 8120 |
| Parser Worker | 8121 |

## Reset Local

```bash
make reset-local
```

Atencao: esse comando remove containers e volumes locais de desenvolvimento depois de confirmacao textual `RESET`. Ele apaga bancos, filas e buckets locais.

## Validacao

```bash
docker compose config --quiet
make infra-check
curl -fsS http://localhost:8000/ready
curl -fsS http://localhost:8101/ready
curl -fsS http://localhost:8102/ready
curl -fsS http://localhost:8110/ready
curl -fsS http://localhost:8120/ready
curl -fsS http://localhost:8121/ready
```
