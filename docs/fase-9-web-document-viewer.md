# Fase 9 — Web Document Viewer

Esta fase implementa o leitor visual de documentos no frontend, consumindo o preview estruturado gerado na Fase 8 pelo `document-service` e `parser-worker`.

O viewer prepara seleção visual reutilizável para fases futuras de anotações, Template Builder, evidências e revisão de extração. Ele não salva anotações no backend nesta fase.

## Arquitetura implementada

```text
apps/web
  /documents
    lista documentos reais retornados pelo BFF
  /documents/{documentId}
    carrega metadados e preview
    renderiza PDF ou Excel
    gera DocumentSelection local

apps/bff
  encaminha rotas /api/v1/documents/* para o Document Service

services/document-service
  segue dono de documentos, status e previews
```

## Rotas Web

```text
/documents
/documents/[documentId]
```

As rotas ficam dentro do layout protegido `src/app/(app)` e usam `RequirePermission` com a permissão já adotada para documentos nesta fase.

## Integração com BFF

O frontend consome:

```text
GET  /api/v1/documents
GET  /api/v1/documents/{document_id}
GET  /api/v1/documents/{document_id}/preview/status
GET  /api/v1/documents/{document_id}/preview
POST /api/v1/documents/{document_id}/preview
POST /api/v1/documents/{document_id}/preview/reprocess
```

Não há mock em runtime. Se não existir preview, a tela mostra estado próprio e permite solicitar geração pelo endpoint real.

## Viewer PDF

Renderiza a partir do JSON estruturado:

- página atual;
- dimensões e rotação;
- blocos de texto;
- linhas;
- tabelas candidatas;
- camada de destaque de evidências;
- seleção retangular por área;
- zoom e seletor de página.

Seleções geradas:

- `pdf_text_block`
- `pdf_line`
- `pdf_area`
- `pdf_table_candidate`

PDF sem camada de texto mostra estado `requires_ocr` e não executa OCR.

## Viewer Excel

Renderiza a partir do JSON estruturado:

- abas;
- grade de células;
- cabeçalhos detectados;
- células mescladas;
- tabelas candidatas;
- seleção de célula, coluna, linha e intervalo;
- destaque preparado para evidências por faixa de célula.

Para proteger a performance inicial, a grade limita a renderização visível e documenta a futura virtualização completa.

Seleções geradas:

- `excel_cell`
- `excel_column`
- `excel_row`
- `excel_range`
- `excel_table_candidate`

## Painel lateral

O painel mostra:

- tipo da seleção;
- texto ou célula quando aplicável;
- JSON completo da seleção;
- copiar JSON;
- limpar seleção.

## Contratos

`packages/document-schema` agora contém:

- `preview.schema.json`
- `selection.schema.json`

O frontend mantém tipos locais compatíveis em `features/document-viewer/types` até o package compartilhado ser consumido diretamente pela Web.

## Estados tratados

- `loading_document`
- `loading_preview`
- `preview_missing`
- `preview_pending`
- `preview_processing`
- `preview_ready`
- `preview_failed`
- `requires_ocr`
- `unsupported_format`
- `empty_preview`
- `error`

## Testes

Cobertura adicionada em:

```text
apps/web/src/features/document-viewer/components/DocumentViewerShell.test.tsx
```

Cobre renderização PDF, renderização Excel, seleção de bloco PDF, seleção de tabela PDF, evidência PDF, seleção de célula Excel, seleção de coluna Excel, seleção de intervalo Excel e estados principais.

## Fora do escopo

- Template Builder completo;
- salvar anotações no backend;
- Annotation Service;
- Template Matching;
- extração final;
- normalização;
- OCR;
- IA;
- Rule Builder;
- execução de regras.
