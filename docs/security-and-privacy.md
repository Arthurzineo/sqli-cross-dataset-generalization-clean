# Segurança e privacidade

- Nenhuma chave real de API, token GitHub ou chave privada foi encontrada na
  varredura inicial por padrões.
- As aplicações de laboratório agora exigem `LAB_JWT_SECRET` no ambiente; os
  exemplos `.env.example` não contêm valor.
- Configurações e logs operacionais reais não foram copiados.
- A base `proprio` não foi copiada por conter potenciais identificadores.
- Antes de qualquer `git push`, repetir a varredura com scanner dedicado e
  revisar manualmente os achados genéricos de `token`, `password` e `secret`.

