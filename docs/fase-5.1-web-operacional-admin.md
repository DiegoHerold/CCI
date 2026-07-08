# Fase 5.1 — Web operacional admin e tolerância a serviços incompletos

## Responsabilidade e limites

Esta fase evolui `apps/web` a partir da Fase 5 (Web inicial). O objetivo não é
substituir a arquitetura existente, e sim torná-la operável por um
administrador antes que todos os serviços de backend estejam prontos:
cadastro de clientes, convite de usuários, aceite público de convite e
degradação visual controlada quando um endpoint do BFF ainda não existe.

A Web continua falando apenas com `apps/bff`. Nenhum código novo desta fase
acessa `identity-service` ou `client-service` diretamente, nem lê PostgreSQL.
Nenhum dado fake é tratado como real: toda confirmação de sucesso (cliente
criado, convite enviado, convite aceito) depende de uma resposta 2xx do BFF.

## O que foi corrigido

* A tela `/clients`, que antes só espelhava os clientes do `/client-context`
  (contexto do usuário logado), passou a consultar a listagem administrativa
  real (`GET /clients`) e a oferecer busca e criação.
* Toda tela administrativa nova segue o mesmo padrão de estados
  (`loading` → `ready` → `error` → `unavailable`), eliminando qualquer
  possibilidade de tela em branco ou erro bruto do backend aparecendo para o
  usuário.
* Os efeitos de carregamento inicial passaram a usar o mesmo padrão já usado
  em `OperationalContextProvider` (`window.setTimeout(…, 0)` antes do
  `setState`), evitando o alerta de lint `react-hooks/set-state-in-effect` e
  cascatas de render desnecessárias.

## Telas criadas ou melhoradas

| Rota | Status | Descrição |
| --- | --- | --- |
| `/clients` | melhorada | Lista real via `GET /clients`, busca, criação via drawer, estados completos. |
| `/users` | criada | Lista real via `GET /users`, busca, badges de status/roles, convite, reenvio de convite e desativação. |
| `/accept-invite?token=...` | criada | Rota pública (fora do layout autenticado) para validar convite e definir senha. |
| `/settings/services` | criada | Painel de diagnóstico que testa `GET /auth/me`, `GET /users`, `GET /clients` e `GET /client-context` e mostra disponibilidade sem expor dados sensíveis. |

A navegação (`src/components/layout/navigation.ts`) ganhou o grupo
"Administração" com o item **Usuários** (atrás de `users:read`) e o item
**Status dos serviços** em "Governança".

## Componentes criados

Estados e utilitários compartilhados (`src/components/states/`):

* `ServiceUnavailableState` — estado obrigatório para endpoint ausente ou não
  implementado (404/501/503), com mensagem padronizada e ação de retry.
* `FormErrorState`, `InlineFieldError` — erro geral de formulário e erro por
  campo, no mesmo padrão visual já usado no login.
* `SuccessNotice`, `PendingNotice` — confirmação e aviso, usados somente após
  confirmação real do BFF.

Badges (`src/components/badges/`): `ClientStatusBadge`, `UserStatusBadge`,
`InviteStatusBadge`, `RoleBadge`.

UI (`src/components/ui/`): `FormDrawer` (painel lateral reutilizável para
formulários de criação/edição) e `DataToolbar` (busca + ação, usado em
`/clients` e `/users`).

Formulários (`src/features/`): `ClientForm` (`features/clients/client-form.tsx`)
e `InviteUserForm` (`features/users/invite-user-form.tsx`), ambos em
`useState` simples — mesmo padrão do `LoginForm` já existente, sem introduzir
`react-hook-form`/`zod` como nova dependência.

## Camada de API alterada

