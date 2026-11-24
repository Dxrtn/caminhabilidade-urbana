# ADR 0001: MVT com camada de service e views baseadas em `View`

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

No Django, a regra de negócio costuma se espalhar entre views, forms, models e signals. Isso dificulta encontrar a regra, testá-la sem HTTP e reutilizá-la, por exemplo no comando de carga de trechos e nas páginas de administração.

As generic views reduzem código, mas escondem o fluxo em herança e tendem a levar regra de negócio para métodos sobrescritos.

## Decisão

O projeto segue MVT, com todas as regras de negócio em uma camada de service que não conhece HTTP. Toda view é uma classe que herda diretamente de `django.views.View`, sem views baseadas em função nem generic views.

As regras de cada camada estão em [`docs/arquitetura.md`](../arquitetura.md).

## Consequências

- As regras podem ser testadas sem cliente HTTP.
- O comando de carga de trechos e as páginas de administração reaproveitam os mesmos services.
- Há mais código repetitivo nas views, principalmente em formulários.
- O `ModelForm.save()` não é usado, pois a gravação é feita pelo service.
- Um teste automatizado verifica a herança das views ([spec 0001](../specs/0001-fundacao.md)).
