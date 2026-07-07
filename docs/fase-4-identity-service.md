# Fase 4 — Identity Service

## Responsabilidade e limites

O `identity-service` pertence ao Control Plane e é responsável por usuários,
autenticação, JWT, roles e permissões globais. É o único dono do schema
PostgreSQL `auth`. O BFF não lê suas tabelas e não reimplementa validação de
token. Não há regras contábeis, cliente/competência, jobs pesados, Temporal ou
eventos de domínio nesta fase.

O transporte BFF → Identity é REST interno temporário. A arquitetura alvo
continua sendo gRPC.

## Modelo persistente

A migration `0001_identity_schema` cria:

- `auth.users`: id UUID textual, nome, e-mail único normalizado, hash da senha,
  status `ACTIVE|INACTIVE` e timestamps;
- `auth.roles` e `auth.permissions`;
- `auth.user_roles` e `auth.role_permissions`.

O desligamento é lógico: a linha permanece e o status muda para `INACTIVE`.

## Roles e permissões

| Role | Permissões |
| --- | --- |
| `ADMIN` | todas as permissões (11 após a Fase 4.1) |
| `MANAGER` | `users:read` e todas as permissões `conferences:*` |
| `OPERATOR` | `conferences:read`, `conferences:create`, `conferences:execute` |
| `VIEWER` | `conferences:read` |

O contrato aditivo está em `packages/shared-auth/identity-rbac-v1.json`. Os
artefatos experimentais da Fase 2 foram preservados para não quebrar seus
consumidores.

A Fase 4.1 adicionou `users:reset-password` ao `ADMIN`; consulte
`docs/fase-4.1-identity-hardening.md` para o contrato atual de sessão.

## Contratos HTTP internos

| Método e rota | Corpo | Autorização | Respostas principais |
| --- | --- | --- | --- |
| `POST /auth/login` | `email`, `password` | pública | `200`, `401`, `422` |
| `GET /auth/me` | — | Bearer válido | `200`, `401` |
| `GET /users` | — | `users:read` | `200`, `401`, `403` |
| `POST /users` | `name`, `email`, `password`, `roles` | `users:create` | `201`, `401`, `403`, `409`, `422` |
| `GET /users/{id}` | — | `users:read` | `200`, `401`, `403`, `404` |
| `PATCH /users/{id}` | `name?`, `email?`, `roles?`, `status?` | `users:update` | `200`, `401`, `403`, `404`, `409`, `422` |
| `PATCH /users/{id}/disable` | — | `users:disable` | `200`, `401`, `403`, `404` |

Campos extras são rejeitados. Nome, e-mail, senha, roles e status são validados.
Nenhuma resposta contém senha ou `passwordHash`.

O login retorna:

```json
{
  "accessToken": "jwt",
  "tokenType": "Bearer",
  "expiresIn": 900,
  "user": {
    "id": "uuid",
    "name": "Administrador CCI",
    "email": "admin@empresa.com",
    "status": "ACTIVE",
    "roles": ["ADMIN"],
    "permissions": ["users:read"]
  }
}
```

Credenciais inválidas, usuário inexistente e usuário inativo produzem a mesma
resposta `401 INVALID_CREDENTIALS`.

## JWT e senha

- senha: Argon2 via `pwdlib`;
- JWT: PyJWT/HS256;
- claims obrigatórias: `sub`, `email`, `roles`, `permissions`, `iat`, `exp`;
- segredo mínimo: 32 caracteres, somente por variável de ambiente;
- `/auth/me` e os guards sempre recarregam o usuário, impedindo acesso após a
  desativação mesmo que o JWT ainda não tenha expirado.

## BFF

O frontend usa as rotas acima com o prefixo `/api/v1` em `localhost:8000`.
O BFF encaminha o JSON, o Bearer token e `X-Correlation-Id`. Erros e status do
Identity são preservados. Falha de rede vira `503` no BFF.

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@empresa.com","password":"senha-forte"}'

curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"
```

## Ambiente e operação

Variáveis obrigatórias:

```env
DATABASE_URL=postgresql+psycopg://cci:senha@postgres-app:5432/cci_platform
JWT_ACCESS_SECRET=um-segredo-com-pelo-menos-32-caracteres
JWT_ACCESS_EXPIRES_IN=15m
JWT_REFRESH_SECRET=outro-segredo-com-pelo-menos-32-caracteres
JWT_REFRESH_EXPIRES_IN=7d
SEED_ADMIN_NAME=Administrador CCI
SEED_ADMIN_EMAIL=admin@empresa.com
SEED_ADMIN_PASSWORD=senha-inicial-forte
```

As três variáveis `SEED_ADMIN_*` devem ser preenchidas juntas. O seed sempre
sincroniza roles/permissões, cria o administrador se não existir e nunca troca
a senha de um administrador existente.

```bash
make identity-migrate
make identity-seed
make identity-test
make identity-health
make bff-test
```

## Eventos e auditoria

Nenhum evento de domínio é publicado ou consumido nesta fase. Logs estruturados
registram método, rota, status, duração e correlação, sem corpo ou senha. O
hardening de sessões e auditoria interna foi acrescentado na Fase 4.1;
permissões por cliente permanecem fora do escopo.
