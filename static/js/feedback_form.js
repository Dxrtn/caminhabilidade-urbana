// Formulário de feedback (spec 0006): contador de caracteres e localização opcional.
// A posição só vai para os campos ocultos se o usuário permitir; o servidor não a guarda.
(function () {
  "use strict";

  // ---------- contador de caracteres da descrição
  document.querySelectorAll("textarea[data-contador]").forEach(function (campo) {
    var maximo = Number(campo.getAttribute("maxlength")) || 500;
    var contador = document.createElement("p");
    contador.className = "helptext";
    contador.id = campo.id + "_contador";
    contador.setAttribute("aria-live", "polite");
    campo.insertAdjacentElement("afterend", contador);
    var descritores = (campo.getAttribute("aria-describedby") || "").split(" ").filter(Boolean);
    descritores.push(contador.id);
    campo.setAttribute("aria-describedby", descritores.join(" "));

    function atualizar() {
      contador.textContent = campo.value.length + " de " + maximo + " caracteres";
    }
    campo.addEventListener("input", atualizar);
    atualizar();
  });

  // ---------- localização
  var latitude = document.getElementById("id_latitude");
  var longitude = document.getElementById("id_longitude");
  var status = document.getElementById("status-localizacao");
  if (!latitude || !longitude || !("geolocation" in navigator)) {
    return;
  }
  navigator.geolocation.getCurrentPosition(
    function (posicao) {
      latitude.value = posicao.coords.latitude.toFixed(6);
      longitude.value = posicao.coords.longitude.toFixed(6);
      if (status) { status.textContent = "Localização obtida para conferir a distância até o trecho."; }
    },
    function () {
      latitude.value = "";
      longitude.value = "";
      if (status) { status.textContent = "Sem localização: o feedback será enviado normalmente."; }
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
  );
})();
