# Temporal

Orquestrador local de workflows duráveis. Usa PostgreSQL exclusivo, separado do banco da aplicação.

Será usado para extrações, OCR, IA assistida, execução de regras, conferências, geração de relatórios e reprocessamentos. Esta tarefa não cria workflows.

O namespace local sugerido é `cci-development`. `dynamicconfig/development.yaml` mantém somente opções mínimas de desenvolvimento; namespaces e políticas de retenção devem ser criados explicitamente antes de uso real.
