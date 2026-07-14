# Rule Schema

Contrato canônico de regras versionadas da CCI. Define identidade, cliente/modelo, versão, estado, campos/objetos obrigatórios e árvore lógica segura.

Será usado por `rule-service`, `rule-worker`, Web Rule Builder visual e auditoria/timeline do `conference-service`. Regras publicadas nunca são sobrescritas: alterações geram nova versão. O schema não executa regras nem permite código arbitrário. Campos com nome histórico `required_variables` permanecem até uma migração explícita de contrato.

Exemplos cobrem `equals`, `exists` e `sum_equals`.
