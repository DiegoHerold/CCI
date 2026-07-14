# CCI — Conferência Contábil Inteligente

A CCI é uma plataforma distribuída para automatizar conferências contábeis por cliente e competência. O fluxo alvo registra documentos, gera preview estruturado, identifica templates, extrai campos/objetos com evidência, normaliza valores, executa regras versionadas e produz resultado consolidado, auditoria, timeline e relatórios.

## Arquitetura oficial

```text
apps/       Web App e BFF
services/   domínios de negócio principais
workers/    tarefas pesadas e assíncronas
packages/   contratos, schemas, eventos, autenticação e bibliotecas puras
infra/      Docker, banco, cache, mensageria, storage, workflows e observabilidade
docs/       contexto, arquitetura e fases
```

Serviços canônicos:

- `identity-service`
- `client-service`
- `document-service`
- `template-service`
- `extraction-service`
- `rule-service`
- `conference-service`
- `report-service`

Os diretórios antigos mais granulares em `services/` são scaffolds históricos ou candidatos a módulos internos. A arquitetura atual evita criar microserviço para cada etapa técnica cedo demais.

Decisão central:

> Tipo de documento é categoria do template. O template é o centro do motor de extração.

## Estado atual

Já existem entregas até a Fase 6:

- Fase 1A: chão técnico com Docker Compose, PostgreSQL, Redis, RabbitMQ, MinIO, Temporal, `.env`, README e Makefile.
- Fase 1B: templates técnicos para serviços FastAPI, orquestração e workers.
- Fase 2: packages compartilhados iniciais.
- Fase 3: BFF inicial em FastAPI.
- Fase 4 e 4.1: Identity Service com autenticação, JWT, sessões, RBAC e hardening.
- Fase 5 e 5.1: Web inicial e telas administrativas preparadas para serviços incompletos.
- Fase 6: Client Service com clientes, competências, vínculos, pastas lógicas e autorização por cliente.
- Fase 7: Document Service com upload de arquivos/ZIP, hash, duplicidade, MinIO e metadados.

O BFF, a Web, o Identity Service, o Client Service e o Document Service são componentes funcionais. Os demais domínios continuam para fases futuras.

## Infra local

Containers disponíveis:

- PostgreSQL principal da aplicação.
- PostgreSQL exclusivo do Temporal.
- Redis.
- RabbitMQ com interface de administração.
- MinIO e inicializador idempotente de buckets.
- Temporal Server.
- Temporal UI.
- BFF inicial em FastAPI.
- Identity Service.
- Client Service.
- Document Service.

Gateway Nginx, Prometheus e OpenTelemetry Collector estão preparados em `docker-compose.override.yml`, mas só iniciam com os perfis `gateway` e `observability`.

Portas locais:

| Componente | Endereço |
| --- | --- |
| PostgreSQL App | `localhost:5432` |
| Redis | `localhost:6379` |
| RabbitMQ AMQP | `localhost:5672` |
| RabbitMQ Management | http://localhost:15672 |
| MinIO API | http://localhost:9000 |
| MinIO Console | http://localhost:9001 |
| Temporal Server | `localhost:7233` |
| Temporal UI | http://localhost:8233 |
| BFF | http://localhost:8000 |
| Identity Service (diagnóstico) | http://localhost:8101 |
| Client Service (diagnóstico) | http://localhost:8102 |
| Document Service (diagnóstico) | http://localhost:8110 |

O PostgreSQL do Temporal não publica porta no host e só pode ser acessado pela rede interna do Compose.

## Como executar

Pré-requisitos:

- Docker Desktop com Docker Compose.
- `make` opcional.

```bash
docker compose up -d
docker compose ps
```

Opcionalmente:

```bash
make up
make ps
```

Para personalizar o ambiente local, copie `.env.example` para `.env` e altere apenas os valores necessários.

## Parar e limpar

Parar sem remover dados:

```bash
docker compose down
```

Parar e remover volumes persistentes:

```bash
docker compose down -v
```

O segundo comando apaga bancos, buckets e filas locais.

## PostgreSQL e MinIO

O projeto usa inicialmente um único cluster PostgreSQL para a aplicação, com isolamento lógico por schemas. Schemas atuais como `auth`, `core`, `documents`, `variables`, `execution`, `audit` e `logs` pertencem às fases já entregues ou aos scaffolds iniciais.

Schemas alvo da arquitetura:

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

Buckets MinIO locais atuais:

- `raw-documents`
- `processed-documents`
- `reports`
- `evidences`

Buckets alvo:

- `cci-documents-original`
- `cci-documents-preview`
- `cci-extraction-artifacts`
- `cci-reports`
- `cci-temp`

O setup cria os dois conjuntos de forma idempotente. Os nomes antigos preservam consumidores atuais; os nomes canônicos devem ser usados por serviços novos. Migração ou remoção exige fase explícita.

## Packages compartilhados

JSON Schema é o contrato canônico; Python/Pydantic e TypeScript são espelhos. Serviços importam contratos, mas packages não acessam PostgreSQL, MinIO, RabbitMQ, Temporal ou APIs.

`variable-schema` continua disponível por compatibilidade. Novos fluxos usam `field-schema` para definição, `extraction-schema` para valores extraídos e revisão e `evidence-schema` para origem. Consulte `packages/README.md`.

## Adicionar serviços e workers

Crie apenas um domínio canônico ou worker previsto, usando os geradores existentes em `tools/`. Adicione o componente ao Compose somente quando houver Dockerfile e healthcheck reais. Serviços de negócio recebem cliente, competência, permissões e correlation ID nos contratos; tarefas pesadas devem ser delegadas a Temporal/workers e eventos usam `packages/shared-events`.

Dockerfiles em `infra/docker/` são referências e não substituem automaticamente Dockerfiles funcionais já existentes.

## Fases documentadas

Consulte `docs/README.md` para a lista de fases existentes e o roadmap oficial 1A a 33.

Os próximos blocos principais são:

- Fase 7: Document Service.
- Fase 8: Parser Worker e Preview.
- Fase 9: Web Document Viewer.
- Fase 10: Template Service.
- Fase 11: Template Matching.
- Fase 12: Template Builder / Annotation.
- Fase 13 em diante: Extraction, regras, conferência, relatórios, observabilidade, qualidade, CI/CD e produção.

## Comandos úteis

```bash
make logs
make postgres-shell
make redis-cli
make rabbitmq-logs
make minio-logs
make temporal-logs
make identity-logs
make identity-health
make identity-test
make client-health
make client-test
make bff-logs
make bff-health
make bff-test
make build
make migrate
make seed
make test
make lint
make format
make infra-check
make create-buckets
make create-schemas
make reset
```

`make reset` e `make clean` removem volumes locais somente após confirmação explícita.

## Fontes canônicas

- `AGENTS.md`
- `docs/contexto_mestre_conferencia_contabil.md`
- `docs/arquitetura_conferencia_contabil.mmd`
