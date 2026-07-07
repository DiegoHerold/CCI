# Packages compartilhados

Fonte oficial dos contratos interoperáveis da CCI:

- `shared-types`: tipos e estados centrais;
- `shared-events`: catálogo, envelope e payloads de eventos;
- `shared-auth`: roles, permissões, claims e helpers puros;
- `document-schema`: documentos e evidências;
- `variable-schema`: variáveis normalizadas;
- `rule-schema`: regras versionadas e árvores lógicas;
- `rule-engine`: avaliação pura em memória.

JSON Schema é a fonte canônica. Python/Pydantic e TypeScript são espelhos mantidos nesta fase manualmente. Os packages não acessam banco, arquivos, APIs, RabbitMQ, Temporal ou MinIO.

Testes:

```bash
pip install -r packages/requirements-test.txt
pytest packages
```
