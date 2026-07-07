# Shared Types

Fonte comum para os tipos e estados centrais da CCI. O JSON Schema é canônico; `python/models.py` oferece modelos Pydantic e `typescript/index.ts` oferece interfaces equivalentes para serviços, workers, BFF e frontend.

Contém usuários, clientes, competências, documentos, variáveis, regras, execuções, resultados, auditoria, relatórios e envelope de eventos. Não contém persistência, autenticação real nem integrações.

O arquivo `examples/shared-types.example.json` demonstra objetos válidos. Novos estados devem ser adicionados primeiro ao schema canônico e depois refletidos em Python e TypeScript.
