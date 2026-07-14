# Fase 5 — Web inicial

## Responsabilidade e limites

`apps/web` é a interface Next.js da CCI. Ela apresenta login, sessão, permissões, contexto de cliente/competência e o cockpit inicial. Toda comunicação de negócio ocorre por REST/HTTPS com `apps/bff`; a Web não conhece URLs de serviços internos, não acessa PostgreSQL, não processa documentos e não executa regras.

Esta fase não altera schemas ou tipos em `packages`, não publica nem consome eventos e não cria persistência. Cliente e competência continuam sob responsabilidade do `client-service`; identidade e sessão pertencem ao `identity-service`; o BFF valida e encaminha a fronteira pública.

## Stack e roteamento

- Next.js 16 com App Router, React 19 e TypeScript estrito;
- Tailwind CSS 4 e componentes shadcn-style configurados em `components.json`;
- Lucide para iconografia, sem imagens ou fontes externas;
- Vitest, Testing Library e jsdom para testes;
- ESLint com configuração oficial do Next.

Rotas:

| Rota | Acesso | Estado nesta fase |
| --- | --- | --- |
| `/` | público | decide entre login e dashboard após validar sessão |
| `/login` | público | formulário real contra o BFF |
| `/dashboard` | autenticado | cockpit e contexto real, sem métricas fictícias |
| `/clients` | `clients:read` | clientes reais retornados por `/client-context` |
| `/competencies` | `client-competencies:read` | lista real do cliente selecionado |
| `/documents`, `/models`, `/variables`, `/rules` | `conferences:read` | estados informativos de módulos futuros; `/variables` é rótulo histórico para campos/objetos extraídos e revisão |
| `/executions`, `/audit` | `conferences:read` | estados informativos de módulos futuros |
| `/reports` | `reports:read` | estado informativo |
| `/settings` | autenticado | usuário, roles e estratégia da sessão |

## Contratos do BFF utilizados

A base pública é `NEXT_PUBLIC_BFF_URL`, incluindo `/api/v1`.

- `POST /auth/login` com `{ email, password }`;
- `POST /auth/refresh` usando o cookie `cci_refresh_token` HttpOnly;
- `GET /auth/me` com access token Bearer;
- `POST /auth/logout` com Bearer e cookie;
- `GET /client-context` para usuário, clientes acessíveis, preferência e competência de referência;
- `PATCH /client-context/preferences` para persistir o cliente escolhido;
- `GET /clients/:clientId/competencies` para competências reais.

Erros seguem `error.code`, `error.message` e `correlation_id`. A interface converte falhas de autenticação/rede em mensagens seguras e não exibe detalhes técnicos.

## Estratégia de sessão e proteção

O access token de 15 minutos é uma variável em memória do módulo HTTP. O refresh nunca entra no JavaScript: permanece no cookie HttpOnly, SameSite definido pelo BFF e Secure em produção. Em cada abertura, a Web executa refresh e `/auth/me` antes de revelar o layout protegido.

`RequireAuth` bloqueia o layout autenticado durante a validação e redireciona para `/login`. `RequirePermission` protege acesso direto às páginas; `PermissionGate` e a sidebar escondem capacidades não autorizadas. Essas barreiras melhoram a experiência, mas o BFF e os serviços continuam sendo a autoridade real.

## Contexto operacional

`OperationalContextProvider` carrega somente `/client-context`. Não existem clientes ou competências de fallback. O cliente default só é aceito se estiver na lista autorizada; uma troca chama o endpoint de preferências. A competência exibida vem da resposta do Client Service e nunca é criada automaticamente pela Web.

Se o serviço estiver indisponível, o dashboard mostra erro recuperável. Lista vazia produz o estado “Nenhum cliente vinculado”. Cliente sem competência cadastrada produz um estado próprio em `/competencies`.

## Componentes e identidade

Componentes reutilizáveis: `AppShell`, `Sidebar`, `Topbar`, `ProductLogo`, `UserMenu`, `ThemeSurface`, `PageHeader`, `MetricCard`, `StatusBadge`, `EmptyState`, `ErrorState`, `LoadingState`, `ForbiddenState`, `ClientSelector`, `CompetenceSelector`, `ModuleCard`, `TimelinePreview`, `PermissionGate` e guards.

O visual adota um cockpit semi-escuro com superfícies slate profundas, bordas translúcidas e realces contidos em ciano/violeta. A tela de login representa o fluxo documento → campos/objetos extraídos → regras → auditoria. O dashboard usa linha operacional, integridade do contexto e módulos por domínio, evitando o padrão de cards SaaS genéricos. Animações são CSS leves e respeitam `prefers-reduced-motion`.

## Ambiente e execução

```env
NEXT_PUBLIC_BFF_URL=http://localhost:8000/api/v1
```

Essa variável contém apenas a URL pública do BFF. `DATABASE_URL`, secrets JWT e credenciais de serviço não pertencem à Web.

```powershell
docker compose up -d --build identity-service client-service bff
cd apps/web
Copy-Item .env.example .env.local
npm ci
npm run dev
```

## Testes e verificações

A suíte cobre login, payload enviado ao BFF, erro seguro, bootstrap de sessão, `/auth/me`, redirecionamento sem sessão, logout, dashboard vazio e com contexto, filtro de menu, forbidden, loading, erro, retry de refresh, URL exclusiva do BFF e ausência de clientes mockados na produção.

```powershell
npm run lint
npm run typecheck
npm test
npm run build
```

## Limitações e próximos passos

- não há recuperação de senha, MFA, OAuth ou SSO;
- a proteção de navegação é client-side porque o access token não é exposto ao servidor Next; o BFF continua protegendo todos os dados;
- módulos de documentos, modelos, campos/objetos extraídos, regras, execuções, auditoria e relatórios são estados informativos, sem ações falsas;
- status em tempo real/SSE, upload e previews permanecem fora do escopo;
- uma implantação cross-site entre Web e BFF exigirá revisão de SameSite/CORS e proteção CSRF antes de `SameSite=None`;
- permissões específicas de futuros domínios devem ser adicionadas ao contrato RBAC antes de habilitar seus menus.
