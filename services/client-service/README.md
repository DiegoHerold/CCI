# Client Service

Serviço do Control Plane responsável por clientes contábeis, competências,
vínculos usuário/cliente, pastas lógicas e contexto operacional da Web. É o
único dono das tabelas de cliente no schema PostgreSQL `core`.

## Execução

```bash
docker compose up -d --build identity-service client-service bff
make client-migrate
make client-test
make client-health
```

O runtime e o Alembic usam exclusivamente `DATABASE_URL`. O Client Service não
lê tabelas `auth`: autentica e consulta usuários pelo contrato REST interno do
Identity Service, enquanto a migração alvo para comunicação interna continua
sendo gRPC.

Variáveis: `DATABASE_URL`, `IDENTITY_SERVICE_URL`,
`IDENTITY_TIMEOUT_SECONDS` e `DEFAULT_COMPETENCE_FOLDER_PATTERN`.

## Limites

Não há leitura/criação física de pastas, upload, processamento de documentos,
regras, workers ou mensageria. Os eventos de domínio estão nomeados na
aplicação e registrados como auditoria append-only, mas não são publicados.
