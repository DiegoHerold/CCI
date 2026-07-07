# Fase 1A — Chão técnico

## Objetivo

Disponibilizar o scaffold completo da arquitetura e uma infraestrutura local reproduzível com Docker Compose.

## Componentes ativos

- PostgreSQL da aplicação, com schemas por domínio e bootstrap técnico;
- PostgreSQL separado para o Temporal;
- Redis;
- RabbitMQ;
- MinIO e criação idempotente dos buckets iniciais;
- Temporal Server e Temporal UI.

## Fora do escopo

Frontend, BFF, APIs, serviços de negócio, autenticação, uploads, regras, extração, workers, relatórios e healthchecks de aplicação permanecem sem implementação.

## Limites preservados

Não existem contratos ou eventos de domínio nesta fase. O único artefato persistente da aplicação é `core.platform_bootstrap`; ele confirma a inicialização do cluster e não representa lógica contábil.
