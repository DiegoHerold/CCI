# Packages compartilhados

Fonte oficial dos contratos interoperáveis da CCI. Packages contêm tipos, schemas, eventos, autenticação e bibliotecas puras; não acessam banco, arquivos, APIs, RabbitMQ, Temporal ou MinIO.

## Packages canônicos

- `shared-types`: tipos e estados centrais.
- `shared-events`: catálogo, envelope e payloads de eventos.
- `shared-auth`: roles, permissões, claims e helpers puros.
- `document-schema`: documentos, uploads, status e preview.
- `template-schema`: templates, categorias, campos/objetos e versões.
- `annotation-schema`: seleções visuais, bbox, células, colunas, tabelas e evidências visuais.
- `extraction-schema`: jobs, resultados, normalização, confiança, status e revisão.
- `evidence-schema`: evidências textuais, visuais e estruturadas.
- `field-schema`: campos, objetos, arrays, tabelas e calculados.
- `rule-schema`: regras versionadas e árvores lógicas.
- `conference-schema`: modelos, execuções, resultados, auditoria e timeline.
- `rule-engine`: avaliação pura em memória.

## Estado atual

A Fase 2 criou `shared-types`, `shared-events`, `shared-auth`, `document-schema`, `variable-schema`, `rule-schema` e `rule-engine`. A preparação arquitetural acrescentou `template-schema`, `annotation-schema`, `field-schema`, `extraction-schema`, `evidence-schema` e `conference-schema` com contratos mínimos.

`variable-schema` permanece como compatibilidade. Novos consumidores devem usar `field-schema`, `extraction-schema` e `evidence-schema`; nenhuma remoção ocorrerá sem versão e migração explícitas.

JSON Schema continua sendo a fonte canônica, com Pydantic e TypeScript como espelhos quando existirem.

O layout real da Fase 2 (`*.schema.json`, `python/`, `typescript/`, `tests/`) foi preservado em vez de introduzir `src/` e metadata de publicação apenas nos packages novos. `pyproject.toml`/`package.json` serão adicionados quando houver estratégia de versionamento e publicação; hoje os packages são consumidos no monorepo.

Testes:

```bash
pip install -r packages/requirements-test.txt
pytest packages
```
