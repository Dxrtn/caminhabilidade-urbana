# PRD 0001: Mapeamento de Caminhabilidade Urbana (protótipo)

- **Status:** Aceito
- **Data:** 2026-11-24
- **Origem:** [Documento de Requisitos completo](../requisitos/) da disciplina de Engenharia de Software. Os títulos das áreas abaixo indicam o requisito correspondente nesse documento (RF001 a RF012).
- **Especificações:** [fundação](../specs/0001-fundacao.md), [contas](../specs/0002-contas.md), [modelo de dados](../specs/0003-modelo-de-dados.md), [gestão de trechos](../specs/0004-gestao-de-trechos.md), [mapa e detalhes](../specs/0005-mapa-e-detalhes.md), [feedbacks](../specs/0006-feedbacks.md), [análise de feedbacks](../specs/0007-analise-de-feedbacks.md), [banco: permissões e exportação](../specs/0008-banco-permissoes-e-exportacao.md)

## Objetivo

No Brasil, cada proprietário constrói a calçada em frente ao imóvel, sem padronização. Pessoas com mobilidade reduzida não têm como saber, antes de sair, se o trajeto a pé até o destino é transitável.

O sistema mostra em um mapa as condições das calçadas de Maceió, trecho a trecho. A equipe mantém a base de trechos, e os usuários cadastrados a atualizam enviando feedbacks com foto, que a equipe analisa.

Esta versão é um **protótipo minimamente funcional**: implementa o ciclo completo do sistema (cadastro de trechos → consulta no mapa → envio de feedback → análise → atualização do trecho), com dados de exemplo, para demonstrar as funcionalidades reais. Não é o sistema completo descrito no documento de requisitos.

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Visitante | Qualquer pessoa, sem login | Consultar o mapa, buscar e ver os detalhes dos trechos |
| Usuário | Pessoa com conta verificada | Tudo o que o visitante faz, mais enviar e acompanhar feedbacks |
| Administrador | Integrante da equipe (`is_staff`) | Manter a base de trechos e analisar os feedbacks |

## Requisitos funcionais

### Cadastro (RF001)

- **RF-01:** O visitante cria uma conta informando nome completo, e-mail, celular, senha, confirmação de senha e aceite dos termos de uso. A forma de locomoção é opcional.
- **RF-02:** Um e-mail ou celular já usado em outra conta não pode ser cadastrado.
- **RF-03:** A senha tem de 8 a 64 caracteres, com ao menos uma letra e um número.
- **RF-04:** A conta só fica ativa depois que o usuário informa o código de 6 dígitos enviado ao celular, válido por 10 minutos.
- **RF-05:** O usuário pode pedir o reenvio do código até 3 vezes.

### Autenticação (RF002)

- **RF-06:** O usuário entra com e-mail e senha e sai do sistema.
- **RF-07:** Uma conta ainda não verificada não consegue entrar.
- **RF-08:** Somente administradores acessam as páginas de administração.

### Mapa (RF004)

- **RF-09:** A página inicial mostra o mapa com os trechos ativos, coloridos por classificação, sem exigir login.
- **RF-10:** A classificação de cada trecho é indicada por cor, padrão de linha e texto, nunca apenas pela cor.
- **RF-11:** O visitante filtra os trechos do mapa por classificação e por obstáculo.
- **RF-12:** Se o visitante permitir o acesso à localização, o mapa é centralizado na posição dele; caso contrário, no centro de Maceió.

### Busca (RF005)

- **RF-13:** O visitante busca trechos por logradouro ou bairro a partir de 3 caracteres e recebe até 5 resultados. Ao escolher um, o mapa é centralizado no trecho.

### Detalhes do trecho (RF006)

- **RF-14:** O detalhe do trecho mostra logradouro, referências de início e fim, lado da rua, bairro, classificação, obstáculos, fotos públicas e data da última atualização.
- **RF-15:** O detalhe mostra os 5 relatos mais recentes, sem identificar o autor. Relatos em análise aparecem sem fotos.
- **RF-16:** Se a última atualização tiver mais de 6 meses, o detalhe mostra um aviso destacado.

### Ouvir condições (RF012)

- **RF-17:** No detalhe, o visitante ouve em voz alta o logradouro, a classificação, os obstáculos e a data da última atualização.

### Enviar feedback (RF007)

- **RF-18:** O usuário envia um feedback sobre um trecho com tipo, obstáculos, classificação sugerida (opcional), descrição de 10 a 500 caracteres e até 3 fotos.
- **RF-19:** Um feedback do tipo "Novo problema" exige ao menos 1 obstáculo e 1 foto.
- **RF-20:** Cada usuário envia no máximo 10 feedbacks por dia.
- **RF-21:** Cada usuário tem no máximo 1 feedback em análise por trecho.
- **RF-22:** O envio de um feedback não altera a classificação do trecho.
- **RF-23:** Se o usuário estiver a mais de 200 m do trecho no envio, o feedback é marcado como "enviado à distância". A localização do usuário não é guardada.

