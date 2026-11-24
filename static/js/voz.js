// Leitura em voz do detalhe do trecho (RF-17). Sem suporte no navegador, os botões ficam escondidos.
(function () {
  "use strict";

  var ouvir = document.getElementById("ouvir");
  var parar = document.getElementById("parar-voz");
  if (!ouvir || !("speechSynthesis" in window) || typeof SpeechSynthesisUtterance === "undefined") {
    return;
  }

  ouvir.hidden = false;

  ouvir.addEventListener("click", function () {
    window.speechSynthesis.cancel();
    var fala = new SpeechSynthesisUtterance(ouvir.dataset.textoVoz);
    fala.lang = "pt-BR";
    fala.onend = function () { parar.hidden = true; };
    fala.onerror = function () { parar.hidden = true; };
    parar.hidden = false;
    window.speechSynthesis.speak(fala);
  });

  parar.addEventListener("click", function () {
    window.speechSynthesis.cancel();
    parar.hidden = true;
    ouvir.focus();
  });
})();
