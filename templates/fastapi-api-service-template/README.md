# {{SERVICE_NAME}}

Template técnico para uma API de domínio FastAPI da CCI.

## Camadas

- `api`: entrada HTTP e rotas;
- `domain`: entidades, value objects e serviços de domínio puros;
- `application`: casos de uso e DTOs;
- `infrastructure`: banco, repositórios, mensageria e clientes futuros;
- `schemas`: contratos HTTP de entrada e saída.

O template implementa somente `/health`, `/ready`, logs JSON, correlação e erros padronizados. Não há domínio, banco ou integração externa.

## Executar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Testes

```bash
pytest
```
