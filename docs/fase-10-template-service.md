# Fase 10 — Template Service

## Responsabilidade e limites

O `template-service` é o serviço canônico responsável por categorias, templates,
campos/objetos esperados, sinais de identificação, anotações visuais, regras
técnicas de extração e versionamento de templates.

O template é o centro do motor de extração. Categoria/tipo de documento é apenas
classificação organizacional. Esta fase não implementa matching automático,
ranking, extração real, OCR, IA, normalização, execução de regra contábil,
conferência ou Template Builder visual.

## Módulos internos

- `categories`: categorias/tipos de documento, com slug único e inativação futura.
- `templates`: entidade principal, formato, estrutura, status e versão ativa.
- `fields`: definições de campos/objetos esperados pelo template, incluindo listas dinâmicas como `contas[]`.
- `identification_signals`: sinais cadastrados para matching futuro.
- `annotations`: seleções visuais vindas do Web Document Viewer.
- `extraction_rules`: estratégias técnicas que serão consumidas futuramente pelos extractor workers.
- `versions`: versões draft/published/archived com snapshot rastreável.

## Banco de dados

A migration `services/template-service/migrations/versions/0001_template_domain.py`
cria o schema `template` e as tabelas:

- `template.categories`
- `template.templates`
- `template.template_versions`
- `template.template_fields`
- `template.identification_signals`
- `template.template_annotations`
- `template.extraction_rules`

O ledger Alembic é isolado em `template.alembic_version_template`.

## Endpoints internos

```text
GET  /health
GET  /ready
POST /template-categories
GET  /template-categories
GET  /template-categories/{category_id}
POST /templates
GET  /templates
GET  /templates/{template_id}
PATCH /templates/{template_id}
PATCH /templates/{template_id}/status
POST /templates/{template_id}/fields
GET  /templates/{template_id}/fields
PATCH /templates/{template_id}/fields/{field_id}
DELETE /templates/{template_id}/fields/{field_id}
POST /templates/{template_id}/identification-signals
GET  /templates/{template_id}/identification-signals
PATCH /templates/{template_id}/identification-signals/{signal_id}
DELETE /templates/{template_id}/identification-signals/{signal_id}
POST /templates/{template_id}/annotations
GET  /templates/{template_id}/annotations
GET  /templates/{template_id}/annotations/{annotation_id}
DELETE /templates/{template_id}/annotations/{annotation_id}
POST /templates/{template_id}/extraction-rules
GET  /templates/{template_id}/extraction-rules
PATCH /templates/{template_id}/extraction-rules/{rule_id}
DELETE /templates/{template_id}/extraction-rules/{rule_id}
POST /templates/{template_id}/versions
GET  /templates/{template_id}/versions
GET  /templates/{template_id}/versions/{version_id}
POST /templates/{template_id}/versions/{version_id}/publish
POST /templates/{template_id}/versions/{version_id}/archive
```

No BFF, as rotas ficam sob `/api/v1` e são apenas encaminhadas ao serviço.

## Eventos

O publisher ainda é abstrato/no-op, sem RabbitMQ real nesta fase. Eventos
preparados:

- `TemplateCategoryCreated`
- `TemplateCreated`
- `TemplateUpdated`
- `TemplateFieldCreated`
- `TemplateIdentificationSignalCreated`
- `TemplateAnnotationCreated`
- `TemplateExtractionRuleCreated`
- `TemplateVersionCreated`
- `TemplateVersionPublished`
- `TemplateArchived`

O contrato `TemplateVersionPublished` foi adicionado em
`packages/shared-events/schemas/template-version-published.schema.json`.

## Packages atualizados

- `packages/template-schema`: templates, categorias, versões, sinais e estratégias.
- `packages/field-schema`: `FieldDefinition`, objetos, arrays, tabelas e `FieldCard`.
- `packages/annotation-schema`: anotações visuais de PDF/Excel.
- `packages/shared-events`: eventos do domínio de template.

## Segurança e limites de domínio

Todas as rotas do serviço exigem Bearer token validado no `identity-service`.
Permissões específicas de template ainda não foram adicionadas ao contrato RBAC;
por isso esta fase aplica autenticação, mas não inventa permissões novas.

O serviço referencia `document_id` e `source_preview_id`, mas não acessa tabelas
do `document-service`. O adapter HTTP está preparado para validação futura de
documento/preview; a validação forte não foi ativada nesta fase para evitar
acoplamento e porque o contrato de seleção ainda está amadurecendo a partir da
Fase 9.

`selection_payload` e `config` têm limite configurável em KB. Regras técnicas
e regex não são executadas nesta fase.

## Variáveis

```env
TEMPLATE_SERVICE_URL=http://template-service:8120
TEMPLATE_SERVICE_PORT=8120
TEMPLATE_DATABASE_SCHEMA=template
TEMPLATE_MAX_SELECTION_PAYLOAD_KB=256
TEMPLATE_MAX_RULE_CONFIG_KB=128
```

## Testes e operação

```bash
make template-migrate
make template-test
make bff-test
pytest packages
docker compose up -d --build template-service bff
```

`template-test` usa PostgreSQL real no perfil `test`, não SQLite ou mocks de
persistência. Os testes cobrem criação/listagem de categoria, slug duplicado,
template, fields simples e arrays, field path duplicado, sinais, anotações PDF e
Excel, regras técnicas, versionamento, publicação, snapshot, imutabilidade de
versão publicada e publisher no-op.

## Fora do escopo

Template Matching automático, extração real de documentos, OCR, IA,
normalização, revisão de extração, Rule Builder, execução de regras contábeis,
conferência, relatórios e telas completas de Template Builder ficam para fases
posteriores.
