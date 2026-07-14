# Shared Events

Catálogo oficial e contratos versionados dos eventos assíncronos da CCI. Todo evento usa o envelope comum e um payload específico validável por JSON Schema.

Será usado pelos serviços produtores/consumidores e pelo `shared-events` futuro gerado para Python e TypeScript. Nesta fase não publica mensagens, não cria filas e não integra RabbitMQ ou NATS.

Os eventos criados na Fase 2 usam nomes históricos como `file.imported` e `variables.ready`. O catálogo agora também reserva os eventos canônicos `DocumentUploaded`, `DocumentPreviewRequested`, `DocumentPreviewStarted`, `DocumentPreviewGenerated`, `DocumentPreviewFailed`, `TemplateMatched`, `TemplateNotFound`, `TemplateAmbiguous`, `ExtractionRequested`, `ExtractionCompleted`, `ExtractionFailed`, `ExtractionReviewed`, `RulePublished`, `RuleExecutionCompleted`, `ConferenceStarted`, `ConferenceCompleted`, `ReportRequested` e `ReportGenerated`. Payloads específicos e migração de producers/consumers ocorrerão nas fases dos respectivos domínios.

Cada novo evento deve entrar em `events.json`, ganhar schema e exemplo, manter `correlation_id` e declarar versão. Mudanças incompatíveis exigem nova versão do contrato.
