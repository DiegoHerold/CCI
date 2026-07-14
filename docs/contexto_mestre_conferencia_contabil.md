# Contexto Mestre do Projeto — Plataforma de Conferência Contábil Inteligente

## 1. Visão geral do projeto

A **Conferência Contábil Inteligente (CCI)** é uma plataforma distribuída para automatizar conferências contábeis por **cliente** e **competência**.

A ideia principal é:

1. O usuário acessa a plataforma.
2. O usuário só enxerga clientes e competências que tem permissão para acessar.
3. Um admin ou coordenador pode cadastrar usuários, convites, vínculos e permissões.
4. Para cada cliente, é configurado um modelo de conferência reutilizável.
5. Esse modelo define documentos esperados, templates esperados, regras associadas, agendamentos e reprocessamentos.
6. Na configuração inicial, o usuário adiciona documentos de exemplo.
7. O sistema gera preview estruturado, permite seleção visual, cria anotações, aplica templates e extrai campos/objetos.
8. Os valores extraídos são normalizados, guardam evidência, confiança, status e podem exigir revisão.
9. Depois que o modelo estiver pronto, as regras ficam salvas, versionadas e publicadas.
10. Nos meses seguintes, o usuário apenas informa ou confirma a pasta da competência.
11. O sistema importa documentos, identifica templates, extrai dados, executa regras, consolida resultado, gera auditoria, timeline e relatórios.
12. Se houver documento ausente, duplicado, ambíguo ou extração de baixa confiança, a conferência dependente pausa e pede confirmação humana.

A plataforma deve ser profissional, confiável, auditável, escalável e preparada para lidar com muitos arquivos, muitos templates, muitos campos/objetos e muitas conferências por cliente.

## 2. Conceito central

O sistema não é apenas um comparador de balancetes.

Ele é uma:

**Plataforma distribuída de conferência contábil baseada em arquivos, templates, extração estruturada, campos/objetos normalizados, regras versionadas, evidências, auditoria e relatórios.**

Fluxo central:

```text
Arquivo bruto
→ documento registrado
→ preview estruturado
→ template identificado
→ campos/objetos extraídos
→ valores normalizados e revisados
→ regras versionadas
→ conferência executada
→ resultado consolidado
→ auditoria e timeline
→ relatório
```

As regras nunca devem ler diretamente PDF, Excel, Word, TXT, imagem ou ZIP.

As regras consomem **campos/objetos extraídos**, com valor bruto, valor normalizado, tipo, evidência, confiança, status e versão do template usado. O termo histórico "variável" continua existindo em contratos antigos da Fase 2, mas a arquitetura alvo usa a linguagem **campo/objeto extraído com evidência**.

## 3. Filosofia da arquitetura

A plataforma deve seguir uma arquitetura distribuída por domínio, mas sem granularidade prematura.

Não queremos monólito.

Também não queremos criar um microserviço para cada etapa técnica cedo demais.

A decisão oficial é:

```text
Poucos serviços principais
→ módulos internos bem isolados
→ workers para tarefas pesadas
→ packages para contratos
→ infra Docker como base operacional
→ módulos preparados para extração futura
```

Regra de leitura:

```text
Serviço separa domínio.
Módulo separa responsabilidade interna.
Worker executa tarefa pesada.
Package compartilha contrato.
Evento integra domínios de forma desacoplada.
```

## 4. Estrutura alvo oficial

```text
cci/
├── apps/
│   ├── web-app/
│   └── bff/
│
├── services/
│   ├── identity-service/
│   ├── client-service/
│   ├── document-service/
│   ├── template-service/
│   ├── extraction-service/
│   ├── rule-service/
│   ├── conference-service/
│   └── report-service/
│
├── workers/
│   ├── parser-worker/
│   ├── pdf-extractor-worker/
│   ├── excel-extractor-worker/
│   ├── ocr-worker/
│   ├── ai-extraction-worker/
│   ├── rule-worker/
│   └── report-worker/
│
├── packages/
│   ├── shared-types/
│   ├── shared-events/
│   ├── shared-auth/
│   ├── document-schema/
│   ├── template-schema/
│   ├── annotation-schema/
│   ├── extraction-schema/
│   ├── evidence-schema/
│   ├── rule-schema/
│   └── rule-engine/
│
├── infra/
│   ├── docker/
│   ├── postgres/
│   ├── redis/
│   ├── rabbitmq/
│   ├── minio/
│   ├── temporal/
│   ├── gateway/
│   ├── observability/
│   └── scripts/
│
├── docs/
│   ├── architecture/
│   ├── phases/
│   ├── contracts/
│   └── decisions/
│
├── scripts/
├── docker-compose.yml
├── docker-compose.override.yml
├── .env.example
├── Makefile
└── README.md
```

