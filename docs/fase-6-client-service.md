# Fase 6 — Client Service completo

## Responsabilidade e limites

O `client-service` pertence ao Control Plane e organiza clientes contábeis,
competências mensais, vínculos de usuários, responsabilidades, caminhos
lógicos e o contexto inicial da Web. Ele é implantável separadamente, usa
FastAPI/Pydantic/SQLAlchemy/Alembic e é dono das tabelas abaixo no schema
PostgreSQL `core`:

- `clients`: cadastro, CNPJ normalizado, ciclo de vida e configuração de pasta;
- `client_competencies`: período mensal, status, pasta resolvida e fechamento;
- `client_users`: referência lógica ao `userId`, papel e responsabilidade;
- `user_client_preferences`: cliente/competência padrão por usuário;
- `client_audit_events`: trilha append-only sem tokens, senhas ou hashes.

O serviço não acessa tabelas `auth`, não implementa login, senha ou JWT e não
lê o filesystem. A referência a usuário é lógica; existência e status são
consultados no Identity Service pelo contrato REST interno atual. A arquitetura
alvo BFF → serviços permanece gRPC, portanto REST está documentado como
transição explícita.

## CNPJ, ciclo de vida e pastas

CNPJ com ou sem máscara é reduzido a 14 dígitos e validado pelos dois dígitos
verificadores. Sequências repetidas e valores inválidos são rejeitados;
`cnpj_normalized` possui `UNIQUE` e check PostgreSQL. O valor público retorna
formatado.

Clientes usam `ACTIVE`, `INACTIVE` e `ARCHIVED`. Inativação e arquivamento são
lógicos. Somente cliente ativo aceita competência ou vínculo novo; arquivados
ficam fora da listagem padrão.

O padrão default é `{{YYYY}}/{{MM}}`. Também são aceitos `{{competenceName}}`,
`{{previousMonth.MM}}` e `{{previousMonth.YYYY}}`. Padrão absoluto, token
desconhecido e `..` são rejeitados. O preview apenas concatena logicamente
Windows, UNC ou Unix; não testa existência e não cria diretório. A validação
física pertence a um futuro Storage/File Service.

## Competências e vínculos

Uma competência é única por `(client_id, period)` e usa `YYYY-MM`, ano
1900–2200 e mês 1–12. Status: `OPEN`, `PREPARING`,
`READY_FOR_CONFERENCE`, `IN_CONFERENCE`, `REVIEW`, `CLOSED` e `ARCHIVED`.
Fechamento registra usuário/data; fechadas não reabrem pelo fluxo normal e
arquivadas não mudam.

Vínculos são únicos por `(client_id, user_id)`, nunca copiam dados sensíveis e
usam papéis `CLIENT_MANAGER|CLIENT_OPERATOR|CLIENT_VIEWER`, áreas
`ACCOUNTING|FISCAL|PAYROLL|LEGAL|GENERAL` e estado `ACTIVE|INACTIVE`.

## Autorização

Toda rota de negócio exige Bearer válido no Identity Service, permissão global
e vínculo ativo com o cliente. `ADMIN` tem bypass explícito de vínculo. A
validação é centralizada em `ClientAccessService`; negações geram
`CLIENT_ACCESS_DENIED` na auditoria.

Permissões adicionadas ao seed idempotente do Identity:

`clients:read`, `clients:create`, `clients:update`, `clients:disable`,
`clients:archive`, `client-users:read`, `client-users:manage`,
`client-competencies:read`, `client-competencies:create`,
`client-competencies:update`, `client-competencies:close`,
`client-competencies:archive`, `client-folders:read`,
`client-folders:update`, `client-folders:preview`, `client-context:read`.

O mapeamento de `ADMIN`, `MANAGER`, `OPERATOR` e `VIEWER` está no contrato
`packages/shared-auth/identity-rbac-v2.json`.

## Contratos HTTP

Todas as rotas abaixo são internas no Client Service e públicas para a Web com
o prefixo `/api/v1` no BFF. O BFF apenas propaga método, query, body,
`Authorization`, IP e `X-Correlation-Id`; não duplica negócio.

