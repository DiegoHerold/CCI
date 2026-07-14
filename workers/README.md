# Workers

Workers executam tarefas pesadas ou assíncronas iniciadas por serviços e workflows. Eles não são serviços de negócio e não devem concentrar domínio próprio.

## Workers canônicos

- `parser-worker`: gera preview estruturado de PDF/Excel para seleção visual no frontend.
- `pdf-extractor-worker`: aplica templates em PDFs.
- `excel-extractor-worker`: aplica templates em planilhas.
- `ocr-worker`: processa documentos escaneados, imagens e PDFs sem camada de texto.
- `ai-extraction-worker`: extrai casos difíceis com JSON estruturado, evidência, confiança e revisão obrigatória.
- `rule-worker`: executa regras publicadas usando objetos extraídos e valores normalizados.
- `report-worker`: gera relatórios pesados.

`word-extractor-worker` e `txt-extractor-worker` existem como scaffolds históricos/complementares e se encaixam na Fase 27, junto com TXT, CSV, XML, Word e melhorias nos extratores. Eles não alteram a lista principal de workers da arquitetura atual.
