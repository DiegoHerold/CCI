# Fase 16 - Fluxo Guiado de Extracao, Template Builder e Review

Esta fase conecta o fluxo operacional entre documento, matching de template, criacao guiada de template, extracao, normalizacao e revisao humana de campos/objetos extraidos.

## Escopo

- `apps/web`: fluxo guiado por documento, builder guiado a partir de preview e tela de revisao de variaveis.
- `apps/bff`: agregacao de estado do fluxo do documento e proxies para revisao/correcao de campos.
- `template-service`: sugestoes heuristicas de template/campos/regras a partir de preview estruturado e preview de normalizacao por regra.
- `extraction-service`: correcao, aprovacao, rejeicao e aprovacao de resultados extraidos.
- `packages`: contratos de campos importantes, sugestoes de template, revisao de extracao e eventos de revisao.

## Fluxo implementado

```text
upload/preview do documento
-> estado guiado no BFF
-> matching de template
-> criacao guiada de template quando necessario
-> campos, extraction_rules, sinal de identificacao e versao publicada
-> retorno ao documento para reprocessar matching/extracao
-> resultado normalizado
-> review, correcao, aprovacao/rejeicao e evidencias
```

## Responsabilidades preservadas

- `document-service` continua dono do arquivo bruto, preview, status e metadados.
- `template-service` continua dono de templates, categorias, campos, regras tecnicas, sinais e matching.
- `extraction-service` continua dono de jobs, resultados, normalizacao, evidencias, confianca e revisao.
- `apps/bff` agrega estado para a Web sem acessar tabelas internas de servicos.
- `apps/web` apenas orquestra a experiencia e chama o BFF.

## Contratos e eventos

Contratos adicionados/estendidos:

- `field-schema`: flag `important` em campos reutilizaveis.
- `template-schema`: sugestoes de template/campos/arrays/regras e preview de normalizacao.
- `extraction-schema`: requests e historico de review/correcao.
- `shared-events`: `ExtractionFieldCorrected`, `ExtractionFieldApproved`, `ExtractionFieldRejected` e `ExtractionResultApproved`.

## Cliente, competencia, permissoes, evidencias e auditoria

O fluxo reutiliza os controles existentes de identidade e autorizacao entre BFF e servicos. Documento, matching, extracao e resultado continuam vinculados ao documento registrado, que preserva cliente e competencia. Toda variavel relevante mantem confianca, status e evidencia; correcoes/aprovacoes registram ator, data, motivo, valores anteriores e novos valores em tabela propria do `extraction-service`.

## Fora do escopo

- OCR Worker.
- AI Extraction Worker.
- Rule Builder contabil.
- Rule Worker.
- Conference Service.
- Report Service.
- Execucao de regras contabeis sobre os campos extraidos.

