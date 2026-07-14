# Redis

Infraestrutura local para cache, locks simples, rate limit e estado temporário. Uma fila leve só deve ser usada quando RabbitMQ ou Temporal forem desnecessários para o caso.

`redis.conf` contém apenas defaults seguros para desenvolvimento: persistência AOF e nenhuma política de eviction implícita. Autenticação e TLS devem ser definidos antes de produção.
