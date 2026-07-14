# Document Schema

Contratos de documento, metadata, status, upload/storage, preview estruturado e seleção visual. `preview.schema.json` define `ParsedDocumentPreview`, `PdfDocumentPreview`, blocos/linhas/tokens com `bbox`, e `ExcelDocumentPreview` com abas, células, mesclagens, cabeçalhos e candidatos de tabela. `selection.schema.json` define `DocumentSelection` e `EvidenceHighlight` usados pelo Web Document Viewer.

Contrato canônico dos arquivos importados e das evidências localizadas neles. O JSON Schema governa IDs, vínculo com cliente/competência, integridade, storage, classificação, status e metadados.

Será usado por ingestão, classificação, extração, variável e auditoria. Os espelhos Pydantic e TypeScript não armazenam nem processam arquivos; não há MinIO, upload ou classificação real neste package.

Veja `examples/document.example.json` e `examples/evidence.example.json`.
