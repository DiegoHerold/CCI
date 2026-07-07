# Shared Auth

Contratos interoperáveis de roles, permissões e claims da CCI. `permissions.json` é o catálogo oficial; `roles.json` contém a matriz inicial. Os módulos Python e TypeScript oferecem helpers puros para autorização.

Será usado por identity-service, BFF e serviços que precisem conferir acesso. Não implementa login, emissão ou validação criptográfica de tokens, sessões ou persistência.

Exemplo: `has_permission(claims, "documents.import")` e `can_access_client(claims, "client_123")`.
Os arquivos `roles.json`, `permissions.json` e os helpers Python/TypeScript
preservam o contrato experimental criado na Fase 2.

O contrato aditivo `identity-rbac-v1.json` registra os papéis e permissões
emitidos pelo Identity Service a partir da Fase 4. Ele usa roles em maiúsculas
e permissões no formato `recurso:ação`; a Fase 4.1 acrescenta
`users:reset-password` ao `ADMIN`. Consumidores antigos não foram
alterados nesta fase; a unificação dos helpers será feita quando o package
ganhar distribuição/versionamento próprios.

`identity-session-v1.json` registra as claims, TTLs padrão e a divisão de
responsabilidade de transporte entre Identity e BFF introduzida na Fase 4.1.

`identity-rbac-v2.json` adiciona as permissões globais do Client Service sem
alterar o contrato experimental da Fase 2 nem remover a versão 1. O vínculo
ativo no Client Service continua obrigatório além da permissão global; apenas
`ADMIN` possui bypass explícito de vínculo.