### Meus feedbacks (RF008)

- **RF-24:** O usuário vê seus feedbacks com trecho, data, tipo, status e motivo da rejeição, 10 por página, do mais recente para o mais antigo.
- **RF-25:** O usuário exclui um feedback próprio que ainda esteja em análise.
- **RF-26:** O usuário recebe uma notificação no sistema quando o status de um feedback muda.

### Gestão de trechos (RF009)

- **RF-27:** O administrador cadastra e edita trechos com logradouro, bairro, referências de início e fim, lado da rua, coordenadas de início e fim, classificação, obstáculos, fotos e observações.
- **RF-28:** O administrador desativa um trecho. Trechos desativados não aparecem no mapa e não são excluídos.
- **RF-29:** Toda mudança de classificação de um trecho fica registrada em um histórico com classificação anterior, nova, autor e data.
- **RF-30:** O administrador pesquisa trechos por logradouro, bairro e classificação, e lista os trechos sem atualização há mais de 6 meses.
- **RF-31:** A equipe carrega trechos em lote por comando, a partir dos dados de exemplo do projeto ou de um arquivo CSV.

### Análise de feedbacks (RF010)

- **RF-32:** O administrador vê a fila de feedbacks em análise, do mais antigo para o mais recente.
- **RF-33:** Ao aceitar um feedback, o administrador pode atualizar a classificação e os obstáculos do trecho e escolher quais fotos se tornam públicas.
- **RF-34:** Ao rejeitar um feedback, o administrador informa o motivo, que é obrigatório.

## Requisitos não funcionais

- **RNF-01 (arquitetura):** O código segue as regras de [`docs/arquitetura.md`](../arquitetura.md) e demonstra os pilares de POO descritos em [`docs/poo.md`](../poo.md).
- **RNF-02 (interface):** Site responsivo, pensado primeiro para celular e utilizável a partir de 360 px de largura, em português do Brasil ([ADR 0003](../adr/0003-site-web-responsivo.md)).
- **RNF-03 (acessibilidade):** Todos os campos têm rótulo, imagens têm texto alternativo, áreas de toque têm no mínimo 44 × 44 px e o contraste de texto é de pelo menos 4,5:1.
- **RNF-04 (segurança):** Toda alteração de dados usa POST com proteção CSRF, o conteúdo enviado por usuários é escapado na exibição, as senhas usam o sistema do Django e uploads aceitam apenas imagens de até 5 MB.
- **RNF-05 (banco de dados):** PostgreSQL, com integridade de entidade, de domínio, referencial e definida pelo usuário declaradas no banco, além de trigger, índice, view e contas com permissões ([ADR 0004](../adr/0004-postgresql-como-banco-de-dados.md), [ADR 0007](../adr/0007-regras-de-integridade-no-banco.md)).
- **RNF-06 (privacidade):** O aceite dos termos é registrado com data e hora, e a localização do usuário não é armazenada.
- **RNF-07 (qualidade):** Cada requisito funcional tem pelo menos um teste automatizado, e `python manage.py test` passa por completo.

## Fora do escopo desta versão

- Aplicativo nativo para Android e iOS ([ADR 0003](../adr/0003-site-web-responsivo.md))
- Gerenciar conta e excluir conta (RF003 do documento de requisitos)
- Identificação de obstáculos por visão computacional (RF011 do documento de requisitos)
- Envio real de SMS: o código é exibido no terminal ([ADR 0005](../adr/0005-sms-simulado.md))
- Recuperação de senha, login por celular, bloqueio por tentativas e verificação em duas etapas
- Busca de endereços em serviço externo: a busca usa apenas a base de trechos
- Traçado do trecho desenhado à mão no mapa: o trecho é uma linha entre dois pontos ([ADR 0006](../adr/0006-mapa-com-leaflet-e-openstreetmap.md))
- Compressão e desfoque automático de fotos, e suspensão automática de contas
- Painel para a prefeitura, avaliação de estabelecimentos, sugestão de rotas e uso sem internet
- Deploy em produção

## Critérios de conclusão

1. Um administrador carrega os trechos de exemplo e eles aparecem no mapa, com cor, padrão e legenda.
2. Um visitante busca um trecho, abre o detalhe e ouve as condições em voz alta.
3. Um visitante cria uma conta, verifica o celular com o código exibido no terminal e envia um feedback com foto.
4. Um administrador aceita o feedback mudando a classificação: o mapa muda de cor, o histórico registra a mudança e o usuário recebe a notificação.
5. Tudo funciona em uma tela de celular.
6. Todos os requisitos funcionais têm testes, e a suíte passa.
