# Shared Auth

Contratos interoperáveis de roles, permissões e claims da CCI. `permissions.json` é o catálogo oficial; `roles.json` contém a matriz inicial. Os módulos Python e TypeScript oferecem helpers puros para autorização.

Será usado por identity-service, BFF e serviços que precisem conferir acesso. Não implementa login, emissão ou validação criptográfica de tokens, sessões ou persistência.

Exemplo: `has_permission(claims, "documents.import")` e `can_access_client(claims, "client_123")`.
