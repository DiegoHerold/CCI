# Contexto Mestre do Projeto — Plataforma de Conferência Contábil Inteligente

## 1. Visão geral do projeto

Estou construindo uma plataforma chamada **Conferência Contábil Inteligente**.

O objetivo da plataforma é permitir que escritórios contábeis façam conferência automatizada de arquivos contábeis por **cliente** e **competência**.

A ideia principal é:

1. O usuário acessa a plataforma.
2. O usuário só enxerga os clientes que tem permissão para acessar.
3. Um admin ou coordenador pode cadastrar usuários e definir permissões.
4. Para cada cliente, será criado um modelo de conferência.
5. Esse modelo terá documentos esperados, critérios de identificação, regras, agendamentos e configurações.
6. Na primeira configuração, o usuário adiciona documentos de exemplo.
7. O sistema extrai os dados, normaliza, transforma em variáveis e permite criar regras.
8. Depois que o modelo estiver pronto, as regras ficam salvas e versionadas.
9. Nos meses seguintes, o usuário apenas informa ou confirma a pasta da competência.
10. O sistema importa os documentos, identifica os arquivos, extrai dados, normaliza variáveis, executa as regras salvas, gera logs, auditoria e relatório.
11. Se houver documento ausente, duplicado ou ambíguo, o sistema deve pausar e pedir confirmação do usuário.
12. O sistema deve gerar relatório em PDF, Excel e também um balancete anotado com status visual das conferências.

A plataforma deve ser profissional, confiável, auditável, escalável e preparada para lidar com muitos arquivos, muitas variáveis e muitas conferências por cliente.

---

## 2. Conceito central

O sistema não é apenas um comparador de balancetes.

Ele é uma:

**Plataforma distribuída de conferência contábil baseada em arquivos, extração estruturada, variáveis normalizadas, regras versionadas, execução automatizada, logs, auditoria e relatórios.**

O núcleo do sistema é:

```text
Arquivo bruto
→ documento identificado
→ dados extraídos
→ dados normalizados
→ variáveis
→ regras
→ execução
→ resultado
→ auditoria
→ relatório
```

As regras nunca devem ler diretamente PDF, Excel, Word ou TXT.

As regras devem consumir **variáveis normalizadas e confirmadas** pelo `variable-registry-service`.

---

## 3. Filosofia da arquitetura

A plataforma deve seguir uma arquitetura distribuída por domínio.

Não quero monolito.

Também não quero uma estrutura improvisada que precise ser refeita depois.

A estrutura será construída serviço por serviço, devagar, mas já respeitando a arquitetura final desde o início.

A separação principal é:

```text
Control Plane = organiza a conferência
Data Plane = processa a conferência
Workers = executam tarefas pesadas
Packages = padronizam contratos
Infra = sustenta a plataforma
```

---

## 4. Estrutura de diretórios escolhida

```text
apps/
  web/
  bff/

services/
  identity-service/
  client-service/
  conference-model-service/
  schedule-service/
  document-ingestion-service/
  document-classification-service/
  extraction-orchestrator/
  normalization-service/
  variable-registry-service/
  rule-service/
  execution-control-service/
  result-service/
  audit-service/
  report-service/
  log-service/

workers/
  pdf-extractor-worker/
  excel-extractor-worker/
  word-extractor-worker/
  txt-extractor-worker/
  ocr-worker/
  ai-extraction-worker/
  rule-worker/
  report-worker/

packages/
  shared-types/
  shared-events/
  shared-auth/
  variable-schema/
  rule-schema/
  document-schema/
  rule-engine/

infra/
  postgres/
  minio/
  temporal/
  rabbitmq-ou-nats/
  redis/
  observability/
```

---

## 5. Tecnologias principais

### Frontend

```text
Next.js
React
TypeScript
Tailwind
shadcn/ui
React Flow
```

O frontend fica em:

```text
apps/web
```

Ele deve ser responsável por:

