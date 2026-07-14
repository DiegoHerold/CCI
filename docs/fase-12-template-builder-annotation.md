# Fase 12 - Template Builder / Annotation

## Responsabilidade e limites

Esta fase adiciona o Template Builder visual para ensinar templates a partir de documentos com preview estruturado.

O `template-service` continua sendo o dono de templates, campos/objetos, annotations, sinais, regras tecnicas e versoes. O `document-service` continua sendo o dono de documentos e previews. O BFF apenas encaminha chamadas. A Web compoe o viewer existente com paineis de mapeamento.

Fora do escopo: extracao final, execucao real de `extraction_rules`, OCR, IA, normalizacao, Rule Builder contabil, Conference Service e Report Service.

## Backend

Endpoints novos no `template-service`:

```text
GET  /templates/{template_id}/builder-state
POST /templates/{template_id}/annotations/with-rule
PATCH /templates/{template_id}/annotations/{annotation_id}
```

`builder-state` agrega:

- template;
- versao ativa;
- versao draft;
- fields;
- annotations;
- extraction_rules;
- identification_signals.

`annotations/with-rule` cria uma annotation e, opcionalmente, uma regra tecnica ligada por `created_from_annotation_id`.

## Estrategias de regra sugeridas

```text
pdf_text_block/pdf_line -> find_near_label quando ha rotulo, fixed_bbox como fallback
pdf_area -> fixed_bbox
pdf_table_candidate -> pdf_area_table
excel_cell -> excel_cell_address
excel_column -> excel_column_by_header
excel_range/excel_table_candidate -> excel_range_table
```

As regras sao persistidas como configuracao tecnica. Elas nao sao executadas nesta fase.

## Frontend

Rotas adicionadas:

```text
/templates
/templates/{templateId}/builder?documentId={documentId}
```

Componentes principais:

- `TemplateBuilderPage`
- `FieldTree`
- `FieldEditor`
- `AnnotationPanel`
- `AnnotationList`
- `IdentificationSignalsPanel`
- `TemplateVersionPanel`

O builder usa `DocumentViewerShell` real da Fase 9 com painel lateral customizado. As annotations existentes viram highlights no documento por meio dos contratos de evidencias do viewer.

## Fluxo suportado

```text
abrir template
abrir documento com preview via documentId
selecionar bloco/area/tabela/celula/coluna/range
criar campo simples ou array como contas[]
associar selecao a campo
salvar annotation
gerar regra tecnica sugerida
cadastrar sinais de identificacao
criar draft
publicar versao
```

## Packages atualizados

- `packages/annotation-schema`: requests de annotation e annotation com regra.
- `packages/field-schema`: `FieldTreeNode`, requests de field e status de mapeamento.
- `packages/template-schema`: `ExtractionRule`, `TemplateBuilderState` e `TemplateBuilderSaveRequest`.
- `packages/shared-events`: `TemplateAnnotationUpdated`.

## Cliente, competencia, permissoes, evidencias e auditoria

Cliente e competencia seguem preservados no documento carregado pelo `document-service`.
Permissoes seguem o padrao atual da Web, usando `RequirePermission` e token Bearer pelo BFF.
Annotations preservam `document_id`, `source_preview_id`, selection payload e campo associado.
Auditoria de negocio completa continua futura; esta fase registra rastros tecnicos em annotations, extraction_rules, versoes e eventos do template-service.

## Testes

```bash
make template-test
make bff-test
cd apps/web && npm test -- TemplateBuilderPage
cd apps/web && npm run typecheck
make packages-test
```

Cobertura adicionada:

- builder-state;
- annotation com regra `find_near_label`;
- annotation Excel com regra `excel_column_by_header`;
- edicao basica de annotation;
- proxy BFF dos endpoints de builder;
- fluxo unitario Web de criar campo e salvar annotation.

## Limitacoes conhecidas

O builder nao executa regras e nao valida resultado de extracao. O endpoint legado de criar annotation continua sem validacao forte de existencia do documento para manter baixo acoplamento; o fluxo visual real parte de documento carregado pelo BFF/Document Service.
