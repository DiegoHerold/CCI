# CCI BFF

Porta de entrada HTTP da CCI para a futura aplicação web. O frontend deve falar somente com o BFF; serviços internos continuam donos dos seus dados e domínios.

## Estado da Fase 3

O BFF é funcional, mas seus dados ainda são placeholders. Não há autenticação real, persistência ou chamadas a serviços. Os clients em `app/infrastructure/clients` guardam URLs e preparam a propagação de `X-Correlation-Id`, sem realizar I/O.

Endpoints:

- `GET /health` e `GET /ready`;
- `GET /api/v1/platform/status`;
- `GET /api/v1/auth/me` — usuário de desenvolvimento;
- `GET /api/v1/clients` e `/api/v1/executions` — listas vazias;
- `GET /api/v1/logs/stream` — três eventos SSE de demonstração.

O usuário de desenvolvimento será substituído pelo identity-service em fase futura.

## Executar

Pelo Compose:

```bash
docker compose up -d --build bff
curl http://localhost:8000/health
```

Localmente:

```bash
pip install -r apps/bff/requirements.txt
uvicorn app.main:app --app-dir apps/bff --reload --port 8000
```

## Testes

```bash
pytest apps/bff/tests
```

Ou em container:

```bash
make bff-test
```

## Limites

Não há integração com PostgreSQL, Redis, RabbitMQ, Temporal, MinIO ou serviços internos. Nenhum evento é publicado ou consumido. Os contratos de `packages/` não foram alterados nesta fase.
