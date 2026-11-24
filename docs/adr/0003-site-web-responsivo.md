# ADR 0003: Site web responsivo no lugar do aplicativo nativo

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

O documento de requisitos descreve um aplicativo para celular (Android e iOS). O protótipo precisa ser entregue em poucos dias, em uma linguagem orientada a objetos e integrado a um banco relacional, para três disciplinas ao mesmo tempo. Um aplicativo nativo exigiria, além do back-end, uma segunda base de código e uma API completa.

## Decisão

O protótipo é um site web responsivo em Django, renderizado no servidor e pensado primeiro para telas de celular (a partir de 360 px de largura). Os recursos de celular que o sistema usa estão disponíveis no navegador: localização (Geolocation API), câmera para fotos (`<input type="file" accept="image/*" capture>`) e leitura em voz (Web Speech API).

## Consequências

- Uma única base de código atende celular e computador.
- Não é preciso publicar em lojas de aplicativos.
- O site não funciona sem internet, o que já estava fora do escopo.
- A experiência é a de um site, não a de um aplicativo instalado. Um aplicativo nativo continua previsto em versão futura e exigirá uma nova ADR.
