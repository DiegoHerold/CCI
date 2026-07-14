# Fase 11 - Template Matching

## Responsabilidade e limites

O `template-service` agora possui o modulo interno `matching`, responsavel por gerar um perfil tecnico de documento, comparar esse perfil com templates ativos/publicados e registrar o melhor resultado de matching.

O template continua sendo o centro do motor de extracao. Categoria/tipo de documento e derivada do template vencedor, nao uma classificacao isolada.

Fora do escopo desta fase: extracao real de campos/objetos, OCR, IA, normalizacao, revisao de extracao, execucao de regras, conferencia e relatorios.

## Fluxo implementado

```text
document_id
-> DocumentServicePort.get_document
-> DocumentServicePort.get_preview
-> DocumentProfile
-> filtros de templates ativos/publicados por formato
-> scoring por identification_signals
-> ranking de candidatos
-> matched / not_found / ambiguous
-> persistencia de run e candidatos
-> evento de dominio via publisher abstrato/no-op
```

O modulo nao acessa tabelas do `document-service`; ele consome metadados e preview por porta/adaptador HTTP.

## Banco de dados

Migration criada:

```text
services/template-service/migrations/versions/0002_template_matching.py
```

Tabelas no schema `template`:

- `template.document_profiles`
- `template.template_matching_runs`
- `template.template_matching_candidates`

## Endpoints internos

```text
POST /template-matching/documents/{document_id}/match
GET  /template-matching/documents/{document_id}
GET  /template-matching/documents/{document_id}/runs
GET  /template-matching/runs/{matching_run_id}
POST /template-matching/documents/{document_id}/confirm
```

## Endpoints do BFF

```text
POST /api/v1/documents/{document_id}/template-match
GET  /api/v1/documents/{document_id}/template-match
GET  /api/v1/documents/{document_id}/template-match/runs
POST /api/v1/documents/{document_id}/template-match/confirm
```

O BFF apenas encaminha para o `template-service`; nao calcula score, nao decide template e nao acessa preview diretamente.

## DocumentProfile

O perfil persistido contem:

- `document_id`, `client_id`, `competence_id`
- `file_format`, `mime_type`, `original_filename`
- `page_count`, `sheet_count`, `requires_ocr`
- `text_sample`, `normalized_text_sample`
- `detected_keywords`, `detected_regex_patterns`
- `has_cnpj`, `has_dates`, `has_currency_values`, `has_tables`
- `structure_hints`
- `sheet_names`, `detected_headers`

PDF usa paginas, blocos, linhas, tabelas e `requires_ocr`.
Excel usa abas, celulas, cabecalhos detectados e tabelas candidatas.

## Scoring

Os sinais suportados sao:

```text
contains_text
contains_any_text
contains_all_text
not_contains_text
regex
file_format
sheet_name
column_header
table_header
page_count_range
has_cnpj
has_date
has_currency_values
structure_hint
```

Estrategia:

- sinal obrigatorio ausente elimina o candidato;
- sinal positivo encontrado soma peso;
- sinal negativo encontrado penaliza score;
- score final e normalizado entre `0.0` e `1.0`;
- candidatos e detalhes de score sao persistidos para auditoria tecnica.

Thresholds:

```env
TEMPLATE_MATCH_MIN_CONFIDENCE=0.75
TEMPLATE_MATCH_AUTO_ACCEPT_CONFIDENCE=0.90
TEMPLATE_MATCH_AMBIGUITY_DELTA=0.08
TEMPLATE_MATCH_MAX_CANDIDATES=10
```

Decisao:

- `matched`: melhor candidato acima do autoaceite e sem ambiguidade;
- `not_found`: nenhum candidato acima da confianca minima;
- `ambiguous`: candidatos proximos ou melhor candidato exigindo confirmacao;
- `failed`: reservado em contrato para falhas operacionais futuras.

## Eventos

Publisher real ainda nao foi ligado a RabbitMQ/NATS nesta fase; a abstracao/no-op existente foi mantida.

Eventos preparados:

- `TemplateMatched`
- `TemplateNotFound`
- `TemplateAmbiguous`
- `TemplateManuallyConfirmed`

## Packages atualizados

- `packages/template-schema`: contratos de `DocumentProfile`, request, candidato e resultado de matching.
- `packages/document-schema`: status `template_matched`, `template_not_found`, `template_ambiguous`.
- `packages/shared-events`: evento `TemplateManuallyConfirmed`.

## Cliente, competencia, permissoes, evidencias e auditoria

O `DocumentProfile` preserva `client_id` e `competence_id` vindos do `document-service`.
Permissoes continuam passando pelo Bearer token validado no `template-service`.
O matching nao cria evidencia de extracao final; ele preserva rastros tecnicos de decisao em `score_details`, candidatos e runs.
Auditoria de negocio completa fica para `conference-service`; esta fase gera historico tecnico de matching e eventos de dominio.

## Testes

```bash
make template-test
make bff-test
make packages-test
```

Cobertura adicionada:

- perfil PDF;
- perfil Excel;
- filtro por formato;
- ignorar template sem versao publicada;
- sinais `contains_text`, `contains_all_text`, `not_contains_text`, `sheet_name`, `column_header`, `has_cnpj`;
- score normalizado;
- `matched`, `not_found`, `ambiguous`;
- candidatos ranqueados;
- persistencia de runs e candidates;
- confirmacao manual;
- publisher abstrato;
- preview ausente;
- documento sem texto com `requires_ocr`.

## Limitacoes conhecidas

O `template-service` ainda nao atualiza status do documento diretamente para `template_matched`, `template_not_found` ou `template_ambiguous`; esses status foram adicionados ao contrato e devem ser aplicados futuramente via evento consumido pelo `document-service`.
