(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("transportQtyInput");
    const display = document.getElementById("transportQtyDisplay");
    if (!input || !display) {
      return;
    }

    document.querySelectorAll("[data-qty-change]").forEach(function (button) {
      button.addEventListener("click", function () {
        const delta = Number(button.dataset.qtyChange || 0);
        const current = Number(input.value || 1);
        const next = Math.max(1, current + delta);
        input.value = next;
        display.textContent = String(next);
      });
    });
  });
})();
