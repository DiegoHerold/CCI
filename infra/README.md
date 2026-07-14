# Infra

`infra/` e o bloco oficial da arquitetura da CCI para Docker, PostgreSQL, Redis, RabbitMQ, MinIO, Temporal, gateway, observabilidade e scripts de bootstrap local.

## Estrutura

```text
infra/
  docker/
  postgres/
  redis/
  rabbitmq/
  minio/
  temporal/
  gateway/
  observability/
  scripts/
```

## Subida Local

```bash
make infra-up
make create-schemas
make create-buckets
make infra-check
make up
```

`make infra-up` sobe apenas a base tecnica. `make up` sobe tambem os apps, services e workers que existem de verdade e possuem Dockerfile funcional.

## Perfis Opcionais

```bash
docker compose --profile gateway up -d gateway
docker compose --profile observability up -d prometheus otel-collector
```

Gateway, Prometheus e OpenTelemetry Collector sao auxiliares locais. Grafana, Loki, dashboards, alertas, TLS, secrets e politicas de producao continuam fora do escopo desta infra local.

## Schemas

`infra/postgres/init/001_create_schemas.sql` cria os schemas canonicos:

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

Schemas historicos podem permanecer para compatibilidade com fases ja entregues. Migrations reais continuam nos servicos donos de cada dominio.

## Buckets

`infra/minio/buckets/buckets.txt` cria:

```text
cci-documents-original
cci-documents-preview
cci-extraction-artifacts
cci-reports
cci-temp
```

## Reset Local

```bash
make reset-local
```

Esse comando e destrutivo, pede confirmacao textual `RESET` e remove volumes locais de desenvolvimento. Nao use contra ambiente com dados que precisam ser preservados.
