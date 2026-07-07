# Fase 1B — Templates técnicos

## Objetivo

Definir uma base técnica repetível para os futuros serviços e workers da CCI sem implementar lógica de negócio ou integrações reais.

## Três tipos de componente

### API Service

Usado por serviços de domínio. Organiza entrada HTTP, domínio puro, casos de uso, DTOs, infraestrutura futura e schemas. Expõe somente `GET /health` e `GET /ready` nesta fase.

### Orchestrator Service

Usado por `extraction-orchestrator` e `execution-control-service`. Acrescenta comandos, estado de orquestração e pontos de extensão para workflows, activities e Temporal. A rota `POST /workflows/placeholder` retorna `202`, mas não inicia workflow.

### Worker

Usado para processamento pesado. Não expõe HTTP: inicia de forma controlada, emite logs estruturados, aguarda trabalho futuro e encerra com segurança ao receber `SIGTERM` ou `SIGINT`.

## Padrões compartilhados

- configuração por variáveis de ambiente com `pydantic-settings`;
- logs JSON com `timestamp`, `level`, `service`, `env`, `correlation_id` e `message`;
- Dockerfile baseado em Python slim;
- dependências mínimas e testes unitários;
- diretórios preparados para domínio, aplicação e infraestrutura futura.

APIs e orquestradores aceitam `X-Correlation-Id`, geram UUID quando ausente e devolvem o identificador na resposta. Logs HTTP incluem método, caminho, status e duração.

## Healthcheck e readiness

`GET /health` confirma apenas que o processo está vivo; não consulta banco, cache, mensageria ou storage.

`GET /ready` retorna `checks: {}`. Serviços reais poderão adicionar checks de infraestrutura e retornar HTTP 503 quando algum requisito obrigatório estiver indisponível.

## Erros HTTP

Exceções HTTP, validação e falhas inesperadas usam a estrutura:

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Unexpected error",
    "correlation_id": "uuid"
  }
}
```

## Como criar componentes

```bash
python tools/create_api_service_from_template.py identity-service
python tools/create_orchestrator_from_template.py extraction-orchestrator
python tools/create_worker_from_template.py pdf-extractor-worker
```

O destino padrão é `services/<nome>` ou `workers/<nome>`. O gerador aborta se o destino existir e não estiver vazio. `--force` está disponível, mas nunca é aplicado automaticamente.

Os placeholders `{{SERVICE_NAME}}` ou `{{WORKER_NAME}}` recebem o nome informado; `{{APP_ENV}}` é materializado como `development`.

## Fora do escopo

Não há frontend, BFF funcional, domínio contábil, persistência, eventos, uploads, extração, regras ou relatórios. Também não há SDK do Temporal, SQLAlchemy, boto3, pika, Redis client, pandas, openpyxl, PyMuPDF, Docling, OCR ou bibliotecas de IA.
