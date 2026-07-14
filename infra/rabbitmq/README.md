# RabbitMQ

Event bus local para comunicação assíncrona entre domínios. `definitions.json` prepara o exchange tópico `cci.events` e filas conceituais por domínio; os consumers ainda não são implementados.

Os routing keys seguem `<domínio>.<evento-em-kebab-case>`. Os contratos oficiais pertencem a `packages/shared-events` e sempre carregam correlação e causação. Entre os eventos preparados estão `DocumentUploaded`, `TemplateMatched`, `ExtractionCompleted`, `RulePublished`, `ConferenceCompleted` e `ReportGenerated`.

O Compose atual não importa as definitions automaticamente para evitar alterar uma instância persistente existente. A ativação deve ser explícita após revisar consumers, DLQs e política de retry.
