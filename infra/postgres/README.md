# PostgreSQL

O cluster principal da aplicação usa schemas por domínio. Cada serviço é dono de seu schema e não acessa tabelas internas de outro domínio.

`init/001_create_schemas.sql` é idempotente e preserva os schemas históricos das fases já entregues enquanto prepara `identity`, `client`, `document`, `template`, `extraction`, `rule`, `conference` e `report`. Ele também mantém o registro técnico `core.platform_bootstrap`.

`schemas/` documenta propriedade e convenções. `migrations/` reserva a organização global; migrations de serviços continuam nos próprios serviços quando já houver Alembic.
