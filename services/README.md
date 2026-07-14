# Services

Serviços de domínio da CCI. A arquitetura oficial atual usa poucos serviços principais, cada um com módulos internos bem isolados e preparados para extração futura.

## Serviços canônicos

- `identity-service`: usuários, autenticação, roles, permissões, convites e sessões.
- `client-service`: clientes, CNPJ, competências, vínculos, permissões por cliente e pasta padrão.
- `document-service`: documentos, uploads, storage, duplicidade, status e preview estruturado.
- `template-service`: templates, categorias, campos/objetos, anotações, matching e versionamento.
- `extraction-service`: jobs, orquestração, resultados, evidências, normalização, confiança e revisão.
- `rule-service`: DSL, regras, operadores, fórmulas, simulação, publicação e versões.
- `conference-service`: modelos, execuções, documentos esperados, rule sets, resultado consolidado, auditoria, timeline e agenda.
- `report-service`: relatórios PDF/Excel, documentos anotados e exportações.

## Estado físico atual

`identity-service`, `client-service` e `document-service` já possuem implementação. Outros diretórios podem ser scaffolds legados da arquitetura granular anterior, como `conference-model-service`, `document-ingestion-service`, `document-classification-service`, `extraction-orchestrator`, `normalization-service`, `variable-registry-service`, `execution-control-service`, `result-service`, `audit-service`, `log-service` e `schedule-service`.

Esses diretórios antigos não são a divisão oficial de domínios. Quando uma fase futura retomar essas capacidades, elas devem ser incorporadas como módulos dos serviços canônicos, salvo decisão arquitetural explícita em contrário.

Regra:

```text
Serviço separa domínio.
Módulo separa responsabilidade interna.
Módulo extraível usa contrato público, portas/adapters, eventos e testes próprios.
```
