# CCI Web

Aplicação Next.js da Conferência Contábil Inteligente. A Web é a interface do usuário e fala somente com o BFF; não acessa PostgreSQL nem serviços internos.

## Executar

Requisitos: Node.js 20.9+ e BFF disponível. O workspace foi validado com Node.js 22.

```powershell
cd apps/web
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Acesse `http://localhost:3000`. O valor padrão de desenvolvimento é `NEXT_PUBLIC_BFF_URL=http://localhost:8000/api/v1`.

## Scripts

```powershell
npm run lint
npm run typecheck
npm test
npm run build
```

## Sessão

1. `POST /auth/login` devolve o access token curto e define o refresh em cookie HttpOnly no BFF.
2. O access token permanece somente em memória.
3. Em uma recarga, a Web chama `POST /auth/refresh` com `credentials: include` e depois `GET /auth/me`.
4. Um 401 tenta um refresh uma única vez. Falha de refresh limpa a sessão e leva ao login.
5. `POST /auth/logout` revoga a sessão, limpa o cookie no BFF e sempre limpa o estado local.

Não são usados `localStorage`, `sessionStorage`, refresh token em JavaScript ou secrets públicos.

## Organização

- `src/app`: App Router, login, layout protegido e páginas;
- `src/components`: UI shadcn-style, marca, layout, cockpit e estados;
- `src/features/auth`: sessão, guards e permissões;
- `src/features/context`: contexto operacional, cliente e competência;
- `src/features/document-viewer`: viewer PDF/Excel baseado em preview estruturado, seleção visual e payloads para anotações futuras;
- `src/lib/api`: cliente HTTP tipado e APIs do BFF;
- `src/types`: DTOs de resposta da fronteira Web/BFF;
- `src/test`: setup e fixtures apenas de teste.

Detalhes completos, contratos e limitações estão em `docs/fase-5-web-inicial.md` e `docs/fase-9-web-document-viewer.md`.
