# Documentação da CCI

- `contexto_mestre_conferencia_contabil.md`: visão canônica do produto, arquitetura, módulos, infra e roadmap.
- `arquitetura_conferencia_contabil.mmd`: diagrama Mermaid da arquitetura alvo.
- `fase-1a-chao-tecnico.md`: escopo e critérios técnicos desta fase.
- `fase-1b-templates-tecnicos.md`: padrões e geradores para APIs, serviços modulares e workers.
- `fase-2-packages-compartilhados.md`: contratos canônicos e motor inicial de regras.
- `fase-3-bff-inicial.md`: primeira porta de entrada HTTP e placeholders para a web.
- `fase-4-identity-service.md`: usuários, JWT, RBAC, seed e integração com o BFF.
- `fase-4.1-identity-hardening.md`: sessões, refresh, revogação, bloqueio, rate limit e auditoria de identidade.
- `fase-5-web-inicial.md`: Web App inicial, login, sessão, rotas protegidas e cockpit.
- `fase-5.1-web-operacional-admin.md`: telas administrativas preparadas para serviços incompletos.
- `fase-6-client-service.md`: clientes, competências, vínculos, contexto Web, pastas lógicas e autorização por cliente.
- `fase-7-document-service.md`: upload de arquivos/ZIP, hash, duplicidade, MinIO, metadados e status inicial do documento.
- `fase-8-parser-worker-preview.md`: Parser Worker, jobs de preview, PDF/Excel estruturado, bucket de preview e APIs de consulta/reprocessamento.
- `fase-9-web-document-viewer.md`: viewer visual PDF/Excel na Web, seleção estruturada, painel lateral, destaques de evidência e integração com BFF.
- `preparacao-infra-packages.md`: preparação aditiva de infra, contracts, Compose, ambiente e operação para as próximas fases.

## Decisão arquitetural atual

A arquitetura oficial usa poucos serviços principais com módulos internos extraíveis:

```text
apps: web-app e bff
services: identity, client, document, template, extraction, rule, conference, report
workers: parser, pdf, excel, ocr, ai-extraction, rule, report
packages: shared-types, shared-events, shared-auth, schemas e rule-engine
infra: docker, postgres, redis, rabbitmq, minio, temporal, gateway, observability, scripts
```

Os serviços granulares antigos (`conference-model-service`, `document-ingestion-service`, `document-classification-service`, `extraction-orchestrator`, `normalization-service`, `variable-registry-service`, `execution-control-service`, `result-service`, `audit-service`, `log-service`, `schedule-service`) não são mais a divisão oficial. Quando existirem fisicamente, devem ser lidos como scaffolds legados ou módulos candidatos dentro dos serviços canônicos.

## Roadmap oficial resumido

1. Fase 1A — Chão técnico
2. Fase 1B — Base padrão dos serviços
3. Fase 2 — Packages compartilhados
4. Fase 3 — BFF inicial
5. Fase 4 — Identity Service
6. Fase 5 — Web inicial
7. Fase 6 — Client Service
8. Fase 7 — Document Service
9. Fase 8 — Parser Worker e Preview
10. Fase 9 — Web Document Viewer
11. Fase 10 — Template Service
12. Fase 11 — Template Matching
13. Fase 12 — Template Builder / Annotation
14. Fase 13 — Extraction Service
15. Fase 14 — Extractor Workers básicos
16. Fase 15 — Normalização e Resultados da Extração
17. Fase 16 — Web Extraction Review
18. Fase 17 — Rule DSL
19. Fase 18 — Web Rule Builder
20. Fase 19 — Rule Service
21. Fase 20 — Rule Simulator
22. Fase 21 — Conference Service
23. Fase 22 — Rule Worker
24. Fase 23 — Results, Audit e Timeline
25. Fase 24 — Report Service / Report Worker
26. Fase 25 — Agendamentos e reprocessamentos
27. Fase 26 — Agente Local
28. Fase 27 — Workers complementares
29. Fase 28 — OCR Worker
30. Fase 29 — AI Extraction Worker
31. Fase 30 — Observabilidade completa
32. Fase 31 — Testes e qualidade
33. Fase 32 — CI/CD
34. Fase 33 — Produção

As decisões futuras devem preservar cliente, competência, permissões, evidências, auditoria, módulos extraíveis e o papel central do template no motor de extração.
