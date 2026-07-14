# Fase 2 — Packages compartilhados

## Objetivo

Definir os contratos oficiais antes da implementação dos serviços. JSON Schema é canônico; Pydantic atende Python e interfaces/types atendem TypeScript.

## Limites

Os packages contêm somente tipos, enums, validações puras, exemplos e o motor de regras em memória. Não há persistência, transporte, autenticação real, extração ou processamento de arquivos.

## Fluxo contratual

Documentos preservam integridade e storage; evidências localizam a origem; campos/objetos extraídos guardam valor bruto, valor normalizado, tipo, confiança e status; regras versionadas referenciam esses campos/objetos; o rule-engine avalia o mapa em memória; eventos versionados carregam o resultado entre domínios no futuro.

O package `variable-schema` criado nesta fase é histórico e representa o primeiro contrato de valores normalizados consumidos por regras. Na arquitetura alvo, ele evolui para `extraction-schema`, `evidence-schema` e, quando necessário, `field-schema`, mantendo compatibilidade até uma migração explícita.

## Testes

```bash
pip install -r packages/requirements-test.txt
pytest packages
```

Os testes validam exemplos contra JSON Schema, matriz de autorização e todos os operadores iniciais do rule-engine.