```txt
src/lib/api/http-client.ts        (sem mudança de contrato; continua padronizando fetch, token e erro)
src/lib/api/error-utils.ts        (novo) — classifica qualquer ApiError em ApiErrorCode
src/lib/api/clients-api.ts        (novo) — GET /clients, POST /clients
src/lib/api/users-api.ts          (novo) — GET /users, POST /users/invitations,
                                            POST /users/:id/resend-invite, PATCH /users/:id/disable
src/lib/api/auth-api.ts           (ampliado) — GET /auth/invitations/:token,
                                                POST /auth/invitations/:token/accept
src/lib/validation/cnpj.ts        (novo) — formatCnpj, isValidCnpj, normalizeCnpjDigits
```

`classifyApiError` mapeia qualquer resposta do BFF para um dos códigos:

```ts
type ApiErrorCode =
  | "UNAUTHORIZED"      // 401
  | "FORBIDDEN"         // 403
  | "NOT_FOUND"         // não usado diretamente: 404 vira SERVICE_UNAVAILABLE
  | "VALIDATION_ERROR"  // 400/422
  | "SERVICE_UNAVAILABLE" // 404, 501, 503, ou mensagem indicando rota não implementada
  | "NETWORK_ERROR"     // falha de fetch (status 0)
  | "UNKNOWN_ERROR";    // qualquer outro caso (ex.: 500 genérico)
```

Toda tela usa `classifyApiError` (ou o atalho `isEndpointUnavailable`) antes de
decidir o estado visual — nunca interpreta o corpo do erro diretamente.

## Fluxos implementados

### Cadastro de cliente (`/clients`)

1. Admin com `clients:create` clica em **Novo cliente**.
2. `ClientForm` valida no frontend: razão social obrigatória, CNPJ obrigatório
   e com dígitos verificadores válidos (algoritmo completo, não apenas
   contagem de dígitos), UF com 2 letras se preenchida.
3. Envia `POST /clients`. Sucesso real → fecha o drawer, mostra
   `SuccessNotice` e recarrega a lista (`GET /clients`).
4. Erro de validação do BFF (400/422, ex.: CNPJ duplicado) → mensagem do
   backend aparece no topo do formulário; nada é limpo.
5. Endpoint ausente (404/501/503) → formulário permanece aberto e mostra
   "Cadastro ainda não concluído…"; nenhum cliente é salvo local ou
   remotamente.

### Convite de usuário (`/users`)

1. Admin com `users:create` clica em **Novo usuário**.
2. `InviteUserForm` valida nome, e-mail (formato) e ao menos uma role global.
   A role `ADMIN` só fica selecionável se o usuário logado já for `ADMIN`.
3. Vínculo com clientes é opcional: se `GET /clients` responder normalmente,
   mostra a lista para seleção; se responder indisponível, mostra o aviso
   "Vínculo com clientes indisponível" sem quebrar o formulário.
4. Envia `POST /users/invitations`. Sucesso real → fecha o drawer, mostra
   `SuccessNotice`, recarrega `/users`. Nenhuma senha é pedida ou gerada aqui.
5. Endpoint ausente → "Convite ainda não disponível…"; nenhum usuário é
   criado e nenhum e-mail é considerado enviado.
6. Reenvio de convite (`POST /users/:id/resend-invite`) e desativação
   (`PATCH /users/:id/disable`) seguem a mesma regra: sucesso só é anunciado
   após resposta 2xx real do BFF.

### Aceite de convite (`/accept-invite?token=...`)

1. Rota pública, fora do layout autenticado (`src/app/accept-invite/page.tsx`,
   não usa `RequireAuth`/`AppShell`).
2. Ao montar, valida o token via `GET /auth/invitations/:token`.
   * Sem token na URL → estado "Convite inválido".
   * `status: EXPIRED` → "Convite expirado".
   * `status: INVALID` → "Convite inválido".
   * Endpoint ausente → `ServiceUnavailableState` com o texto exigido pela
     especificação.
3. Usuário define senha (mínimo 8 caracteres, 1 letra e 1 número) e confirma;
   o frontend valida que os dois campos coincidem antes de enviar.
