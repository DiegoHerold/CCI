# Field Schema

Contrato de campos e objetos extraíveis. Paths estáveis como `empresa.cnpj`, `periodo.competencia` e `contas[].saldo_atual` substituem gradualmente o catálogo histórico de variáveis.

`variable-schema` permanece compatível até uma migração explícita; novos contratos devem preferir `FieldDefinition` e evidências separadas.
