# ADR 0005: Envio de código por SMS simulado

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

O cadastro exige a verificação do celular por um código enviado por SMS. Serviços reais de SMS são pagos, exigem conta e chave de API, e não fazem sentido em um protótipo acadêmico. Ao mesmo tempo, o envio deve poder ser trocado por um serviço real sem alterar as regras do cadastro.

## Decisão

O envio fica atrás da classe abstrata `EnviadorDeCodigo`, que declara o método `enviar(celular, codigo)`. Há duas implementações:

- `EnviadorSmsSimulado`, usada no desenvolvimento, que exibe o código no terminal e no log.
- `EnviadorEmMemoria`, usada nos testes, que guarda os códigos enviados para conferência.

A classe usada é definida pela configuração `ENVIADOR_DE_CODIGO`. Os services de cadastro dependem apenas da classe abstrata.

## Consequências

- O cadastro pode ser demonstrado sem custo, lendo o código no terminal.
- Um envio real exigirá apenas uma nova subclasse e a troca da configuração.
- O sistema não comprova, de fato, que o celular pertence ao usuário nesta versão.