O workspace atual ainda usa `apps/web` como caminho físico da Web App. Esse nome não precisa ser renomeado agora; ele representa logicamente `apps/web-app`.

Também existem scaffolds antigos em `services/` para a arquitetura granular anterior. Eles devem ser tratados como **legados ou placeholders históricos**, não como a lista oficial de serviços finais.

## 5. Tecnologias principais

### Apps

- Web App: Next.js, React, TypeScript, Tailwind, shadcn/ui e React Flow.
- BFF: FastAPI atual em `apps/bff`; NestJS continua aceitável como alternativa futura.
- A Web conversa somente com o BFF.
- O BFF agrega dados, propaga contexto, adapta respostas para frontend e não deve concentrar regra de negócio profunda.

### Serviços

- Preferencialmente FastAPI/Python.
- Cada serviço é dono de seu domínio e de seu schema.
- REST interno é aceitável como transição explícita.
- gRPC é o alvo para comunicação interna forte entre BFF e serviços.

### Banco, storage, workflow e eventos

- PostgreSQL: cluster inicial com schemas por domínio.
- MinIO agora; S3 futuramente.
- Temporal para workflows longos, retentativas e reprocessamentos.
- RabbitMQ ou NATS para eventos assíncronos oficiais.
- Redis para cache, locks, rate limit e estados transitórios.
- Observabilidade com OpenTelemetry, Sentry, Prometheus e Grafana.

## 6. Serviços e módulos internos

### 6.1 Identity Service

```text
identity-service/
├── modules/
│   ├── users/
│   ├── auth/
│   ├── roles/
│   ├── permissions/
│   ├── invitations/
│   └── sessions/
```

Responsabilidades:

- usuários;
- login;
- JWT;
- refresh token;
- roles;
- permissões;
- convite por e-mail;
- confirmação de senha;
- sessões.

Eventos importantes:

- `UserCreated`
- `UserInvited`
- `UserActivated`
- `UserDisabled`
- `RoleAssigned`

### 6.2 Client Service

```text
client-service/
├── modules/
│   ├── clients/
│   ├── competences/
│   ├── client_users/
│   ├── client_folders/
│   └── client_status/
```

Responsabilidades:

- clientes;
- CNPJ;
- competências;
- usuários vinculados ao cliente;
- permissões por cliente;
- pasta padrão;
- status da competência;
- organização da área de trabalho.

Eventos importantes:

- `ClientCreated`
- `CompetenceCreated`
- `CompetenceClosed`
- `ClientUserLinked`

O `client-service` já existe ou está em andamento e mantém esse nome físico. Não renomear automaticamente para `workspace-service`.

### 6.3 Document Service

```text
document-service/
├── modules/
│   ├── documents/
│   ├── uploads/
│   ├── storage/
│   ├── preview/
│   ├── parsing_jobs/
│   ├── duplicates/
│   └── document_status/
```

Responsabilidades:

- registrar documentos;
- upload manual;
- upload ZIP;
- metadados;
- hash;
- duplicidade;
- armazenamento no MinIO;
- vínculo com cliente e competência;
- status do documento;
- preview estruturado para frontend.

Preview PDF:

- páginas;
- textos;
- coordenadas;
- bbox;
- blocos;
- linhas;
- tabelas prováveis.

Preview Excel:

- abas;
- linhas;
- colunas;
- células;
- cabeçalhos;
- intervalos;
- células mescladas.

