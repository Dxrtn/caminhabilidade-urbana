# ADR 0002: Usuário customizado com login por e-mail

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

O documento de requisitos identifica o usuário por e-mail e celular, sem nome de usuário. O `User` padrão do Django exige `username`, e trocar o modelo de usuário depois da primeira migração é trabalhoso.

## Decisão

O projeto usa o model `contas.Usuario`, que herda de `AbstractUser`, remove o campo `username` e usa `email` como `USERNAME_FIELD`. O model é definido antes da primeira migração ([spec 0001](../specs/0001-fundacao.md)), com um manager próprio para criar usuários e superusuários.

O administrador é um usuário com `is_staff = True`. Não há outros perfis nesta versão.

## Consequências

- O login usa e-mail e senha, como o usuário espera.
- O manager próprio é mais código para manter e testar.
- `login()` e `logout()` continuam na view, pois alteram a sessão HTTP.
