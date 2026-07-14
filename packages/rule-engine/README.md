# Rule Engine

Motor inicial, puro e em memória para avaliar regras sobre um mapa de campos/objetos extraídos e normalizados. Será usado pelo `rule-service` para testes e pelo `rule-worker` para execução futura.

Operadores suportados: `equals`, `not_equals`, `greater_than`, `less_than`, `greater_or_equal`, `less_or_equal`, `exists`, `not_exists`, `difference_less_than`, `sum_equals`, `and` e `or`.

O motor não acessa arquivos, banco, APIs, mensageria ou Temporal. Não usa `eval` nem executa fórmulas livres; operadores novos devem ser funções puras adicionadas a `operators.py`, despachadas explicitamente em `engine.py` e cobertas por testes.

Uso:

```python
from engine import evaluate_rule

result = evaluate_rule(rule, variables)
print(result.status)
```

Campos/objetos ausentes geram `pending`, operador desconhecido gera `error`, comparações falsas geram `divergent` e comparações verdadeiras geram `approved`. O nome `variables` ainda aparece em APIs internas do package por compatibilidade da Fase 2.
