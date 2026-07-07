# Rule Schema

Contrato canônico de regras versionadas da CCI. Define identidade, cliente/modelo, versão, estado, variáveis obrigatórias e árvore lógica segura.

Será usado por rule-service, rule-worker, editor visual e auditoria. Regras publicadas nunca são sobrescritas: alterações geram nova versão. O schema não executa regras nem permite código arbitrário.

Exemplos cobrem `equals`, `exists` e `sum_equals`.
