# Gateway

Nginx de referencia para desenvolvimento local. O BFF continua sendo a entrada de negocio da Web; servicos internos nao devem ser expostos diretamente em producao.

Rotas locais:

- `/` e `/web`: Web App.
- `/api`: BFF.
- `/health`: healthcheck simples do gateway.

Consoles administrativos de MinIO, RabbitMQ e Temporal continuam acessiveis por suas portas locais e devem ser revisados antes de qualquer exposicao por gateway.