- login;
- dashboard;
- clientes;
- competências;
- importação de arquivos;
- mapa de documentos;
- visualização dos documentos;
- variáveis;
- regras visuais;
- execução;
- logs em tempo real;
- auditoria;
- relatórios.

---

### BFF / API Gateway

```text
NestJS ou FastAPI
```

O BFF fica em:

```text
apps/bff
```

O frontend deve conversar apenas com o BFF.

O BFF deve:

- autenticar requisições;
- validar permissões;
- chamar serviços internos;
- juntar dados de vários serviços;
- devolver respostas prontas para a tela;
- esconder a complexidade do backend.

---

### Serviços backend

Preferencialmente:

```text
FastAPI Python
```

Cada serviço deve ter responsabilidade clara e ser dono do próprio domínio.

---

### Banco de dados

```text
PostgreSQL
```

No início, pode ser um cluster PostgreSQL com schemas por domínio:

```text
auth
core
models
documents
extraction
variables
rules
execution
audit
reports
logs
```

Cada serviço deve ser dono do seu schema/domínio.

Um serviço não deve acessar diretamente as tabelas internas de outro serviço.

---

### Storage

```text
MinIO no início
S3 no futuro
```

Usado para:

- arquivos originais;
- arquivos processados;
- relatórios;
- Excel exportado;
- PDF exportado;
- balancete anotado;
- evidências visuais.

---

### Workflows

```text
Temporal
```

Usado para processos longos e confiáveis:

- extração de documentos;
- OCR;
- IA;
- execução de conferências;
- geração de relatório;
- reprocessamentos;
- retentativas;
- workflows que podem demorar minutos ou horas.

---

### Event Bus

```text
RabbitMQ ou NATS
```

Usado para comunicação assíncrona entre serviços.

Eventos importantes:

```text
file.imported
document.classified
document.ambiguous
document.missing
document.confirmed
extraction.started
raw.extracted
variables.normalized
variables.ready
variables.need_review
schedule.due
execution.started
rule.executed
result.created
divergence.found
execution.finished
audit.created
report.generated
log.created
```

---

### Cache e status temporário

```text
Redis
```

Usado para:

- cache;
- status temporário;
- progresso de execução;
- sessões rápidas;
- locks simples;
- dados transitórios para logs em tempo real.

---

### Observabilidade

```text
OpenTelemetry
Sentry
Prometheus
Grafana
```

Desde o início, todo serviço deve ter:

- logs estruturados;
- `trace_id`;
- `correlation_id`;
- métricas;
- tratamento de erro;
- healthcheck.

---

## 6. Comunicação entre componentes

### Frontend → BFF

Usar:

```text
REST/HTTPS
```

Para:

- abrir telas;
- listar clientes;
- criar usuários;
- criar competências;
- iniciar importação;
- iniciar execução;
- buscar resultados;
- baixar relatórios.

---

### Logs/status em tempo real

Usar:

```text
SSE ou WebSocket
```

Para:

- logs da execução;
- progresso da extração;
- progresso das conferências;
- notificações de pendência;
- notificações de erro;
- status em tempo real.

Preferência inicial:

```text
SSE para logs/status enviados do servidor para o frontend.
WebSocket somente se precisar de comunicação bidirecional mais forte.
```

---

### BFF → Serviços internos

Usar:

```text
gRPC interno
```

Motivo:

- comunicação rápida;
- contratos fortes;
- melhor para serviço-para-serviço;
- menos ambiguidade entre domínios.

Se algum serviço ainda estiver em fase inicial, REST interno pode ser usado temporariamente, mas a arquitetura alvo é gRPC.

---

### Serviços → Processos pesados

Usar:

```text
Temporal + Workers
```

Nunca processar PDF pesado, OCR, IA, execução de 100 conferências ou relatório pesado diretamente em uma request HTTP.

Fluxo correto:

```text
Frontend chama BFF
BFF chama serviço responsável
Serviço cria execução
Temporal inicia workflow
Workers processam
Eventos são publicados
Log Service envia status para a tela
```

---

### Comunicação assíncrona entre serviços

Usar:

```text
RabbitMQ ou NATS
```