| Rota interna | Objetivo | Permissão | Vínculo |
| --- | --- | --- | --- |
| `GET /clients` | lista paginada e filtrada | `clients:read` | filtra por vínculo; ADMIN vê todos |
| `POST /clients` | cria cliente | `clients:create` | não |
| `GET /clients/{id}` | consulta | `clients:read` | sim |
| `PATCH /clients/{id}` | atualiza cadastro | `clients:update` | sim |
| `PATCH /clients/{id}/disable` | inativa | `clients:disable` | sim |
| `PATCH /clients/{id}/archive` | arquiva | `clients:archive` | sim |
| `PATCH /clients/{id}/restore` | restaura | `clients:archive` | sim |
| `GET/PATCH /clients/{id}/folder` | consulta/atualiza pasta | `client-folders:read/update` | sim |
| `POST /clients/{id}/folder-preview` | resolve caminho lógico | `client-folders:preview` | sim |
| `GET/POST /clients/{id}/competencies` | lista/cria | `client-competencies:read/create` | sim |
| `POST .../competencies/ensure-current` | cria ou retorna idempotentemente | `client-competencies:create` | sim |
| `GET/PATCH .../competencies/{competencyId}` | consulta/atualiza | `client-competencies:read/update` | sim |
| `PATCH .../{competencyId}/status` | transição de status | `client-competencies:update` | sim |
| `PATCH .../{competencyId}/close` | fecha | `client-competencies:close` | sim |
| `PATCH .../{competencyId}/archive` | arquiva | `client-competencies:archive` | sim |
| `GET/POST /clients/{id}/users` | lista/vincula | `client-users:read/manage` | sim |
| `GET/PATCH/DELETE .../users/{userId}` | consulta/altera/inativa | `client-users:read/manage` | sim |
| `GET /client-context` | contexto inicial real | `client-context:read` | filtra por vínculo |
| `GET/PATCH /client-context/preferences` | preferência operacional | `client-context:read` | cliente preferido deve ser acessível |

Listagens aceitam paginação validada. Clientes aceitam filtros `status`,
`search`, `cnpj`, `city`, `state`, `taxRegime`, `responsibilityArea`, `page`,
`limit`, `sortBy` e `sortDirection`. Competências aceitam `status`, `year`,
`fromPeriod`, `toPeriod`, `page` e `limit`. Payloads usam camelCase e rejeitam
campos extras. Erros seguem `error.code`, `error.message` e `correlation_id`.

Exemplo:

```http
POST /api/v1/clients/{clientId}/folder-preview
Authorization: Bearer <access-token>
Content-Type: application/json

{"year": 2026, "month": 7}
```

```json
{
  "clientId": "uuid",
  "period": "2026-07",
  "defaultFolderPath": "R:\\Clientes\\Empresa",
  "competenceFolderPattern": "{{YYYY}}/{{MM}}",
  "resolvedCompetencePath": "R:\\Clientes\\Empresa\\2026\\07"
}
```

## Migration, seed e testes

`0001_client_domain` cria as cinco tabelas, FKs internas ao domínio, checks e
índices. Não existe FK para `auth.users`, preservando propriedade de schema.
O ledger Alembic é isolado em `core.alembic_version_client`, sem compartilhar
a tabela de revisão do Identity Service.
O seed já existente do Identity foi estendido e continua idempotente; nenhum
cliente fictício é criado.

```bash
make identity-seed
make client-migrate
make client-test
docker compose up -d --build identity-service client-service bff
```

`make client-test` usa `postgres-client-test`, um PostgreSQL 16 efêmero em
`tmpfs`; não usa SQLite, memória, JSON nem mock de persistência. O gateway de
Identity é substituído apenas nos testes do domínio externo, enquanto todas as
operações de cliente usam PostgreSQL real. Runtime, migration e seed usam o
cluster indicado por `DATABASE_URL`.

## Auditoria e eventos

Criação/alteração/ciclo de vida, pastas, competências, vínculos e negações de
acesso geram registros append-only. Nenhum evento oficial é publicado ou
consumido nesta fase. Os nomes `client.created`, `client.updated`,
`client.disabled`, `client.archived`, `client_user.linked`,
`client_competency.created`, `client_competency.closed` e
`client_folder.updated` ficam preparados para futura outbox em
`packages/shared-events`, antes de ativar RabbitMQ.

## Fora do escopo

Web visual, varredura/criação de pastas, upload, documentos, conferências,
Temporal, workers e IA. Evidências contábeis ainda não são produzidas; cliente,
competência, permissões e auditoria já são preservados para as próximas fases.