Eventos importantes:

- `DocumentUploaded`
- `DocumentStored`
- `DocumentPreviewRequested`
- `DocumentPreviewGenerated`
- `DocumentDuplicateDetected`

### 6.4 Template Service

```text
template-service/
├── modules/
│   ├── templates/
│   ├── categories/
│   ├── fields/
│   ├── annotations/
│   ├── extraction_rules/
│   ├── matching/
│   └── versions/
```

Responsabilidades:

- templates;
- categorias/tipos de documento;
- formatos aceitos;
- sinais de identificação;
- campos e objetos;
- anotações visuais;
- regras técnicas de extração;
- matching de templates;
- versionamento.

Decisão importante:

> O tipo de documento não é o centro da arquitetura. O tipo/categoria é uma classificação do template. O template é o centro do motor de extração.

Exemplo:

```text
Template: BALANCETE_DOMINIO_PDF_V1
Categoria: Balancete
Formato: PDF
Estrutura: Hierárquica
Campos:
- empresa.nome
- empresa.cnpj
- periodo.competencia
- contas[].codigo
- contas[].descricao
- contas[].saldo_atual
```

O módulo `annotations` representa seleções visuais feitas no frontend.

Exemplo PDF:

```text
page: 1
bbox: x, y, width, height
selected_text: "CNPJ: 00.000.000/0001-00"
field: empresa.cnpj
```

Exemplo Excel:

```text
sheet: Balancete
column: F
header: Saldo Atual
field: contas[].saldo_atual
```

Eventos importantes:

- `TemplateCreated`
- `TemplateVersionPublished`
- `TemplateMatched`
- `TemplateNotFound`
- `TemplateAmbiguous`
- `TemplateAnnotationCreated`

### 6.5 Extraction Service

```text
extraction-service/
├── modules/
│   ├── jobs/
│   ├── orchestration/
│   ├── results/
│   ├── evidence/
│   ├── normalization/
│   └── review/
```

Responsabilidades:

- criar jobs de extração;
- iniciar workflows no Temporal;
- chamar workers;
- aplicar templates;
- normalizar valores;
- salvar objetos extraídos;
- salvar evidências;
- controlar confiança;
- controlar status;
- permitir revisão e correção manual.

A extração deve salvar:

- objetos extraídos;
- campos;
- valor bruto;
- valor normalizado;
- tipo de dado;
- evidência;
- confiança;
- status;
- versão do template usado.

Eventos importantes:

- `ExtractionRequested`
- `ExtractionStarted`
- `ExtractionCompleted`
- `ExtractionFailed`
- `ExtractionReviewRequired`
- `ExtractionReviewed`

### 6.6 Rule Service

```text
rule-service/
├── modules/
│   ├── rules/
│   ├── dsl/
│   ├── operators/
│   ├── formulas/
│   ├── simulation/
│   └── versions/
```

Responsabilidades:

- regras de conferência;
- Rule DSL;
- operadores;
- fórmulas;
- blocos lógicos;
- validação;
- versionamento;
- publicação;
- simulação/debug.

O futuro **Web Rule Builder** deve ter:

- painel visual estilo canvas;
- campos/objetos como cards no lado esquerdo;
- canvas central com drag and drop;
- painel lateral com condições, comparações, blocos lógicos, fórmulas e equações;
- geração de JSON/DSL estruturado e executável;
- validação antes de publicar;
- simulação com dados reais.

Eventos importantes:

- `RuleCreated`
- `RulePublished`
- `RuleDisabled`
- `RuleSimulationCompleted`

### 6.7 Conference Service

```text
conference-service/
├── modules/
│   ├── models/
│   ├── executions/
│   ├── expected_documents/
│   ├── rule_sets/
│   ├── results/
│   ├── audit/
│   ├── timeline/
│   └── schedule/
```

Responsabilidades:

- modelos de conferência;
- documentos esperados;
- templates/categorias esperadas;
- regras associadas;
- execuções;
- filas;
- status;
- resultados consolidados;
- auditoria de negócio;
- timeline;
- agendamentos;
- reprocessamentos.

