# Contexto permanente — Conferência Contábil Inteligente

## Fontes obrigatórias do projeto

Antes de planejar, implementar, revisar ou sugerir qualquer alteração neste projeto, leia:

1. `docs/contexto_mestre_conferencia_contabil.md`
2. `docs/arquitetura_conferencia_contabil.mmd`

Esses arquivos são as fontes canônicas da visão do produto e da arquitetura. Não use cópias da pasta Downloads. Se uma solicitação exigir mudança de arquitetura, explicite a divergência e confirme o impacto antes de descaracterizar as decisões registradas.

## Visão do produto

Este workspace pertence à plataforma **Conferência Contábil Inteligente**. Ela automatiza conferências contábeis por cliente e competência, respeitando permissões de acesso, templates reutilizáveis, documentos esperados, regras versionadas, campos/objetos extraídos, evidências, auditoria, timeline e relatórios.

Frase-guia:

> Configura uma vez por cliente. Todo mês importa ou detecta a pasta da competência. O sistema identifica documentos, aplica templates, extrai e normaliza campos/objetos, executa regras salvas, gera evidências, auditoria, timeline e relatórios.

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

As regras nunca leem diretamente PDF, Excel, Word, TXT ou imagem. Elas consomem somente campos/objetos extraídos, normalizados, evidenciados e aprovados/revisados pelo fluxo de extração. O termo histórico "variável" pode aparecer em contratos antigos, mas a linguagem alvo é **campo/objeto extraído com evidência**.

## Organização arquitetural oficial

- **Apps:** interfaces e entrada da experiência; `apps/web` é a Web App atual e representa logicamente `web-app`; `apps/bff` é a porta de entrada da Web.
- **Services:** domínios de negócio principais: `identity-service`, `client-service`, `document-service`, `template-service`, `extraction-service`, `rule-service`, `conference-service` e `report-service`.
- **Workers:** executores de tarefas pesadas ou assíncronas: parser, PDF, Excel, OCR, IA, regras e relatórios.
- **Packages:** contratos, eventos, autenticação, schemas e bibliotecas puras compartilhadas.
- **Infra:** Docker, PostgreSQL, Redis, RabbitMQ, MinIO, Temporal, gateway, observabilidade e scripts.
- **Docs:** arquitetura, fases, contratos e decisões.

Regra de leitura:

```text
Serviço separa domínio.
Módulo separa responsabilidade interna.
Worker executa tarefa pesada.
Package compartilha contrato.
Evento integra domínios de forma desacoplada.
```

O projeto é distribuído por domínio e deve evoluir serviço por serviço. Não consolidar os domínios em um monólito. Também não criar serviço separado para cada etapa técnica cedo demais; módulos internos devem ser bem isolados e extraíveis no futuro.

## Serviços canônicos

- `identity-service`: usuários, autenticação, JWT, refresh token, roles, permissões, convites e sessões.
- `client-service`: clientes, CNPJ, competências, usuários vinculados ao cliente, permissões por cliente, pasta padrão e organização da área de trabalho.
- `document-service`: uploads, ZIP, metadados, hash, duplicidade, MinIO, vínculo cliente/competência, status e preview estruturado.
- `template-service`: templates, categorias/tipos de documento, campos/objetos, anotações visuais, regras técnicas de extração, matching e versionamento.
- `extraction-service`: jobs, Temporal, aplicação de templates, normalização, resultados, evidências, confiança, status e revisão.
- `rule-service`: Rule DSL, regras, operadores, fórmulas, blocos lógicos, canvas visual futuro, validação, versionamento, publicação e simulação.
- `conference-service`: modelos de conferência, documentos esperados, rule sets, execuções, resultados consolidados, auditoria de negócio, timeline, agendamentos e reprocessamentos.
- `report-service`: relatórios PDF/Excel, documentos anotados, balancete anotado e exportações.

Decisão importante:

> O tipo de documento não é o centro da arquitetura. Tipo/categoria é uma classificação do template. O template é o centro do motor de extração.