Para eventos de domínio.

Exemplo:

```text
document-ingestion-service publica file.imported
document-classification-service consome file.imported
document-classification-service publica document.classified
extraction-orchestrator consome document.confirmed
normalization-service consome raw.extracted
variable-registry-service consome variables.normalized
execution-control-service consome schedule.due ou variables.ready
result-service consome rule.executed
audit-service consome result.created
report-service consome execution.finished
log-service consome eventos relevantes
```

---

## 7. Responsabilidade de cada serviço

### `identity-service`

Responsável por:

- usuários;
- login;
- sessões;
- roles;
- permissões globais;
- permissões por cliente.

Deve responder perguntas como:

```text
Este usuário pode acessar este cliente?
Este usuário pode criar outro usuário?
Este usuário pode editar regra?
Este usuário pode executar conferência?
Este usuário pode visualizar relatório?
```

Perfis previstos:

```text
Admin
Coordenador
Analista
Revisor
Somente leitura
```

---

### `client-service`

Responsável por:

- clientes;
- CNPJ;
- competências;
- status da competência;
- usuários vinculados ao cliente;
- pasta padrão do cliente;
- dados principais do cliente.

Exemplo de competência:

```text
Cliente: Empresa X
Competência: 05/2026
Status: aguardando documentos
```

---

### `conference-model-service`

Responsável por:

- modelos de conferência por cliente;
- documentos esperados;
- critérios de identificação;
- grupos de conferência;
- configurações do modelo;
- versões do modelo;
- modelo ativo do cliente.

Exemplo:

```text
Cliente: Empresa X
Modelo: Conferência Mensal Completa
Documentos esperados:
  - Balancete
  - Guia INSS
  - Guia FGTS
  - Folha
  - Relatório Fiscal
```

Esse serviço é essencial porque a ideia é configurar uma vez e reutilizar todo mês.

---

### `schedule-service`

Responsável por:

- agendamentos;
- execução mensal automática;
- execução por pasta pronta;
- reprocessamentos agendados;
- próximas execuções;
- disparos automáticos.

Ele não executa conferências diretamente.

Ele publica eventos como:

```text
schedule.due
folder.ready
```

Quem executa é o `execution-control-service`.

---

### `document-ingestion-service`

Responsável por:

- upload manual;
- upload de ZIP;
- importação de pasta;
- recebimento de arquivos vindos do agente local;
- hash do arquivo;
- metadados;
- arquivo bruto imutável;
- vínculo com cliente e competência;
- armazenamento no MinIO/S3.

Não deve fazer extração profunda.

Ele apenas registra e armazena os arquivos.

---

### `document-classification-service`

Responsável por:

- identificar tipo do documento;
- comparar com documentos esperados;
- calcular confiança;
- detectar duplicidade;
- detectar ausência;
- detectar ambiguidade;
- montar mapa de documentos da competência.

Exemplo:

```text
Foram encontrados 2 possíveis balancetes:
1. balancete_preliminar_05_2026.pdf
2. balancete_final_05_2026.pdf

Sistema recomenda o final, mas o usuário precisa confirmar.
```

Se um documento obrigatório não for encontrado, o sistema deve pausar as conferências dependentes.

---

### `extraction-orchestrator`

Responsável por:

- receber documentos confirmados;
- decidir quais workers usar;
- iniciar workflows no Temporal;
- acompanhar status da extração;
- controlar falhas e reprocessamentos;
- coordenar PDF, Excel, Word, TXT, OCR e IA.

Ele não deve conter toda a lógica de extração.

Ele orquestra os workers.

---

### `normalization-service`

Responsável por transformar dados brutos em dados padronizados.

Exemplos:

```text
"R$ 3.500,00" → 3500.00
"05/2026" → 2026-05
"00.000.000/0001-00" → CNPJ normalizado
"2.01.03.001" → código contábil normalizado
```

Ele deve gerar dados prontos para virar variáveis.

---

### `variable-registry-service`

Responsável pelo catálogo central de variáveis.

Guarda:

