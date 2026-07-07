# {{WORKER_NAME}}

Template técnico para um worker de processamento da CCI.

O worker não expõe API HTTP. Ele carrega configuração por ambiente, configura logs JSON, registra handlers de `SIGTERM` e `SIGINT`, inicia um loop ocioso e encerra de forma limpa. Handlers, processors e adaptadores de infraestrutura permanecem vazios até a implementação do worker real.

Não há integração com Temporal, RabbitMQ, MinIO ou PostgreSQL nesta fase.

## Executar localmente

```bash
pip install -r requirements.txt
python -m worker.main
```

## Testes

```bash
pytest
```
