# Excel Extractor Worker

Worker técnico da CCI para aplicar templates publicados em previews estruturados de planilhas.

Responsabilidades nesta fase:

- receber `ExtractorWorkerInput` com documento, preview, template e regras técnicas;
- usar `preview_json` quando enviado no payload ou carregar preview JSON do MinIO;
- executar estratégias básicas de Excel;
- devolver `raw_extracted_fields`, `raw_extracted_objects`, warnings, errors e evidências.

Estratégias suportadas:

- `excel_cell_address`
- `excel_column_by_header`
- `excel_range_table`
- `excel_sheet_by_name`

Estratégias preparadas, mas ainda não executadas nesta fase:

- `excel_named_range`
- `excel_header_row_detection`
- `excel_hierarchical_rows`

O worker não acessa banco, não busca templates/documentos diretamente nos serviços de domínio e não executa macros ou fórmulas.
