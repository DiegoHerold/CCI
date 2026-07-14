# Variable Schema

Contrato histórico da Fase 2 para o dado normalizado consumido pelas regras. Uma variável mantém chave estável, valor tipado, valor bruto, confiança, status e evidência de origem.

Na arquitetura alvo, esse vocabulário evolui para campos/objetos extraídos sob responsabilidade do `extraction-service`, com evidências em `evidence-schema` e revisão explícita. Não existe mais um `variable-registry-service` como serviço canônico separado.

Regra arquitetural: regras recebem campos/objetos extraídos e normalizados conforme contrato compartilhado; regras nunca leem PDF, Excel, TXT, Word ou imagens diretamente.
