# Contexto permanente — Conferência Contábil Inteligente

## Fontes obrigatórias do projeto

Antes de planejar, implementar, revisar ou sugerir qualquer alteração neste projeto, leia:

1. `docs/contexto_mestre_conferencia_contabil.md`
2. `docs/arquitetura_conferencia_contabil.mmd`

Esses arquivos são as fontes canônicas da visão do produto e da arquitetura. Não use as cópias da pasta Downloads. Se uma solicitação exigir mudança de arquitetura, explicite a divergência e confirme o impacto antes de descaracterizar as decisões registradas.

## Visão do produto

Este workspace pertence à plataforma **Conferência Contábil Inteligente**. Ela automatiza conferências contábeis por cliente e competência, respeitando permissões de acesso, modelos reutilizáveis, documentos esperados, regras versionadas, evidências, logs, auditoria e relatórios.

Frase-guia:

> Configura uma vez por cliente. Todo mês importa ou detecta a pasta da competência. O sistema identifica documentos, extrai dados, normaliza variáveis, executa regras salvas, gera logs, auditoria e relatórios.

Fluxo central:

```text
Arquivo bruto
→ documento identificado
→ dados extraídos
→ dados normalizados
→ variáveis confirmadas
→ regras versionadas
→ execução
→ resultado
→ auditoria
→ relatório
```

As regras nunca leem diretamente PDF, Excel, Word ou TXT. Elas consomem somente variáveis normalizadas e confirmadas pelo `variable-registry-service`.

## Organização arquitetural

- **Control Plane:** organiza usuários, clientes, competências, modelos, regras e agendamentos.
- **Data Plane:** recebe, identifica, extrai e normaliza documentos e mantém o registro de variáveis.
- **Workers:** executam processamento pesado de PDF, Excel, Word, TXT, OCR, IA, regras e relatórios.
- **Packages:** centralizam tipos, contratos, eventos, autenticação e schemas compartilhados.
- **Infra:** sustenta persistência, storage, workflows, mensageria, cache e observabilidade.
- **Auditoria:** transforma execução e evidências em uma explicação confiável para o usuário contábil.

O projeto é distribuído por domínio e deve evoluir serviço por serviço. Não consolidar os domínios em um monólito, mesmo durante a construção incremental.

## Tecnologias e comunicação

- Frontend: Next.js, React, TypeScript, Tailwind, shadcn/ui e React Flow em `apps/web`.
- BFF/API Gateway: NestJS ou FastAPI em `apps/bff`; o frontend conversa somente com o BFF.
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
2. Um serviço não acessa diretamente tabelas internas de outro serviço.
3. Regras não leem arquivos brutos; recebem variáveis registradas e confirmadas.
4. Tarefas pesadas não são processadas dentro de requests HTTP; usar Temporal e workers.
5. Regras nunca são sobrescritas; toda alteração cria uma nova versão.
6. IA auxilia extração e interpretação, mas não decide a conferência sozinha.
7. Toda extração relevante preserva origem, confiança e evidência.
8. Toda execução relevante gera logs e auditoria.
9. Log técnico e auditoria de negócio são conceitos separados.
10. Toda solução considera cliente, competência e permissões.
11. Comunicação assíncrona entre domínios usa eventos oficiais.
12. Workflows longos, retentativas e reprocessamentos usam Temporal.
13. Contratos compartilhados pertencem a `packages`.
14. Cada serviço deve poder evoluir e ser implantado separadamente.
15. Documentos ausentes, duplicados ou ambíguos pausam as conferências dependentes e exigem confirmação humana quando aplicável.

## Protocolo para alterações

Ao responder ou alterar o projeto, sempre informe de forma objetiva:

- qual serviço, app, worker, package ou componente de infraestrutura está sendo afetado;
- qual responsabilidade de domínio pertence a ele;
- quais contratos, schemas ou tipos compartilhados mudam;
- quais eventos são publicados e consumidos;
- como cliente, competência, permissões, evidências e auditoria são preservados;
- quais testes ou verificações demonstram que a mudança funciona sem violar os limites entre domínios.

Prefira mudanças incrementais compatíveis com a arquitetura final. Se houver mais de uma opção válida, recomende uma e explique os impactos relevantes sem reabrir decisões já consolidadas nos documentos canônicos.
