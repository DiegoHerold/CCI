# Temporal

Orquestrador local de workflows duraveis. Usa PostgreSQL exclusivo, separado do banco da aplicacao.

Sera usado para extracoes, OCR, IA assistida, execucao de regras, conferencias, geracao de relatorios e reprocessamentos.

A Fase 13 prepara o `ExtractionWorkflow` no `extraction-service` e reserva a task queue `extraction-task-queue`. Os workers reais de PDF/Excel entram na Fase 14.

O namespace local sugerido e `cci-development`. `dynamicconfig/development.yaml` mantem somente opcoes minimas de desenvolvimento; namespaces e politicas de retencao devem ser criados explicitamente antes de uso real.