- variáveis brutas;
- variáveis normalizadas;
- variáveis confirmadas;
- variáveis corrigidas;
- variáveis ignoradas;
- evidências;
- status de revisão;
- origem da variável;
- confiança;
- se a variável é usada em alguma regra.

Exemplo de variável:

```json
{
  "key": "guia_inss.valor_total",
  "value": 3500.00,
  "type": "currency",
  "status": "confirmed",
  "confidence": 0.96,
  "evidence": {
    "document_id": "doc_123",
    "page": 1,
    "text": "Valor Total R$ 3.500,00"
  }
}
```

As regras devem depender deste serviço.

---

### `rule-service`

Responsável por:

- criação de regras;
- edição;
- versionamento;
- validação;
- teste;
- ativação;
- inativação.

As regras podem ser:

- comparação;
- fórmula;
- condição;
- existência;
- agrupamento;
- regra composta.

Exemplo de regra:

```json
{
  "name": "Conferir INSS",
  "version": 1,
  "logic": {
    "operator": "equals",
    "left": "balancete.conta.2.01.03.001.saldo_atual",
    "right": "guia_inss.valor_total",
    "tolerance": 0.01
  }
}
```

Nunca sobrescrever regras antigas.

Sempre criar nova versão.

---

### `execution-control-service`

Responsável por:

- iniciar execução manual;
- iniciar execução agendada;
- executar pendentes;
- reprocessar divergentes;
- montar fila de conferências;
- iniciar workflow no Temporal;
- controlar status geral da execução.

Ele não executa regra diretamente.

Ele chama workflows e workers.

---

### `result-service`

Responsável por:

- salvar resultados;
- consolidar status;
- armazenar valores comparados;
- armazenar diferença;
- armazenar criticidade;
- armazenar mensagem do resultado.

Status possíveis:

```text
aprovado
divergente
erro
pendente
não aplicável
revisão necessária
```

---

### `audit-service`

Responsável pela explicação de negócio.

Deve responder:

```text
Qual regra rodou?
Qual versão da regra?
Quais documentos foram usados?
Quais variáveis foram usadas?
Qual valor foi comparado?
Qual diferença foi encontrada?
Qual evidência sustenta o resultado?
Quem executou?
Quando executou?
```

Auditoria não é log técnico.

Auditoria é explicação confiável para usuário contábil.

---

### `report-service`

Responsável por:

- relatório PDF;
- resultado Excel;
- balancete anotado;
- relatório por competência;
- relatório por cliente;
- exportação da auditoria.

Usa `report-worker` para geração pesada.

---

### `log-service`

Responsável por:

- logs de negócio;
- logs técnicos;
- linha do tempo da execução;
- envio de logs/status para o frontend via SSE/WebSocket.

Logs de negócio devem ser claros para usuário comum.

Exemplo:

```text
Iniciando conferência da competência 05/2026.
Balancete identificado.
148 contas extraídas.
Executando regra INSS.
Comparando saldo do balancete com valor da guia.
Conferência aprovada.
```

Logs técnicos devem conter:

```text
trace_id
workflow_id
worker
erro
stack trace
tempo de execução
```

---

## 8. Workers

Workers são responsáveis por processamento pesado.

Eles devem receber uma tarefa, processar e devolver resultado.

Não devem ser donos de regra de negócio principal.

### `pdf-extractor-worker`

Usa:

```text
Docling
pdfplumber
PyMuPDF
```

Extrai:

- texto;
- páginas;
- tabelas;
- blocos;
- posições;
- valores.

---

### `excel-extractor-worker`

Usa:

```text
openpyxl
pandas
```

Extrai:

- abas;
- células;
- fórmulas;
- tabelas;
- linhas;
- colunas;
- valores.

---

### `word-extractor-worker`

Extrai:

- parágrafos;
- tabelas;
- texto;
- estrutura do documento.

---

### `txt-extractor-worker`

Extrai:

- linhas;
- blocos de texto;
- valores;
- datas;
- códigos;
- padrões textuais.

---

### `ocr-worker`

