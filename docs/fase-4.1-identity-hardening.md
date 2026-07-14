# Fase 4.1 — Identity Service Hardening

## Escopo e limites

Esta fase endurece o `identity-service`, componente do Control Plane e único
dono do schema PostgreSQL `auth`. O BFF continua sem regras de autenticação:
ele transporta requisições e aplica a estratégia web de cookie. Nenhum outro
serviço lê tabelas de identidade.

Não há publicação em RabbitMQ nem integração com auditoria/timeline de conferência. Os eventos
descritos aqui são registros append-only internos de segurança no schema
`auth`; auditoria contábil de negócio continua sendo responsabilidade do `conference-service`.

## Fluxo de login e sessão

1. O Identity aplica rate limit por hash de IP e e-mail.
2. Valida bloqueio temporário, status e senha sem revelar se a conta existe.
3. Cria uma linha em `auth.sessions`.
4. Emite access JWT de 15 minutos e refresh JWT de 7 dias.
5. Persiste somente SHA-256 do refresh token.
6. Registra `AUTH_LOGIN_SUCCESS` ou `AUTH_LOGIN_FAILED`.

O access token contém `sub`, `sid`, `typ=access`, `jti`, `email`, `roles`,
`permissions`, `iat` e `exp`. O refresh contém `sub`, `sid`, `typ=refresh`,
`jti`, `iat` e `exp`, assinado com segredo diferente. O contrato compartilhado
está em `packages/shared-auth/identity-session-v1.json`.

## Modelo persistente

A migration `0002_identity_hardening` acrescenta:

- campos `failed_login_attempts`, `locked_until` e `last_failed_login_at` em
  `auth.users`;
- `auth.sessions`: usuário, hash do refresh, IP, user-agent, expiração,
  revogação e timestamps;
- `auth.audit_events`: evento, usuário, IP, user-agent, metadata segura e
  timestamp;
- `auth.login_rate_limits`: identificador irreversível, janela e contador.

Tokens e senhas completos nunca entram na auditoria. IP e e-mail usados no
rate limit são armazenados como hashes; o e-mail de tentativas desconhecidas
aparece na auditoria somente como fingerprint truncada.

## Endpoints internos

| Método e rota | Autorização | Comportamento |
| --- | --- | --- |
| `POST /auth/login` | pública | cria sessão e retorna access + refresh |
| `POST /auth/refresh` | refresh token | emite novo access token |
| `POST /auth/logout` | access token | revoga a sessão atual |
| `POST /auth/logout-all` | access token | revoga todas as sessões do usuário |
| `POST /auth/change-password` | access token | troca senha e preserva somente a sessão atual |
| `GET /auth/me` | access token | recarrega usuário e sessão |
| `POST /users/{id}/reset-password` | `users:reset-password` | troca senha e revoga todas as sessões do alvo |

O refresh não é rotacionado nesta fase. Sessão revogada/expirada e usuário
inativo não geram novo access token. Access tokens também deixam de funcionar
assim que sua sessão é revogada.

## Estratégia do BFF para navegador/PWA

As rotas públicas usam o prefixo `/api/v1`. No login, o BFF remove
`refreshToken` do JSON e o coloca no cookie `cci_refresh_token` com:

- `HttpOnly`;
- `SameSite=Lax` por padrão;
- `Secure=true` em produção;
- escopo `/api/v1/auth`;
- `Cache-Control: no-store` nas respostas de identidade.

O frontend mantém o access token curto apenas em memória e chama
`POST /api/v1/auth/refresh`; o navegador envia o cookie automaticamente. Não
usar armazenamento web para tokens. Se frontend e BFF forem implantados em
sites diferentes, será necessário rever SameSite e adicionar proteção CSRF
explícita antes de usar `SameSite=None`.

## Política de senha e abuso

A senha exige no mínimo 8 caracteres, uma letra e um número; não pode ser igual
ao nome nem ao e-mail. Após `AUTH_MAX_FAILED_ATTEMPTS`, a conta é bloqueada por
`AUTH_LOCK_MINUTES`. Sucesso antes do bloqueio zera o contador. Login também é
limitado por IP e e-mail dentro de uma janela persistida no PostgreSQL.

Conta inexistente, senha errada, conta inativa e conta bloqueada retornam o
mesmo `401 INVALID_CREDENTIALS`. Excesso do rate limit retorna `429` com
`Retry-After`.

## Auditoria interna

Eventos registrados:

- `AUTH_LOGIN_SUCCESS` e `AUTH_LOGIN_FAILED`;
- `AUTH_LOGOUT` e `AUTH_LOGOUT_ALL`;
- `AUTH_TOKEN_REFRESH`;
- `AUTH_PASSWORD_CHANGED`;
- `AUTH_PASSWORD_RESET_BY_ADMIN`;
- `AUTH_USER_DISABLED` e `AUTH_USER_ENABLED`;
- `AUTH_PERMISSION_DENIED`.

Não existem endpoints comuns para editar ou excluir esses registros.

## Ambiente

```env
JWT_ACCESS_SECRET=
JWT_ACCESS_EXPIRES_IN=15m
JWT_REFRESH_SECRET=
JWT_REFRESH_EXPIRES_IN=7d
AUTH_MAX_FAILED_ATTEMPTS=5
AUTH_LOCK_MINUTES=15
AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
AUTH_LOGIN_RATE_LIMIT_MAX=10
AUTH_REFRESH_COOKIE_SECURE=true
AUTH_REFRESH_COOKIE_SAMESITE=lax
AUTH_REFRESH_COOKIE_MAX_AGE=604800
```

Os dois segredos JWT devem ser diferentes, aleatórios e ter ao menos 32
caracteres.

## Operação

```bash
make identity-migrate
make identity-seed
make identity-test
make bff-test
docker compose up -d --build identity-service bff
```

O container aplica `0002_identity_hardening` automaticamente antes do seed e
do servidor. O seed adiciona `users:reset-password` ao papel `ADMIN` sem
duplicar dados nem alterar a senha do administrador existente.

Access tokens emitidos antes desta migration não possuem `sid` e deixam de ser
aceitos; usuários já autenticados precisam entrar novamente uma única vez após
o deploy.

## Fora do escopo

Rotação de refresh token, MFA, OAuth/SSO, recuperação por e-mail, permissões por
cliente, device trust e painel de sessões ficam para fases futuras. Também será
necessário definir retenção/limpeza para sessões expiradas, auditoria e janelas
de rate limit. Em produção, a porta do Identity deve permanecer restrita à rede
interna para que somente o BFF encaminhe o IP de origem confiável.