O Conference Service responde:

> A conferência dessa competência passou ou não passou?

Eventos importantes:

- `ConferenceStarted`
- `ConferenceCompleted`
- `ConferenceFailed`
- `ConferenceResultUpdated`
- `ConferenceAuditGenerated`

### 6.8 Report Service

```text
report-service/
├── modules/
│   ├── report_requests/
│   ├── pdf_reports/
│   ├── excel_reports/
│   ├── annotated_documents/
│   └── exports/
```

Responsabilidades:

- relatórios PDF;
- relatórios Excel;
- relatório final da conferência;
- documentos anotados;
- balancete anotado;
- exportações.

Eventos importantes:

- `ReportRequested`
- `ReportGenerated`
- `ReportFailed`

## 7. Workers

Workers não são serviços de negócio. Eles executam tarefas pesadas ou assíncronas.

```text
workers/
├── parser-worker/
├── pdf-extractor-worker/
├── excel-extractor-worker/
├── ocr-worker/
├── ai-extraction-worker/
├── rule-worker/
└── report-worker/
```

- `parser-worker`: gera preview estruturado. PDF vira texto, coordenadas, páginas, blocos e possíveis tabelas. Excel vira abas, células, colunas, cabeçalhos e intervalos.
- `pdf-extractor-worker`: aplica templates em PDFs.
- `excel-extractor-worker`: aplica templates em planilhas.
- `ocr-worker`: trata documentos escaneados, imagens e PDFs sem camada de texto.
- `ai-extraction-worker`: extração assistida por IA para casos difíceis. Sempre gera JSON estruturado, evidências, confiança e revisão obrigatória.
- `rule-worker`: executa regras publicadas usando objetos extraídos e normalizados.
- `report-worker`: gera relatórios pesados.

TXT, CSV, XML e Word entram como workers complementares em fase posterior; eles não definem a arquitetura principal.

## 8. Packages compartilhados

Packages centralizam contratos e bibliotecas puras. Eles não acessam banco, MinIO, RabbitMQ, Temporal ou APIs.

Packages alvo:

- `shared-types`
- `shared-events`
- `shared-auth`
- `document-schema`
- `template-schema`
- `annotation-schema`
- `extraction-schema`
- `evidence-schema`
- `rule-schema`
- `rule-engine`

Roadmap adicional:

- `field-schema`
- `conference-schema`

O package histórico `variable-schema` pertence ao estágio inicial de contratos e deve evoluir para o vocabulário de campos/objetos extraídos, evidências e revisão.

## 9. Infra

A pasta `infra/` é bloco oficial da arquitetura.

Estrutura esperada:

```text
infra/
├── docker/
├── postgres/
├── redis/
├── rabbitmq/
├── minio/
├── temporal/
├── gateway/
├── observability/
└── scripts/
```

Responsabilidades:

- `infra/docker`: Dockerfiles base, padrões de build e imagens comuns.
- `infra/postgres`: schemas, init scripts, migrations globais ou organização dos bancos/schemas por domínio.
- `infra/redis`: cache, locks, rate limit e estados temporários.
- `infra/rabbitmq`: exchanges, filas, bindings e definitions.
- `infra/minio`: buckets e policies.
- `infra/temporal`: namespaces, dynamic config e workflows esperados.
- `infra/gateway`: Nginx ou Traefik para roteamento local/futuro.
- `infra/observability`: OpenTelemetry, Prometheus, Grafana, Loki, Sentry ou estrutura futura.
- `infra/scripts`: inicialização, reset, buckets, schemas e bootstrap local.

Schemas PostgreSQL sugeridos:

```text
identity
client
document
template
extraction
rule
conference
report
```

Buckets MinIO sugeridos:

```text
cci-documents-original
cci-documents-preview
cci-extraction-artifacts
cci-reports
cci-temp
```

A estrutura física atual de `infra/` ainda está incompleta em relação ao alvo. Esta documentação define como ela deve ser entendida e evoluída, sem exigir reimplementação de containers nesta tarefa.

## 10. Módulos extraíveis no futuro

Decisão arquitetural:

