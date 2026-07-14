# Infra

`infra/` é bloco oficial da arquitetura da CCI. A responsabilidade desta pasta é sustentar o ambiente local e a evolução operacional com Docker, PostgreSQL, Redis, RabbitMQ, MinIO, Temporal, gateway, observabilidade e scripts de bootstrap.

## Estrutura alvo

```text
infra/
├── docker/
├── postgres/
├── redis/
├── rabbitmq/
├── minio/
├── temporal/
├── gateway/
├── observability/
└── scripts/
```

## Estado atual

Todas as pastas alvo existem. PostgreSQL, Redis, RabbitMQ, MinIO e Temporal continuam funcionais no Compose principal. Gateway, Prometheus e OpenTelemetry Collector são extensões locais opcionais por perfil; Dockerfiles, policies, dashboards e workflows são bases de referência, não produção pronta.

```bash
docker compose up -d
docker compose --profile gateway up -d gateway
docker compose --profile observability up -d prometheus otel-collector
make infra-check
```

## Schemas sugeridos

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

Schemas históricos como `auth`, `core`, `documents`, `variables`, `execution`, `audit` e `logs` podem existir por causa das fases já entregues. Eles não redefinem a arquitetura alvo.

## Buckets sugeridos

```text
cci-documents-original
cci-documents-preview
cci-extraction-artifacts
cci-reports
cci-temp
```

Buckets locais antigos continuam sendo criados para compatibilidade. Os nomes canônicos também são criados de forma idempotente; migração de objetos e consumers exige fase explícita.

## Segurança e reset

Consoles e portas publicados destinam-se apenas a desenvolvimento local. Produção deve restringir serviços internos, adicionar secrets, TLS, backups e políticas de retenção. `make reset` e `make clean` pedem confirmação antes de remover volumes.
