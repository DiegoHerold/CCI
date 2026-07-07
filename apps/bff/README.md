# CCI BFF

Porta HTTP da futura aplicação web. O frontend fala somente com o BFF; cada
serviço interno continua dono de seu domínio e de seus dados.

## Estado após a Fase 4

O BFF encaminha autenticação e gestão de usuários ao Identity Service por REST
interno. Ele propaga `Authorization: Bearer ...` e `X-Correlation-Id`, mas não
decodifica JWT nem replica regras de RBAC.

Desde a Fase 4.1, o refresh token fica em cookie `HttpOnly`, `SameSite=Lax` e
`Secure` em produção. O BFF remove o refresh token da resposta JSON; o frontend
mantém somente o access token curto em memória.

Rotas integradas:

- `POST /api/v1/auth/login`;
- `POST /api/v1/auth/refresh`, `/logout`, `/logout-all` e `/change-password`;
- `GET /api/v1/auth/me`;
- `GET|POST /api/v1/users`;
- `GET|PATCH /api/v1/users/{id}`;
- `PATCH /api/v1/users/{id}/disable`;
- `POST /api/v1/users/{id}/reset-password`.

Continuam disponíveis as rotas da Fase 3 para health, status da plataforma,
clientes, execuções e SSE. Essas capacidades ainda são placeholders.

## Executar e testar

```bash
docker compose up -d --build identity-service bff
make bff-health
make bff-test
```

O BFF não acessa PostgreSQL nem publica eventos. O transporte interno REST é a
etapa incremental atual; gRPC permanece como arquitetura alvo.
