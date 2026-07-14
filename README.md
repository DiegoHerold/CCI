# CCI - Conferencia Contabil Inteligente

A CCI e uma plataforma distribuida para automatizar conferencias contabeis por cliente e competencia. O fluxo alvo registra documentos, gera preview estruturado, identifica templates, extrai campos/objetos com evidencia, normaliza valores, executa regras versionadas e produz resultado consolidado, auditoria, timeline e relatorios.

## Arquitetura Oficial

```text
apps/       Web App e BFF
services/   dominios de negocio principais
workers/    tarefas pesadas e assincronas
packages/   contratos, schemas, eventos, autenticacao e bibliotecas puras
infra/      Docker, banco, cache, mensageria, storage, workflows e observabilidade
docs/       contexto, arquitetura e fases
```

Servicos canonicos: `identity-service`, `client-service`, `document-service`, `template-service`, `extraction-service`, `rule-service`, `conference-service` e `report-service`.

Os diretorios antigos mais granulares em `services/` sao scaffolds historicos ou candidatos a modulos internos. A arquitetura atual evita criar microservico para cada etapa tecnica cedo demais.

## Estado Atual

Ja existem entregas ate a Fase 12:

- Fase 1A: chao tecnico com Docker Compose, PostgreSQL, Redis, RabbitMQ, MinIO, Temporal, `.env`, README e Makefile.
- Fase 1B: templates tecnicos para servicos FastAPI, orquestracao e workers.
- Fase 2: packages compartilhados iniciais.
- Fase 3: BFF inicial em FastAPI.
- Fase 4 e 4.1: Identity Service com autenticacao, JWT, sessoes, RBAC e hardening.
- Fase 5 e 5.1: Web inicial e telas administrativas preparadas para servicos incompletos.
- Fase 6: Client Service com clientes, competencias, vinculos, pastas logicas e autorizacao por cliente.
- Fase 7: Document Service com upload de arquivos/ZIP, hash, duplicidade, MinIO e metadados.
- Fase 8: Parser Worker e preview estruturado PDF/Excel.
- Fase 9: Web Document Viewer com selecao visual e evidencias.
- Fase 10: Template Service com templates, campos, annotations, extraction rules e versoes.
- Fase 11: Template Matching dentro do Template Service.
- Fase 12: Template Builder visual e annotations com regra tecnica sugerida.

Componentes funcionais no Compose padrao: Web, BFF, Identity Service, Client Service, Document Service, Template Service e Parser Worker. Extraction, Rule, Conference e Report continuam para fases futuras e nao entram como servicos obrigatorios.

## Infra Local

Base tecnica:

- `postgres-app`
- `redis`
- `rabbitmq`
- `minio`
- `minio-setup`
- `temporal-postgres`
- `temporal`
- `temporal-ui`

Apps, services e workers existentes:

- `web-app`
- `bff`
- `identity-service`
- `client-service`
- `document-service`
- `template-service`
- `parser-worker`

Perfis opcionais em `docker-compose.override.yml`:

- `gateway`: Nginx local para `/`, `/web` e `/api`.
- `observability`: Prometheus e OpenTelemetry Collector iniciais.

## Portas

| Componente | Endereco |
| --- | --- |
| Web App | http://localhost:3000 |
| BFF | http://localhost:8000 |
| PostgreSQL App | `localhost:5432` |
| Redis | `localhost:6379` |
| RabbitMQ AMQP | `localhost:5672` |
| RabbitMQ Management | http://localhost:15672 |
| MinIO API | http://localhost:9000 |
| MinIO Console | http://localhost:9001 |
| Temporal Server | `localhost:7233` |
| Temporal UI | http://localhost:8233 |
| Identity Service | http://localhost:8101 |
| Client Service | http://localhost:8102 |
| Document Service | http://localhost:8110 |
| Template Service | http://localhost:8120 |
| Parser Worker | http://localhost:8121 |
| Gateway opcional | http://localhost:8080 |
| Prometheus opcional | http://localhost:9090 |

O PostgreSQL do Temporal nao publica porta no host.

## Recriar Ambiente Local

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

## Schemas PostgreSQL

O cluster principal da aplicacao usa schemas por dominio. O bootstrap cria de forma idempotente:

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

Schemas historicos como `auth`, `core`, `documents`, `variables`, `execution`, `audit` e `logs` podem existir por causa das fases ja entregues. Eles nao redefinem a arquitetura alvo.

Migrations reais continuam dentro de cada servico:

```bash
make migrate
```

## Buckets MinIO

`infra/minio/buckets/buckets.txt` prepara:

```text
cci-documents-original
cci-documents-preview
cci-extraction-artifacts
cci-reports
cci-temp
```

O setup e idempotente:

```bash
make create-buckets
```

## Comandos Uteis

```bash
make up
make down
make restart
make build
make logs
make ps
make infra-up
make infra-down
make infra-check
make create-buckets
make create-schemas
make migrate
make seed
make test
make lint
make format
make reset-local
```

`make reset`, `make reset-local` e `make clean` removem volumes locais somente apos confirmacao explicita. Use apenas em desenvolvimento local.

## Testes Rapidos

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

## Fontes Canonicas

- `AGENTS.md`
- `docs/contexto_mestre_conferencia_contabil.md`
- `docs/arquitetura_conferencia_contabil.mmd`
