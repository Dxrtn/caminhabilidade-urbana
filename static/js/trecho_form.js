// Mapa do formulário de trecho (spec 0004): mostra a linha entre os dois pontos
// e preenche as coordenadas com cliques — o 1º define o início, o 2º o fim.
(function () {
  "use strict";

  var elementoMapa = document.getElementById("mapa-trecho");
  if (!elementoMapa || typeof L === "undefined") {
    return; // sem o Leaflet, os campos numéricos continuam funcionando
  }

  var campos = {
    latInicio: document.getElementById("id_lat_inicio"),
    lngInicio: document.getElementById("id_lng_inicio"),
    latFim: document.getElementById("id_lat_fim"),
    lngFim: document.getElementById("id_lng_fim"),
  };
  var CENTRO_MACEIO = [-9.6658, -35.7353];

  var mapa = L.map(elementoMapa).setView(CENTRO_MACEIO, 14);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">colaboradores do OpenStreetMap</a>',
    // Os tiles do OSM exigem Referer; o Django usa "same-origin" no site todo (veja mapa.js).
    referrerPolicy: "strict-origin-when-cross-origin",
  }).addTo(mapa);

  var marcadorInicio = null;
  var marcadorFim = null;
  var linha = null;
  var proximoClique = "inicio";

  function ler(campoLat, campoLng) {
    var lat = parseFloat(campoLat.value);
    var lng = parseFloat(campoLng.value);
    return isNaN(lat) || isNaN(lng) ? null : L.latLng(lat, lng);
  }

  function marcar(marcador, ponto, rotulo) {
    if (!ponto) {
      if (marcador) { mapa.removeLayer(marcador); }
      return null;
    }
    if (marcador) {
      marcador.setLatLng(ponto);
      return marcador;
    }
    return L.marker(ponto, { title: rotulo, alt: rotulo }).addTo(mapa);
  }

  function desenhar(ajustarVisao) {
    var inicio = ler(campos.latInicio, campos.lngInicio);
    var fim = ler(campos.latFim, campos.lngFim);
    marcadorInicio = marcar(marcadorInicio, inicio, "Início do trecho");
    marcadorFim = marcar(marcadorFim, fim, "Fim do trecho");
    if (linha) { mapa.removeLayer(linha); linha = null; }
    if (inicio && fim) {
      linha = L.polyline([inicio, fim], { color: "#0b4f8a", weight: 6 }).addTo(mapa);
      if (ajustarVisao) { mapa.fitBounds(linha.getBounds(), { maxZoom: 18, padding: [30, 30] }); }
    } else if (inicio && ajustarVisao) {
      mapa.setView(inicio, 17);
    }
  }

  mapa.on("click", function (evento) {
    var lat = evento.latlng.lat.toFixed(6);
    var lng = evento.latlng.lng.toFixed(6);
    if (proximoClique === "inicio") {
      campos.latInicio.value = lat;
      campos.lngInicio.value = lng;
      proximoClique = "fim";
    } else {
      campos.latFim.value = lat;
      campos.lngFim.value = lng;
      proximoClique = "inicio";
    }
    desenhar(false);
  });

  Object.keys(campos).forEach(function (chave) {
    campos[chave].addEventListener("change", function () { desenhar(true); });
  });

  desenhar(true);
})();
