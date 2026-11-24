// Pede confirmação antes de enviar formulários marcados com data-confirmar (desativar/reativar trecho).
(function () {
  "use strict";

  document.querySelectorAll("form[data-confirmar]").forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      if (!window.confirm(formulario.dataset.confirmar)) {
        evento.preventDefault();
      }
    });
  });
})();
