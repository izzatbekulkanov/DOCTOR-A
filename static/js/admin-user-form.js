(function () {
  "use strict";

  function formatUzbekPhone(value) {
    let digits = (value || "").replace(/\D/g, "");
    if (digits.startsWith("998")) {
      digits = digits.slice(3);
    }
    digits = digits.slice(0, 9);

    if (!digits.length) {
      return "";
    }

    let formatted = "+998";
    if (digits.length > 0) {
      formatted += " " + digits.slice(0, 2);
    }
    if (digits.length > 2) {
      formatted += " " + digits.slice(2, 5);
    }
    if (digits.length > 5) {
      formatted += " " + digits.slice(5, 7);
    }
    if (digits.length > 7) {
      formatted += " " + digits.slice(7, 9);
    }

    return formatted;
  }

  function initPhoneMasks() {
    document.querySelectorAll("[data-phone-format]").forEach(function (input) {
      const syncValue = function () {
        input.value = formatUzbekPhone(input.value);
      };

      syncValue();
      input.addEventListener("input", syncValue);
      input.addEventListener("focus", function () {
        if (!input.value) {
          input.value = "+998 ";
        }
      });
      input.addEventListener("blur", function () {
        if (input.value.trim() === "+998") {
          input.value = "";
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initPhoneMasks();
  });
})();