Usado para documentos escaneados ou imagens.

Pode usar:

```text
Tesseract
PaddleOCR
serviço externo se necessário
```

---

### `ai-extraction-worker`

Usado para documentos difíceis.

Pode:

- interpretar layout confuso;
- sugerir campos;
- classificar trechos;
- extrair JSON estruturado;
- encontrar evidências.

A IA deve ajudar na extração.

A IA não deve decidir a conferência sozinha.

---

### `rule-worker`

Executa regras de conferência.

Recebe:

- regra;
- competência;
- variáveis necessárias;
- modelo do cliente.

Devolve:

- aprovado;
- divergente;
- erro;
- pendente;
- não aplicável;
- revisão necessária.

---

### `report-worker`

Gera arquivos pesados:

- PDF;
- Excel;
- balancete anotado;
- relatório final;
- auditoria exportável.

---

## 9. Packages compartilhados

### `shared-types`

Tipos comuns:

```text
User
Client
Competence
Document
Variable
Rule
Execution
Result
Audit
Report
```

---

### `shared-events`

Eventos oficiais do sistema.

Exemplos:

```text
file.imported
document.classified
document.ambiguous
document.missing
document.confirmed
raw.extracted
variables.normalized
variables.ready
rule.executed
result.created
report.generated
log.created
```

Todos os serviços devem usar esses eventos padronizados.

---

### `shared-auth`

Responsável por:

- validação de token;
- claims do usuário;
- roles;
- permissões;
- middlewares comuns.

---

### `variable-schema`

Contrato oficial das variáveis.

---

### `rule-schema`

Contrato oficial das regras.

---

### `document-schema`

Contrato oficial dos documentos.

---

### `rule-engine`

Biblioteca usada pelo `rule-service` e pelo `rule-worker` para interpretar regras.

---

## 10. Ordem de construção

Vou construir serviço por serviço, devagar.

Mesmo que todas as pastas existam desde o início, alguns serviços podem começar apenas com:

- healthcheck;
- config;
- logging;
- conexão com banco;
- contratos;
- endpoint básico.

Ordem recomendada:

```text
1. infra básica
2. packages
3. apps/web
4. apps/bff
5. identity-service
6. client-service
7. conference-model-service
8. document-ingestion-service
9. document-classification-service
10. extraction-orchestrator
11. pdf-extractor-worker
12. excel-extractor-worker
13. normalization-service
14. variable-registry-service
15. rule-service
16. execution-control-service
17. rule-worker
18. result-service
19. audit-service
20. report-service
21. log-service
22. schedule-service
23. OCR
24. IA
25. agente local
```

---

## 11. Regras de arquitetura que a IA deve respeitar

1. Não transformar o projeto em monolito.
2. Não fazer serviço acessar diretamente tabela interna de outro serviço.
3. Não fazer regra ler arquivo bruto diretamente.
4. Não processar tarefa pesada em request HTTP.
5. Não sobrescrever regra antiga; sempre versionar.
6. Não deixar IA decidir conferência sozinha.
7. Sempre salvar evidência da extração.
8. Sempre salvar logs e auditoria.
9. Sempre diferenciar log técnico de auditoria de negócio.
10. Sempre pensar em cliente, competência e permissões.
11. Sempre usar eventos para comunicação assíncrona.
12. Sempre usar Temporal para workflows longos.
13. Sempre manter contratos em `packages`.
14. Sempre criar código pensando que cada serviço pode evoluir separado.
15. Sempre explicar qual serviço está sendo alterado, qual evento usa e qual responsabilidade tem.

---

## 12. Frase guia do projeto

```text
Configura uma vez por cliente.
Todo mês importa ou detecta a pasta da competência.
O sistema identifica documentos, extrai dados, normaliza variáveis, executa regras salvas, gera logs, auditoria e relatórios.
```

A plataforma deve ser construída com a seguinte mentalidade:

```text
Control Plane organiza.
Data Plane processa.
Workers executam.
Packages padronizam.
Infra sustenta.
Auditoria gera confiança.
```
