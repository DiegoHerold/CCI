# CCI Identity Service

Serviço do Control Plane responsável por usuários internos, autenticação,
sessões, JWT, roles, permissões globais e auditoria interna de segurança. É
dono exclusivo das tabelas do schema PostgreSQL `auth`.

## Executar

Na raiz, copie `.env.example` para `.env`, defina segredos JWT distintos com
pelo menos 32 caracteres e as três variáveis do administrador inicial. Depois:

```bash
docker compose up -d --build identity-service bff
make identity-health
```

O container executa `alembic upgrade head` e o seed idempotente antes de
iniciar a API. Com o ambiente já instalado, os comandos individuais são:

```bash
alembic upgrade head
python -m app.infrastructure.seed
pytest -q
```

## Rotas internas

- `POST /auth/login` — pública;
- `POST /auth/refresh` — refresh token;
- `POST /auth/logout`, `/auth/logout-all` e `/auth/change-password` — Bearer;
- `GET /auth/me` — Bearer token;
- `GET /users` e `GET /users/{id}` — `users:read`;
- `POST /users` — `users:create`;
- `PATCH /users/{id}` — `users:update`;
- `PATCH /users/{id}/disable` — `users:disable`;
- `POST /users/{id}/reset-password` — `users:reset-password`;
- `GET /health` e `GET /ready`.

Para aplicações web, use as mesmas rotas com o prefixo `/api/v1` no BFF em
`http://localhost:8000`. A porta `8101` existe para diagnóstico e comunicação
interna, não para integração direta do frontend.

## Segurança

Senhas usam Argon2. Access e refresh tokens usam segredos separados; apenas o
hash SHA-256 do refresh é persistido. Sessões revogadas, expiradas ou ligadas a
usuário inativo são rejeitadas. Login tem bloqueio temporário e rate limit
persistente por IP/e-mail.

Consulte `docs/fase-4.1-identity-hardening.md` para os contratos atuais.
