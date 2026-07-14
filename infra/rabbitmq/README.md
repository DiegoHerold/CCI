# RabbitMQ

Event bus local para comunicacao assincrona entre dominios. `rabbitmq.conf` monta `definitions.json`, preparando o exchange topico `cci.events` e filas conceituais por dominio quando um broker local novo e criado.

Os contracts oficiais pertencem a `packages/shared-events`. Esta infra nao implementa consumers, DLQs finais, retry de dominio ou outbox transacional.

Filas preparadas:

- `cci.document`
- `cci.template`
- `cci.extraction`
- `cci.rule`
- `cci.conference`
- `cci.report`
