# ADR 0006: Mapa com Leaflet e OpenStreetMap, com trecho representado por dois pontos

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

O mapa é a tela principal do sistema. Serviços como Google Maps exigem chave de API e cobrança. O documento de requisitos prevê o traçado do trecho desenhado à mão no mapa e uma busca de endereços em serviço externo, o que aumentaria muito o trabalho do protótipo.

## Decisão

- O mapa usa a biblioteca Leaflet 1.9.4, carregada por CDN, com o mapa base do OpenStreetMap e a atribuição exigida pela licença.
- Cada trecho é uma linha reta entre o ponto de início e o ponto de fim, guardados como latitude e longitude (`DecimalField(max_digits=9, decimal_places=6)`), sem extensão geográfica como PostGIS.
- A busca consulta apenas logradouros e bairros da própria base de trechos.

## Consequências

- Não há custo nem chave de API.
- Trechos em curva aparecem como uma linha reta entre os pontos.
- Cálculos de distância usam a fórmula de Haversine em Python, suficiente para a regra de 200 m.
- A busca não encontra endereços que não tenham trechos cadastrados.
