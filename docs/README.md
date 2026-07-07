# Documentação da CCI

- `contexto_mestre_conferencia_contabil.md`: visão canônica do produto e decisões arquiteturais.
- `arquitetura_conferencia_contabil.mmd`: diagrama Mermaid da arquitetura alvo.
- `fase-1a-chao-tecnico.md`: escopo e critérios técnicos desta fase.
- `fase-1b-templates-tecnicos.md`: padrões e geradores para APIs, orquestradores e workers.
- `fase-2-packages-compartilhados.md`: contratos canônicos e motor inicial de regras.
- `fase-3-bff-inicial.md`: primeira porta de entrada HTTP e placeholders para a web.
- `fase-4-identity-service.md`: usuários, JWT, RBAC, seed e integração com o BFF.
- `fase-4.1-identity-hardening.md`: sessões, refresh, revogação, bloqueio, rate limit e auditoria de identidade.

As decisões futuras devem preservar os limites entre Control Plane, Data Plane, workers, packages e infraestrutura.
