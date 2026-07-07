# Variable Schema

Contrato canônico do dado normalizado consumido pelas regras. Uma variável mantém chave estável, valor tipado, valor bruto, confiança, status e evidência de origem.

Será usado por normalização, variable-registry-service, rule-service, rule-worker e auditoria. Este package não lê arquivos nem confirma dados; essas responsabilidades permanecem nos serviços apropriados.

Regra arquitetural: regras recebem variáveis conformes a este contrato e nunca leem PDF, Excel ou TXT diretamente.
