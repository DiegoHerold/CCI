# Fase 3 — BFF inicial

## Objetivo

Disponibilizar a primeira porta de entrada HTTP da CCI. A futura web em `http://localhost:3000` fala somente com o BFF, que futuramente comporá respostas e propagará contexto aos serviços internos.

## Endpoints

- `/health`: vida do processo, sem dependências externas;
- `/ready`: valida somente configuração básica;
- `/api/v1/platform/status`: mostra os serviços futuros como `not_connected`;
- `/api/v1/auth/me`: usuário administrativo placeholder de desenvolvimento;
- `/api/v1/clients`: lista vazia até existir client-service;
- `/api/v1/executions`: lista vazia até existir execution-control-service;
- `/api/v1/logs/stream`: SSE finito de demonstração.

## Correlation ID e logs

O middleware lê `X-Correlation-Id` ou gera UUID, armazena no contexto, devolve o header e inclui o valor nos logs JSON. Os clients placeholder já sabem construir o header para comunicação interna futura.

Logs de request incluem método, caminho, status e duração, além de timestamp, nível, serviço, ambiente, correlação e mensagem.

## SSE placeholder

O stream envia `connected`, `heartbeat` e `placeholder_log`, todos com o mesmo correlation ID. Não há conexão com RabbitMQ ou log-service; o fluxo real futuro será `log-service → BFF → frontend`.

## Executar e testar

```bash
docker compose up -d --build bff
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/api/v1/platform/status
pytest apps/bff/tests
```

## Fora do escopo

Login/JWT, permissões reais por cliente, serviços de domínio, banco, cache, mensageria, workflows, storage e gRPC. Nenhum contrato compartilhado foi alterado e nenhum evento é produzido ou consumido.
