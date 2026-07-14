# Documentacao da CCI

- `contexto_mestre_conferencia_contabil.md`: visao canonica do produto, arquitetura, modulos, infra e roadmap.
- `arquitetura_conferencia_contabil.mmd`: diagrama Mermaid da arquitetura alvo.
- `fase-1a-chao-tecnico.md`: chao tecnico com Docker Compose e infra base.
- `fase-1b-templates-tecnicos.md`: padroes e geradores para APIs, servicos modulares e workers.
- `fase-2-packages-compartilhados.md`: contratos canonicos e motor inicial de regras.
- `fase-3-bff-inicial.md`: primeira porta de entrada HTTP e placeholders para a web.
- `fase-4-identity-service.md`: usuarios, JWT, RBAC, seed e integracao com o BFF.
- `fase-4.1-identity-hardening.md`: sessoes, refresh, revogacao, bloqueio, rate limit e auditoria de identidade.
- `fase-5-web-inicial.md`: Web App inicial, login, sessao, rotas protegidas e cockpit.
- `fase-5.1-web-operacional-admin.md`: telas administrativas preparadas para servicos incompletos.
- `fase-6-client-service.md`: clientes, competencias, vinculos, contexto Web, pastas logicas e autorizacao por cliente.
- `fase-7-document-service.md`: upload de arquivos/ZIP, hash, duplicidade, MinIO, metadados e status do documento.
- `fase-8-parser-worker-preview.md`: Parser Worker, jobs de preview, PDF/Excel estruturado e APIs de consulta/reprocessamento.
- `fase-9-web-document-viewer.md`: viewer visual PDF/Excel na Web, selecao estruturada e destaques de evidencia.
- `fase-10-template-service.md`: templates, categorias, campos/objetos, annotations, extraction rules e versionamento.
- `fase-11-template-matching.md`: matching de templates por perfil tecnico do documento.
- `fase-12-template-builder-annotation.md`: builder visual de templates e annotations com regra tecnica sugerida.
- `fase-13-extraction-service.md`: jobs de extracao, Temporal preparado, status, retries, dispatch de workers e artefatos brutos.
- `fase-14-extractor-workers-basicos.md`: workers PDF/Excel para extracao bruta por template, estrategias tecnicas e evidencias.
- `fase-15-normalizacao-resultados-extracao.md`: normalizacao, resultados persistidos, evidencias, status e APIs de consulta.
- `fase-16-fluxo-guiado-template-review.md`: fluxo guiado por documento, criacao guiada de template e revisao/correcao de variaveis extraidas.
- `preparacao-infra-packages.md`: preparacao aditiva de infra, contracts, Compose, ambiente e operacao.
- `recriar-infra-docker-local.md`: roteiro para reconstruir Docker local, schemas, buckets e servicos existentes.

## Decisao Arquitetural Atual

A arquitetura oficial usa poucos servicos principais com modulos internos extraiveis:

```text
apps: web-app e bff
services: identity, client, document, template, extraction, rule, conference, report
workers: parser, pdf, excel, ocr, ai-extraction, rule, report
packages: shared-types, shared-events, shared-auth, schemas e rule-engine
infra: docker, postgres, redis, rabbitmq, minio, temporal, gateway, observability, scripts
```

Os servicos granulares antigos nao sao mais a divisao oficial. Quando existirem fisicamente, devem ser lidos como scaffolds legados ou modulos candidatos dentro dos servicos canonicos.

## Roadmap Oficial Resumido

1. Fase 1A - Chao tecnico
2. Fase 1B - Base padrao dos servicos
3. Fase 2 - Packages compartilhados
4. Fase 3 - BFF inicial
5. Fase 4 - Identity Service
6. Fase 5 - Web inicial
7. Fase 6 - Client Service
8. Fase 7 - Document Service
9. Fase 8 - Parser Worker e Preview
10. Fase 9 - Web Document Viewer
11. Fase 10 - Template Service
12. Fase 11 - Template Matching
13. Fase 12 - Template Builder / Annotation
14. Fase 13 - Extraction Service
15. Fase 14 - Extractor Workers basicos
16. Fase 15 - Normalizacao e Resultados da Extracao
17. Fase 16 - Fluxo Guiado, Template Builder e Web Extraction Review
18. Fase 17 - Rule DSL
19. Fase 18 - Web Rule Builder
20. Fase 19 - Rule Service
21. Fase 20 - Rule Simulator
22. Fase 21 - Conference Service
23. Fase 22 - Rule Worker
24. Fase 23 - Results, Audit e Timeline
25. Fase 24 - Report Service / Report Worker
26. Fase 25 - Agendamentos e reprocessamentos
27. Fase 26 - Agente Local
28. Fase 27 - Workers complementares
29. Fase 28 - OCR Worker
30. Fase 29 - AI Extraction Worker
31. Fase 30 - Observabilidade completa
32. Fase 31 - Testes e qualidade
33. Fase 32 - CI/CD
34. Fase 33 - Producao

As decisoes futuras devem preservar cliente, competencia, permissoes, evidencias, auditoria, modulos extraiveis e o papel central do template no motor de extracao.