4. Envia `POST /auth/invitations/:token/accept`. Sucesso real → mostra "Conta
   ativada" e redireciona para `/login` após ~1,6s.
5. Nenhuma senha é logada, persistida em storage do navegador ou reaproveitada
   em outra chamada.

### Status dos serviços (`/settings/services`)

Executa, em paralelo, `GET /auth/me`, `GET /users`, `GET /clients` e
`GET /client-context`, e classifica cada um em: Disponível, Indisponível, Sem
permissão, Não implementado ou Erro — sem expor corpo de resposta, token ou
detalhe técnico. Botão "Verificar novamente" repete a checagem sob demanda.

## Contratos do BFF esperados por esta fase

```http
GET  /clients
POST /clients
GET  /users
POST /users/invitations
POST /users/:id/resend-invite
PATCH /users/:id/disable
GET  /auth/invitations/:token
POST /auth/invitations/:token/accept
```

## Endpoints que ainda não existem no BFF (confirmado nesta fase)

Inspecionando `apps/bff/app/api/routes/`:

* `auth.py` expõe `POST /login`, `POST /refresh`, `POST /logout`,
  `POST /logout-all`, `POST /change-password`, `GET /me`. **Não existe**
  `GET /auth/invitations/:token` nem `POST /auth/invitations/:token/accept`.
* `users.py` expõe `GET /users`, `POST /users` (criação direta com senha,
  fluxo diferente do convite), `GET/PATCH /users/:id`,
  `PATCH /users/:id/disable`, `POST /users/:id/reset-password`. **Não existe**
  `POST /users/invitations` nem `POST /users/:id/resend-invite`.
* `clients.py` já proxeia `GET/POST /clients` e `GET/PATCH /client-context`
  para o Client Service — portanto `/clients` pode funcionar de verdade assim
  que o Client Service (Fase 6) estiver de pé; hoje, sem o serviço rodando,
  a Web mostra `ServiceUnavailableState` normalmente.

Ou seja: o fluxo de **convite por e-mail** (criação pendente, reenvio, aceite
público) está 100% implementado no frontend, mas depende de endpoints novos
no `identity-service`/BFF que ainda não existem. O fluxo de **cadastro de
clientes** depende apenas do Client Service (Fase 6) estar publicado e do BFF
já ter as rotas — o que já é o caso na camada de roteamento.

## Como a Web se comporta quando um serviço está ausente

Em qualquer chamada (listagem, criação, convite, aceite, reenvio,
desativação): 404/501/503 (ou falha de rede) nunca aparece como erro bruto.
A tela mostra `ServiceUnavailableState` com o texto:

> Serviço ainda não disponível — Esta tela já está preparada no frontend, mas
> o endpoint necessário ainda não está disponível no BFF. Quando o serviço
> for ativado, esta funcionalidade passará a funcionar sem alterar a
> interface.

Formulários seguem a mesma regra, mas permanecem visíveis e preenchíveis;
apenas o envio final é bloqueado com uma mensagem específica do fluxo (ver
seções de cada fluxo acima). 401 dispara o mesmo redirecionamento para
`/login` já existente na Fase 5 (via `sessionExpiredHandler`); 403 aciona
`ForbiddenState`/`RequirePermission`.

## Permissões usadas

```txt
clients:read     — ver /clients e o botão de busca
clients:create   — botão "Novo cliente" e envio do formulário
users:read       — ver /users e o item de menu "Usuários"
users:create     — botão "Novo usuário", envio do convite, reenvio de convite
users:update     — reenvio de convite (alternativa a users:create)
users:disable    — botão "Desativar" na listagem de usuários
```

Nenhuma permissão nova foi inventada além das já documentadas na Fase 4/4.1/6.
Onde a permissão ainda não existe no contrato RBAC atual (ex.: papéis dentro
do cliente), o campo correspondente fica desabilitado com uma explicação em
vez de quebrar o formulário.

