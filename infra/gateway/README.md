# Gateway

Nginx de referência para desenvolvimento local. O BFF é a única entrada de negócio da Web; serviços internos não devem ser publicados diretamente em produção.

Roteamento planejado: `/web` para a Web App, `/api` para o BFF e, somente em desenvolvimento, `/minio`, `/rabbitmq` e `/temporal` para consoles administrativos. O perfil opcional `gateway` do Compose ativa esta base; as rotas de componentes ainda ausentes permanecem comentadas.
