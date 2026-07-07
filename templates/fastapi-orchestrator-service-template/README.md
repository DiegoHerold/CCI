# {{SERVICE_NAME}}

Template técnico para um serviço orquestrador FastAPI da CCI.

## Responsabilidade futura

Coordenar processos longos, workflows, activities, workers, eventos, status e reprocessamentos. A organização separa domínio de orquestração, comandos, casos de uso e adaptadores de infraestrutura.

Nesta fase, o template oferece somente `/health`, `/ready` e `POST /workflows/placeholder`, além de logs JSON, correlação e erros padronizados. O diretório `infrastructure/temporal` é apenas um ponto de extensão: não há Temporal SDK nem conexão real.

## Executar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Testes

```bash
pytest
```