## Decisões de design

* Reaproveitado 100% o design system existente (`ThemeSurface`, `Badge`,
  `Button`, `Input`, `Label`, paleta slate/ciano/violeta) — nenhuma biblioteca
  de UI nova foi adicionada.
* Formulários usam `useState` simples, no mesmo padrão do `LoginForm` já
  existente, para não introduzir `react-hook-form`/`zod` como dependência
  nova sem necessidade.
* `FormDrawer` (painel lateral) foi escolhido em vez de modal central para
  manter espaço suficiente para formulários maiores (cliente tem 10 campos).
* Tabela de usuários usa HTML semântico (`<table>`) em vez de divs, para
  acessibilidade e leitura por leitor de tela.

## Arquivos criados

```txt
src/lib/api/error-utils.ts
src/lib/api/clients-api.ts
src/lib/api/users-api.ts
src/lib/validation/cnpj.ts
src/lib/validation/cnpj.test.ts
src/lib/api/error-utils.test.ts
src/components/states/service-unavailable-state.tsx
src/components/states/form-error-state.tsx
src/components/states/inline-field-error.tsx
src/components/states/success-notice.tsx
src/components/states/pending-notice.tsx
src/components/badges/client-status-badge.tsx
src/components/badges/user-status-badge.tsx
src/components/badges/invite-status-badge.tsx
src/components/badges/role-badge.tsx
src/components/ui/form-drawer.tsx
src/components/ui/data-toolbar.tsx
src/features/clients/client-form.tsx
src/features/users/invite-user-form.tsx
src/app/(app)/users/page.tsx
src/app/(app)/users/users.test.tsx
src/app/(app)/settings/services/page.tsx
src/app/accept-invite/page.tsx
src/app/accept-invite/accept-invite.test.tsx
src/app/(app)/clients/clients.test.tsx
src/types/lucide-react.d.ts   (ver "Limitações conhecidas")
docs/fase-5.1-web-operacional-admin.md
```

## Arquivos alterados

```txt
src/types/api.ts                          — novos tipos (ClientRecord, UserRecord, ApiErrorCode, etc.)
src/lib/api/auth-api.ts                   — getInvitation, acceptInvitation
src/app/(app)/clients/page.tsx            — reescrita completa (listagem real + criação)
src/components/layout/navigation.ts       — grupo "Administração" e "Status dos serviços"
src/test/fixtures.ts                      — adminUser, clientRecord, userRecord
src/features/auth/permissions.test.tsx    — cobre item "Usuários" no menu
```

## Testes adicionados

45 testes no total (suíte completa), incluindo os novos:

* `clients.test.tsx` (5) — renderiza sem quebrar, `ServiceUnavailableState`
  sem endpoint, validação de campos obrigatórios/CNPJ, sucesso apenas com
  confirmação do BFF + reload da lista, nenhum cliente fake quando o
  endpoint de criação não existe.
* `users.test.tsx` (5) — idem para usuários e convite.
* `accept-invite.test.tsx` (4) — renderiza com token, convite inválido sem
  token, `ServiceUnavailableState` quando o endpoint não existe, validação de
  senha/confirmação.
* `error-utils.test.ts` (6) — mapeamento de cada status HTTP para
  `ApiErrorCode`.
* `cnpj.test.ts` (6) — validação de CNPJ real (dígitos verificadores),
  rejeição de sequência repetida e de quantidade errada de dígitos.
* `permissions.test.tsx` — ampliado para confirmar que "Usuários" some do
  menu sem `users:read` e aparece para quem tem a permissão.

## Comandos executados

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

## Resultados

* **Lint:** 0 erros, 0 avisos.
* **Typecheck:** 0 erros (ver nota abaixo sobre `lucide-react`).
* **Testes:** 45/45 passando (10 arquivos de teste).
* **Build:** não foi possível concluir `next build` neste ambiente de
  sandbox — ver "Limitações conhecidas".

