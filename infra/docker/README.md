# Imagens base

Referências simples para padronizar containers sem substituir Dockerfiles já existentes nos componentes.

- `base-python.Dockerfile`: base para FastAPI e workers Python.
- `base-node.Dockerfile`: base para apps Node/Next.js.
- `service.Dockerfile`: referência de serviço FastAPI.
- `worker.Dockerfile`: referência de worker assíncrono.
- `web.Dockerfile`: referência de Web App Next.js.

Os Dockerfiles usam contexto na raiz do componente. Ajuste paths e comandos no Dockerfile do componente antes de adotá-los; otimizações avançadas e publicação em registry ficam para fases futuras.
