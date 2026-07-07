# Shared Events

Catálogo oficial e contratos versionados dos eventos assíncronos da CCI. Todo evento usa o envelope comum e um payload específico validável por JSON Schema.

Será usado pelos serviços produtores/consumidores e pelo `shared-events` futuro gerado para Python e TypeScript. Nesta fase não publica mensagens, não cria filas e não integra RabbitMQ ou NATS.

Cada novo evento deve entrar em `events.json`, ganhar schema e exemplo, manter `correlation_id` e declarar versão. Mudanças incompatíveis exigem nova versão do contrato.