## Limitações conhecidas

1. **`node_modules` desta instalação está incompleto para o SO Linux do
   sandbox de verificação** (foi originalmente instalado a partir de um
   Windows): faltam os binários nativos `@rolldown/binding-linux-x64-gnu`
   (usado pelo Vitest) e o pacote `lucide-react` instalado não inclui
   `dist/lucide-react.d.ts`. Isso afeta **todo** o projeto, inclusive
   arquivos que já existiam antes desta fase — não é um problema introduzido
   pelo código novo. Para não bloquear o typecheck, foi adicionado
   `src/types/lucide-react.d.ts`, uma declaração ambiente mínima com os
   ícones usados no projeto; ela deve ser removida assim que
   `npm install` for reexecutado em um ambiente com a instalação completa
   (o comentário no topo do arquivo documenta isso).
2. **`next build` não pôde ser executado até o fim neste sandbox**: a
   compilação com SWC nativo terminou em "Bus error", um sintoma típico de
   executar binários nativos (`.node`) a partir de um sistema de arquivos
   montado via FUSE sem suporte completo a `mmap`. Recomenda-se rodar
   `npm run build` no ambiente normal de desenvolvimento/CI (fora deste
   sandbox) para a verificação final antes do deploy.
3. O fluxo de convite (`POST /users/invitations`, `POST /users/:id/resend-invite`,
   `GET /auth/invitations/:token`, `POST /auth/invitations/:token/accept`)
   está pronto na Web mas depende de endpoints que ainda não existem no
   `identity-service`/BFF (ver seção acima). Até lá, a Web mostra
   `ServiceUnavailableState` de forma controlada.
4. O cadastro de clientes depende do Client Service (Fase 6) estar de pé;
   as rotas já existem no BFF (proxy), então basta subir o serviço.
5. Client roles (papel dentro do cliente, área de responsabilidade,
   responsável principal) descritos na seção 16 da especificação não têm
   contrato RBAC publicado ainda; o campo de vínculo com cliente no convite
   fica limitado a selecionar clientes (sem papel/área), e será estendido
   quando o contrato existir.

## Próximos passos recomendados

1. Implementar `POST /users/invitations`, `POST /users/:id/resend-invite`,
   `GET /auth/invitations/:token` e `POST /auth/invitations/:token/accept`
   no `identity-service`, expondo-os no BFF (`apps/bff/app/api/routes`).
2. Publicar o Client Service (Fase 6) em ambiente de desenvolvimento para
   validar `/clients` e `/users` (vínculo) de ponta a ponta.
3. Rodar `npm install` limpo em um ambiente Linux real (fora deste sandbox)
   e remover `src/types/lucide-react.d.ts` quando os tipos oficiais do pacote
   voltarem a ser resolvidos.
4. Rodar `npm run build` no CI/ambiente de desenvolvimento normal para
   confirmar o build de produção (não verificável neste sandbox).
5. Quando o contrato de papel/área por cliente existir, estender
   `InviteUserForm` para capturar papel no cliente, área de responsabilidade
   e responsável principal (seção 16 da especificação).

## Como validar manualmente

```powershell
docker compose up -d --build identity-service client-service bff
cd apps/web
npm run dev
```

1. Login como administrador.
2. Abrir `/clients`: com Client Service fora do ar, deve aparecer
   `ServiceUnavailableState`; com o serviço no ar, deve listar e permitir
   criar cliente.
3. Abrir `/users`: deve listar usuários reais (Identity Service já suporta
   `GET /users`); clicar em "Novo usuário" deve mostrar o formulário e, ao
   enviar, mostrar "Convite ainda não disponível" (endpoint ainda não existe).
4. Abrir `/accept-invite?token=qualquer` deslogado: deve mostrar
   `ServiceUnavailableState` específico de convite (endpoint ainda não
   existe).
5. Abrir `/settings/services`: deve mostrar o status real de cada endpoint
   testado.
