# CCI — Conferência Contábil Inteligente

A CCI é uma plataforma distribuída para automatizar conferências contábeis por cliente e competência. O fluxo futuro identificará documentos, extrairá e normalizará dados, executará regras versionadas e produzirá resultados, evidências, auditoria e relatórios.

## Evolução por fases

A Fase 1A criou o chão técnico, a Fase 1B padronizou templates, a Fase 2 definiu contratos compartilhados e a Fase 3 disponibilizou o BFF inicial. Serviços de negócio, workers e frontend ainda não foram implementados.

Os containers disponíveis são:

- PostgreSQL principal da aplicação;
- PostgreSQL exclusivo do Temporal;
- Redis;
- RabbitMQ com interface de administração;
- MinIO e inicializador idempotente de buckets;
- Temporal Server;
- Temporal UI;
- BFF inicial em FastAPI.

## Pré-requisitos

- Docker Desktop com Docker Compose;
- `make` é opcional; todos os comandos também podem ser executados diretamente com `docker compose`.

## Como executar

```bash
docker compose up -d
docker compose ps
```

Opcionalmente:

```bash
make up
make ps
```

O Compose possui valores locais padrão. Para personalizar, copie `.env.example` para `.env` e altere apenas o ambiente local.

## Parar e limpar

Parar sem remover os dados:

```bash
docker compose down
```

Parar e remover os volumes persistentes:

```bash
docker compose down -v
```

O segundo comando apaga os bancos, buckets e filas locais.

## Portas locais

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

O PostgreSQL do Temporal não publica porta no host e só pode ser acessado pela rede interna do Compose.

## Credenciais locais de desenvolvimento

| Componente | Usuário/chave | Senha/segredo | Banco |
| --- | --- | --- | --- |
| PostgreSQL App | `cci` | `cci_password` | `cci_platform` |
| RabbitMQ | `cci` | `cci_password` | — |
| MinIO | `cci_minio` | `cci_minio_password` | — |

Estas credenciais são exclusivas para desenvolvimento local e não devem ser reutilizadas em outros ambientes.

## PostgreSQL da aplicação

A fase inicial utiliza um único cluster PostgreSQL para a aplicação, com isolamento lógico por schemas:

`auth`, `core`, `models`, `schedules`, `documents`, `extraction`, `variables`, `rules`, `execution`, `audit`, `reports` e `logs`.

Cada serviço futuro será dono do seu domínio e não poderá acessar diretamente as tabelas internas de outro serviço. O script `infra/postgres/init/001_create_schemas.sql` cria somente os schemas e a tabela técnica `core.platform_bootstrap`.

O Temporal usa outro container e outro volume PostgreSQL. Seus dados internos nunca são misturados ao banco `cci_platform`.

## Buckets MinIO

O container `minio-setup` cria de forma idempotente:

- `raw-documents`;
- `processed-documents`;
- `reports`;
- `evidences`.

Após concluir, o container de setup permanece encerrado com código `0`; esse é o comportamento esperado.

## Estrutura do repositório

```text
apps/       BFF inicial funcional e scaffold da futura web
services/   serviços de domínio futuros
workers/    processamento pesado futuro
packages/   contratos e bibliotecas compartilhadas futuras
infra/      infraestrutura, inicialização e observabilidade
docs/       contexto, arquitetura e documentação de fases
```

O BFF e o Identity Service são os componentes de aplicação funcionais nesta etapa. Os demais serviços, workers e a web continuam como scaffolds.

## Fase 1B — Templates Técnicos

Esta fase adiciona somente modelos técnicos reutilizáveis; nenhum serviço ou worker real foi implementado ou incluído no Docker Compose.

- `templates/fastapi-api-service-template`: API FastAPI de domínio em camadas;
- `templates/fastapi-orchestrator-service-template`: API de coordenação preparada para workflows futuros;
- `templates/python-worker-template`: worker Python sem servidor HTTP.

Exemplos de geração:

```bash
python tools/create_api_service_from_template.py identity-service
python tools/create_orchestrator_from_template.py extraction-orchestrator
python tools/create_worker_from_template.py pdf-extractor-worker
```

Os scripts recusam pastas não vazias. A opção `--force` existe para uso explícito e nunca é aplicada automaticamente. Consulte `docs/fase-1b-templates-tecnicos.md` para os contratos técnicos de health, readiness, logs, correlação e erros.

## Fase 2 — Packages Compartilhados

A Fase 2 define contratos, exemplos e validações sem implementar serviços reais:

- `shared-types`: entidades e estados comuns;
- `shared-events`: catálogo e envelopes de eventos versionados;
- `shared-auth`: roles, permissões, claims e autorização pura;
- `document-schema`: documentos e evidências;
- `variable-schema`: dados normalizados consumidos por regras;
- `rule-schema`: regras versionadas e operadores permitidos;
- `rule-engine`: motor Python puro, em memória e sem `eval`.

JSON Schema é a fonte canônica; Pydantic e TypeScript fornecem os espelhos iniciais. Para executar os testes:

```bash
pip install -r packages/requirements-test.txt
pytest packages
```

Esta fase não publica eventos, não acessa infraestrutura e não adiciona componentes ao Docker Compose.

## Fase 3 — BFF Inicial

O BFF FastAPI em `apps/bff` é a porta de entrada da futura web. Os placeholders de clientes, execuções e SSE permanecem; o placeholder de identidade foi substituído na Fase 4.

```bash
docker compose up -d --build bff
make bff-health
make bff-test
```

Todas as respostas propagam `X-Correlation-Id`, os logs são JSON e o CORS permite `http://localhost:3000`. Consulte `docs/fase-3-bff-inicial.md`.

## Fase 4 — Identity Service

O serviço FastAPI em `services/identity-service` implementa usuários persistentes, Argon2, login, JWT com expiração, `/auth/me`, RBAC e gestão administrativa. O schema `auth` é migrado com Alembic e o seed idempotente cria roles, permissões e o administrador configurado por ambiente.

```bash
copy .env.example .env
# preencha JWT_ACCESS_SECRET, JWT_REFRESH_SECRET e SEED_ADMIN_*
docker compose up -d --build identity-service bff
make identity-test
make bff-test
```

O frontend usa apenas as rotas `/api/v1/auth/*` e `/api/v1/users*` do BFF. Consulte `docs/fase-4-identity-service.md`.

## Fase 4.1 — Identity Service Hardening

O Identity agora mantém sessões persistentes, access/refresh tokens com
segredos separados, logout e revogação, troca/reset de senha, bloqueio por
falhas, rate limit persistente e auditoria interna append-only. Para a web, o
BFF mantém o refresh token em cookie `HttpOnly`; o access token curto permanece
somente em memória.

Consulte `docs/fase-4.1-identity-hardening.md` para fluxos, variáveis e
limitações.

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
make bff-logs
make bff-health
make bff-test
```

## Próximos passos

As próximas fases podem implementar os demais serviços gradualmente, mantendo o BFF sem domínio próprio e preservando a separação entre Control Plane, Data Plane, workers, packages e infraestrutura.