O `client-service` já existe e deve manter esse nome físico. Ele representa o domínio de clientes, competências, vínculos de usuários, permissões por cliente e organização da área de trabalho. Não renomear automaticamente para `workspace-service`.

## Tecnologias e comunicação

- Frontend: Next.js, React, TypeScript, Tailwind, shadcn/ui e React Flow em `apps/web`.
- BFF/API Gateway: FastAPI atual em `apps/bff`; NestJS continua aceitável como alternativa futura. O frontend conversa somente com o BFF.
- Serviços: preferencialmente FastAPI/Python, com responsabilidade e domínio próprios.
- Banco: PostgreSQL, inicialmente um cluster com schemas por domínio; cada serviço é dono de seu schema.
- Storage: MinIO inicialmente e S3 futuramente.
- Workflows longos: Temporal.
- Eventos assíncronos: RabbitMQ ou NATS, usando contratos de `packages/shared-events`.
- Cache, locks e estados transitórios: Redis.
- Observabilidade: OpenTelemetry, Sentry, Prometheus e Grafana.
- Interface para BFF: REST/HTTPS; status em tempo real por SSE inicialmente.
- Comunicação interna alvo: gRPC; REST interno somente como transição explícita.

## Regras arquiteturais obrigatórias

1. Não transformar a plataforma em monólito.
2. Não criar microserviço para cada etapa técnica cedo demais.
3. Um serviço não acessa diretamente tabelas internas de outro serviço.
4. Módulos internos potencialmente extraíveis não acessam repositories internos uns dos outros; usam portas/interfaces/adapters.
5. BFF agrega e adapta dados para a Web, mas não contém regra de negócio profunda.
6. Tarefas pesadas não rodam dentro de requests HTTP; usar Temporal e workers.
7. `document-service` é dono dos arquivos, uploads, status e previews.
8. `template-service` é dono de templates, categorias, campos/objetos, anotações e matching.
9. `extraction-service` é dono de jobs, resultados, evidências, normalização, confiança e revisão.
10. `rule-service` é dono da DSL, regras, operadores, fórmulas, simulação e versionamento.
11. `conference-service` é dono da execução da conferência, resultado consolidado, auditoria, timeline e agendamentos.
12. `report-service` é dono de relatórios e exportações.
13. Regras não leem arquivos brutos; consomem campos/objetos extraídos, normalizados, evidenciados e revisados.
14. Regras nunca são sobrescritas; toda alteração cria uma nova versão.
15. IA auxilia extração e interpretação, sempre com JSON estruturado, evidências, confiança e revisão obrigatória; IA não decide a conferência sozinha.
16. Toda extração relevante preserva origem, confiança e evidência.
17. Toda execução relevante gera auditoria de negócio e timeline.
18. Log técnico e auditoria de negócio são conceitos separados.
19. Toda solução considera cliente, competência e permissões.
20. Comunicação assíncrona entre domínios usa eventos oficiais.
21. Workflows longos, retentativas e reprocessamentos usam Temporal.
22. Contratos compartilhados pertencem a `packages`.
23. Infra deve permitir subir o ambiente com Docker.
24. Documentos ausentes, duplicados ou ambíguos pausam as conferências dependentes e exigem confirmação humana quando aplicável.
25. Anotações visuais no frontend devem poder virar regras reutilizáveis de template.
26. O Rule Builder futuro deve ser visual, estilo canvas, com cards, blocos lógicos, condições, comparações, fórmulas e equações.

## Protocolo para alterações

Ao responder ou alterar o projeto, sempre informe de forma objetiva:

- qual serviço, app, worker, package ou componente de infraestrutura está sendo afetado;
- qual responsabilidade de domínio pertence a ele;
- quais contratos, schemas ou tipos compartilhados mudam;
- quais eventos são publicados e consumidos;
- como cliente, competência, permissões, evidências e auditoria são preservados;
- quais testes ou verificações demonstram que a mudança funciona sem violar os limites entre domínios.

Prefira mudanças incrementais compatíveis com a arquitetura final. Se houver mais de uma opção válida, recomende uma e explique os impactos relevantes sem reabrir decisões já consolidadas nos documentos canônicos.
