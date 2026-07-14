# Preparação de infra e packages

## Objetivo

Completar a estrutura-base da arquitetura oficial sem implementar novos serviços, workflows, consumers ou regras de negócio. A mudança é aditiva e preserva os componentes funcionais até a Fase 6.

## Infra

`infra/` contém Dockerfiles de referência, schemas PostgreSQL canônicos, configuração Redis, definitions conceituais RabbitMQ, buckets MinIO, base Temporal, gateway opcional, observabilidade inicial e scripts operacionais seguros.

O Compose principal continua iniciando PostgreSQL, Redis, RabbitMQ, MinIO, Temporal, Identity, Client e BFF. `docker-compose.override.yml` adiciona somente perfis opcionais:

```bash
docker compose --profile gateway up -d gateway
docker compose --profile observability up -d prometheus otel-collector
```

As definitions RabbitMQ não são importadas automaticamente, pois ainda não existem consumers e uma importação poderia modificar um broker persistente. Temporal não contém workflows. Observabilidade não contém dashboards, Loki funcional, retenção ou alertas.

Schemas e buckets históricos são preservados. Os canônicos são adicionados de forma idempotente; migração de tabelas, objetos ou consumers requer fase própria.

## Packages

Contracts canônicos disponíveis:

- base: `shared-types`, `shared-events`, `shared-auth`;
- documentos e templates: `document-schema`, `template-schema`, `annotation-schema`;
- extração: `field-schema`, `extraction-schema`, `evidence-schema`;
- conferência e regras: `rule-schema`, `conference-schema`, `rule-engine`.

`variable-schema` permanece como compatibilidade da Fase 2. Novos serviços devem preferir campo/objeto extraído com evidência e revisão.

O padrão físico existente foi mantido: JSON Schema canônico, espelhos em `python/` e `typescript/` e validações em `tests/`. Metadata de publicação por package será adicionada quando houver estratégia de versionamento e distribuição; nesta fase o consumo é interno ao monorepo.

## Eventos e limites de domínio

O catálogo reserva eventos de documento, template, extração, regras, conferência e relatório. A reserva não publica mensagens. Cada serviço futuro deve definir payload, versão, producer, consumer, retry e idempotência antes de ativar RabbitMQ.

Cliente, competência e correlation ID atravessam os contratos pertinentes. Permissões continuam sob Identity/Client. Evidência identifica a origem de dados; auditoria e timeline de negócio pertencem ao Conference Service e não se confundem com logs técnicos.

## Operação local

```bash
docker compose up -d
docker compose ps
make infra-check
pytest packages
```

Use `make create-schemas` e `make create-buckets` para bootstrap idempotente. `make reset` exige digitar `RESET` antes de remover volumes.