> Os serviços serão criados como serviços modulares extraíveis.

Isso significa:

- hoje um módulo roda dentro de um serviço maior;
- amanhã, se crescer demais, pode virar serviço próprio;
- para isso, cada módulo deve ter contrato público, eventos próprios, testes próprios e baixo acoplamento.

Estrutura recomendada para módulos grandes:

```text
module/
├── public/
│   ├── commands.py
│   ├── queries.py
│   ├── responses.py
│   └── events.py
│
├── domain/
│   ├── entities.py
│   ├── value_objects.py
│   └── errors.py
│
├── application/
│   ├── use_cases.py
│   ├── service.py
│   └── ports.py
│
├── infrastructure/
│   ├── repository.py
│   ├── local_adapters.py
│   └── external_clients.py
│
├── api/
│   └── routes.py
│
└── tests/
```

Regra obrigatória:

> Um módulo não deve acessar diretamente banco/repository interno de outro módulo se esse módulo puder virar serviço no futuro. Use portas/interfaces/adapters.

Errado:

```python
from modules.templates.repository import TemplateRepository
```

Melhor:

```python
from modules.matching.application.ports import TemplateCatalogPort
```

Hoje a implementação pode ser local. No futuro pode virar HTTP, gRPC ou evento.

## 11. Nova ordem das fases

```text
Fase 1A — Chão técnico
Docker Compose, PostgreSQL, Redis, RabbitMQ, MinIO, Temporal, estrutura de pastas, .env, README e Makefile.

Fase 1B — Base padrão dos serviços
Template FastAPI, healthcheck, ready, config, logs, correlation_id e conexão básica.

Fase 2 — Packages compartilhados
shared-types, shared-events, shared-auth, document-schema, template-schema, annotation-schema, extraction-schema, evidence-schema, field-schema, rule-schema, conference-schema e rule-engine inicial.

Fase 3 — BFF inicial
Porta de entrada da plataforma para a web conversar com os serviços.

Fase 4 — Identity Service
Usuários, login, JWT, roles, permissões, convites e confirmação de senha.

Fase 5 — Web inicial
Next.js, layout, login, sessão, rotas protegidas, dashboard e navegação principal.

Fase 6 — Client Service
Clientes, CNPJ, competências, usuários vinculados ao cliente, permissões por cliente e pasta padrão.

Fase 7 — Document Service
Upload, ZIP, metadados, hash, duplicidade, MinIO, vínculo cliente/competência e status do documento.

Fase 8 — Parser Worker e Preview
Parser de PDF/Excel e geração de modelo selecionável: páginas, textos, coordenadas, células, blocos e tabelas.

Fase 9 — Web Document Viewer
Leitor PDF/Excel no frontend, seleção de texto, célula, coluna, área, tabela e destaque de evidências.

Fase 10 — Template Service
Templates, categorias/tipos, formatos, campos, objetos, sinais de identificação, regras de extração, anotações e versionamento.

Fase 11 — Template Matching
Gerar perfil do documento, filtrar templates, ranquear candidatos, escolher template vencedor ou sinalizar template não encontrado/ambíguo.

Fase 12 — Template Builder / Annotation
Criar templates visualmente selecionando textos, células, colunas e tabelas, associando seleções a campos/objetos e gerando regras reutilizáveis.

Fase 13 — Extraction Service
Jobs de extração, Temporal, status, retries, aplicação de templates e chamada dos workers.

Fase 14 — Extractor Workers básicos
PDF e Excel aplicando templates para extrair objetos, campos, tabelas e hierarquias.

Fase 15 — Normalização e Resultados da Extração
Normalizar valores, datas, CNPJ, contas e salvar objetos extraídos, evidências, confiança e status.

Fase 16 — Web Extraction Review
Cards de campos/objetos, evidências destacadas, correção manual, aprovação e reprocessamento.

Fase 17 — Rule DSL
Estrutura interna das regras: campos, operadores, condições, fórmulas, blocos lógicos, mensagens e severidade.

Fase 18 — Web Rule Builder
Canvas visual com cards de variáveis/objetos, drag and drop, blocos lógicos, condições, comparações, fórmulas e equações.

Fase 19 — Rule Service
Salvar, validar, versionar, ativar, publicar e desativar regras.

Fase 20 — Rule Simulator
Testar regras com dados reais, mostrando cálculos, caminho lógico, campos usados, divergências e evidências.

Fase 21 — Conference Service
Modelos de conferência, documentos esperados, templates esperados, regras associadas, execuções, fila, status e resultado consolidado.

Fase 22 — Rule Worker
Executar regras usando objetos extraídos e valores normalizados.

Fase 23 — Results, Audit e Timeline
Resultados consolidados, diferenças, criticidade, explicação de negócio, timeline e eventos para o frontend.

Fase 24 — Report Service / Report Worker
Relatórios PDF, Excel, documentos anotados, balancete anotado e geração pesada de arquivos.

Fase 25 — Agendamentos e reprocessamentos
Execuções mensais, pasta pronta, reprocessamentos automáticos e rotinas recorrentes.

Fase 26 — Agente Local
Monitorar pastas locais/rede e enviar arquivos para a plataforma.

Fase 27 — Workers complementares
TXT, CSV, XML, Word e melhorias nos extratores.

Fase 28 — OCR Worker
Documentos escaneados, imagens e PDFs sem camada de texto.

Fase 29 — AI Extraction Worker
Extração assistida por IA para documentos difíceis, sempre com JSON estruturado, evidências, confiança e revisão.

Fase 30 — Observabilidade completa
OpenTelemetry, Sentry, Prometheus, Grafana, métricas, tracing e alertas.

Fase 31 — Testes e qualidade
Testes unitários, integração, contratos, workflows, parsers, templates, extração, evidências, regras e regressão.

Fase 32 — CI/CD
Pipeline de build, testes, migrations, deploy e versionamento.

Fase 33 — Produção
Ambiente real, backups, segurança, permissões, monitoramento e documentação final.
```

