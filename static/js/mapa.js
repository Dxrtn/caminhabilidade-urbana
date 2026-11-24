// Mapa público (spec 0005): trechos por classificação, filtros, busca e localização.
// O conteúdo vindo do servidor entra só por textContent, nunca como HTML.
(function () {
  "use strict";

  var elementoMapa = document.getElementById("mapa");
  if (!elementoMapa || typeof L === "undefined") {
    return;
  }

  var CENTRO_MACEIO = [-9.6658, -35.7350];
  var ZOOM_INICIAL = 15;
  // Cor e padrão de linha (RF-10): a classificação nunca depende só da cor.
  var ESTILOS = {
    ACESSIVEL: { color: "#1b7f3b", dashArray: null, rotulo: "Acessível" },
    PARCIAL: { color: "#9a6700", dashArray: "12 8", rotulo: "Parcialmente acessível" },
    INACESSIVEL: { color: "#c62828", dashArray: "2 8", rotulo: "Inacessível" },
    SEM_AVALIACAO: { color: "#6b6b6b", dashArray: "20 6 2 6", rotulo: "Sem avaliação" },
  };

  var urlTrechos = elementoMapa.dataset.apiTrechos;
  var urlBusca = elementoMapa.dataset.apiBusca;
  var urlDetalhe = elementoMapa.dataset.urlDetalhe; // termina em /0/
  var status = document.getElementById("mapa-status");
  var filtroClassificacao = document.getElementById("filtro-classificacao");
  var filtroObstaculo = document.getElementById("filtro-obstaculo");
  var trechoPedido = new URLSearchParams(window.location.search).get("trecho");

  var mapa = L.map(elementoMapa).setView(CENTRO_MACEIO, ZOOM_INICIAL);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    // A política de uso dos tiles do OSM bloqueia navegadores que não mandam Referer, e o
    // Django usa "same-origin" no site todo. Aqui, só para os tiles, envia apenas a origem.
    referrerPolicy: "strict-origin-when-cross-origin",
  }).addTo(mapa);

  var camada = L.layerGroup().addTo(mapa);
  var linhasPorId = {};
  var marcadorUsuario = null;

  function avisar(texto) {
    status.textContent = texto;
  }

  // ---------- popups e linhas

  function criarPopup(trecho) {
    var caixa = document.createElement("div");
    caixa.className = "popup-trecho";
    var titulo = document.createElement("strong");
    titulo.textContent = trecho.logradouro;
    var bairro = document.createElement("p");
    bairro.textContent = trecho.bairro;
    var classificacao = document.createElement("p");
    classificacao.textContent = "Classificação: " + trecho.classificacao_rotulo;
    caixa.append(titulo, bairro, classificacao);
    if (trecho.feedbacks_em_analise > 0) {
      var analise = document.createElement("p");
      analise.textContent = trecho.feedbacks_em_analise + " relato(s) em análise";
      caixa.append(analise);
    }
    var link = document.createElement("a");
    link.href = urlDetalhe.replace(/0\/$/, trecho.id + "/");
    link.textContent = "Ver detalhes";
    caixa.append(link);
    return caixa;
  }

  function desenhar(trechos) {
    camada.clearLayers();
    linhasPorId = {};
    trechos.forEach(function (trecho) {
      var estilo = ESTILOS[trecho.classificacao] || ESTILOS.SEM_AVALIACAO;
      var linha = L.polyline(trecho.coordenadas, {
        color: estilo.color,
        dashArray: estilo.dashArray,
        weight: 7,
        opacity: 0.9,
      });
      linha.bindPopup(criarPopup(trecho));
      linha.addTo(camada);
      linhasPorId[trecho.id] = linha;
    });
    avisar(trechos.length + (trechos.length === 1 ? " trecho no mapa." : " trechos no mapa."));
  }

  function carregarTrechos() {
    var parametros = new URLSearchParams();
    if (filtroClassificacao.value) { parametros.set("classificacao", filtroClassificacao.value); }
    if (filtroObstaculo.value) { parametros.set("obstaculo", filtroObstaculo.value); }
    return fetch(urlTrechos + "?" + parametros.toString(), { headers: { Accept: "application/json" } })
      .then(function (resposta) { return resposta.json(); })
      .then(function (dados) { desenhar(dados.trechos); })
      .catch(function () { avisar("Não foi possível carregar os trechos. Tente de novo."); });
  }

  function focarTrecho(id, centro) {
    var linha = linhasPorId[id];
    if (linha) {
      mapa.fitBounds(linha.getBounds(), { maxZoom: 18, padding: [40, 40] });
      linha.openPopup();
    } else if (centro) {
      mapa.setView(centro, 18); // o trecho pode estar escondido pelos filtros
      avisar("O trecho está fora dos filtros atuais.");
    }
  }

  // ---------- legenda

  var legenda = L.control({ position: "bottomright" });
  legenda.onAdd = function () {
    var caixa = L.DomUtil.create("div", "legenda-mapa");
    var titulo = document.createElement("strong");
    titulo.textContent = "Legenda";
    caixa.append(titulo);
    Object.keys(ESTILOS).forEach(function (chave) {
      var estilo = ESTILOS[chave];
      var item = document.createElement("div");
      item.className = "legenda-mapa__item";
      var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("width", "40");
      svg.setAttribute("height", "10");
      svg.setAttribute("aria-hidden", "true");
      var traco = document.createElementNS("http://www.w3.org/2000/svg", "line");
      traco.setAttribute("x1", "0");
      traco.setAttribute("y1", "5");
      traco.setAttribute("x2", "40");
      traco.setAttribute("y2", "5");
      traco.setAttribute("stroke", estilo.color);
      traco.setAttribute("stroke-width", "5");
      if (estilo.dashArray) { traco.setAttribute("stroke-dasharray", estilo.dashArray); }
      svg.append(traco);
      var texto = document.createElement("span");
      texto.textContent = estilo.rotulo;
      item.append(svg, texto);
      caixa.append(item);
    });
    return caixa;
  };
  legenda.addTo(mapa);

  // ---------- localização (RF-12)

  function localizar(centralizar) {
    if (!("geolocation" in navigator)) {
      avisar("Seu navegador não informa a localização.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      function (posicao) {
        var ponto = [posicao.coords.latitude, posicao.coords.longitude];
        if (marcadorUsuario) { mapa.removeLayer(marcadorUsuario); }
        marcadorUsuario = L.circleMarker(ponto, {
          radius: 9, color: "#0b4f8a", fillColor: "#ffffff", fillOpacity: 1, weight: 4,
        }).addTo(mapa).bindTooltip("Você está aqui");
        if (centralizar) { mapa.setView(ponto, 17); }
      },
      function () {
        avisar("Sem acesso à localização: mostrando o centro de Maceió.");
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }

  document.getElementById("minha-localizacao").addEventListener("click", function () {
    localizar(true);
  });

  // ---------- busca (RF-13)

  var campoBusca = document.getElementById("busca-texto");
  var avisoBusca = document.getElementById("busca-aviso");
  var listaResultados = document.getElementById("busca-resultados");
  var espera = null;

  function mostrarResultados(resultados) {
    listaResultados.replaceChildren();
    resultados.forEach(function (resultado) {
      var item = document.createElement("li");
      var botao = document.createElement("button");
      botao.type = "button";
      botao.className = "busca__resultado";
      var nome = document.createElement("strong");
      nome.textContent = resultado.logradouro;
      var extra = document.createElement("span");
      extra.textContent = resultado.bairro + " · " + resultado.referencias;
      botao.append(nome, extra);
      botao.addEventListener("click", function () {
        listaResultados.hidden = true;
        campoBusca.value = resultado.logradouro;
        focarTrecho(resultado.id, resultado.centro);
      });
      item.append(botao);
      listaResultados.append(item);
    });
    listaResultados.hidden = resultados.length === 0;
  }

  function buscar() {
    var texto = campoBusca.value.trim();
    if (!texto) {
      mostrarResultados([]);
      avisoBusca.textContent = "";
      return;
    }
    fetch(urlBusca + "?" + new URLSearchParams({ q: texto }).toString(), { headers: { Accept: "application/json" } })
      .then(function (resposta) { return resposta.json(); })
      .then(function (dados) {
        mostrarResultados(dados.resultados);
        if (dados.aviso) {
          avisoBusca.textContent = dados.aviso;
        } else if (dados.resultados.length === 0) {
          avisoBusca.textContent = "Nenhum trecho encontrado.";
        } else {
          avisoBusca.textContent = dados.resultados.length + " resultado(s).";
        }
      })
      .catch(function () { avisoBusca.textContent = "Não foi possível buscar agora."; });
  }

  campoBusca.addEventListener("input", function () {
    window.clearTimeout(espera);
    espera = window.setTimeout(buscar, 300);
  });
  campoBusca.addEventListener("keydown", function (evento) {
    if (evento.key === "ArrowDown" && !listaResultados.hidden) {
      evento.preventDefault();
      listaResultados.querySelector("button").focus();
    }
  });
  listaResultados.addEventListener("keydown", function (evento) {
    var botoes = Array.prototype.slice.call(listaResultados.querySelectorAll("button"));
    var posicao = botoes.indexOf(document.activeElement);
    if (evento.key === "ArrowDown" && posicao < botoes.length - 1) {
      evento.preventDefault();
      botoes[posicao + 1].focus();
    } else if (evento.key === "ArrowUp") {
      evento.preventDefault();
      (posicao > 0 ? botoes[posicao - 1] : campoBusca).focus();
    } else if (evento.key === "Escape") {
      listaResultados.hidden = true;
      campoBusca.focus();
    }
  });

  // ---------- início

  filtroClassificacao.addEventListener("change", carregarTrechos);
  filtroObstaculo.addEventListener("change", carregarTrechos);

  carregarTrechos().then(function () {
    if (trechoPedido) {
      focarTrecho(Number(trechoPedido), null);
    }
  });
  if (!trechoPedido) {
    localizar(true);
  }
})();