## 12. Regras arquiteturais que a IA deve respeitar

1. Não transformar o projeto em monólito.
2. Não criar serviço separado para cada etapa técnica cedo demais.
3. Criar poucos serviços principais, com módulos internos bem definidos.
4. Módulos internos devem ser extraíveis no futuro.
5. Um serviço não acessa diretamente tabelas internas de outro serviço.
6. BFF agrega dados para o frontend, não contém regra de negócio profunda.
7. Workers executam tarefas pesadas ou assíncronas.
8. `document-service` é dono dos arquivos e previews.
9. `template-service` é dono dos templates, anotações, campos e matching.
10. `extraction-service` é dono dos jobs, resultados, evidências, normalização e revisão.
11. `rule-service` é dono da DSL, regras, operadores, fórmulas, simulação e versionamento.
12. `conference-service` é dono da execução de conferência, resultados, auditoria, timeline e agendamentos.
13. `report-service` é dono dos relatórios e exportações.
14. Infra deve permitir subir o ambiente com Docker.
15. Tipo de documento é categoria do template, não o centro do motor.
16. Template é o centro do motor de extração.
17. Campos/objetos extraídos substituem a ideia antiga de um catálogo separado de variáveis.
18. Anotações visuais no frontend devem poder virar regras reutilizáveis de template.
19. Regras no frontend devem futuramente ser criadas em canvas visual com cards, blocos lógicos, fórmulas e condições.
20. IA auxilia extração, mas sempre com JSON estruturado, evidência, confiança e revisão obrigatória.
21. Sempre pensar em cliente, competência, permissões, evidências e auditoria.

## 13. Frase guia do projeto

```text
Configura uma vez por cliente.
Todo mês importa ou detecta a pasta da competência.
O sistema identifica documentos, aplica templates, extrai e normaliza campos/objetos, executa regras salvas, gera evidências, auditoria, timeline e relatórios.
```

Mentalidade:

```text
Apps dão a experiência.
BFF protege e agrega.
Services são domínios.
Modules separam responsabilidades internas.
Workers executam peso.
Packages padronizam contratos.
Infra sustenta tudo.
Auditoria gera confiança.
```
