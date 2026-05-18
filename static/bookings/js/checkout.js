(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const checkoutForm = document.querySelector(".checkout-form");
    const container = document.getElementById("selectedServicesInputs");
    if (container) {
      const syncHiddenInputs = function () {
        container.innerHTML = "";
        document.querySelectorAll(".checkout-service-card").forEach(function (card) {
          const button = card.querySelector(".checkout-service-toggle");
          if (!button || !button.classList.contains("is-selected")) {
            return;
          }
          const input = document.createElement("input");
          input.type = "hidden";
          input.name = "selected_services";
          input.value = card.dataset.serviceId;
          container.appendChild(input);
        });
      };

      document.querySelectorAll(".checkout-service-toggle").forEach(function (button) {
        button.addEventListener("click", function () {
          button.classList.toggle("is-selected");
          button.textContent = button.classList.contains("is-selected") ? "- Quitar" : "+ Agregar";
          syncHiddenInputs();
        });
      });

      syncHiddenInputs();
    }

    const passwordInput = document.getElementById("id_register-password1");
    const hintsNode = document.getElementById("checkoutPasswordHints");
    const firstNameInput = document.getElementById("id_register-first_name");
    const emailInput = document.getElementById("id_register-email");

    if (!passwordInput || !hintsNode) {
      if (checkoutForm) {
        checkoutForm.addEventListener("submit", function (event) {
          let hasErrors = false;
          checkoutForm.querySelectorAll("[data-required-field]").forEach(function (field) {
            const value = (field.value || "").trim();
            const isEmpty = !value;
            field.classList.toggle("is-invalid", isEmpty);
            if (isEmpty) {
              hasErrors = true;
            }
          });
          if (hasErrors) {
            event.preventDefault();
          }
        });
      }
      return;
    }

    const commonPasswords = new Set([
      "12345678",
      "password",
      "password123",
      "qwerty123",
      "123456789",
      "admin123",
      "welcome123",
    ]);

    const normalize = function (value) {
      return (value || "").toLowerCase().replace(/\s+/g, "");
    };

    const validatePassword = function () {
      const password = passwordInput.value || "";
      const normalizedPassword = normalize(password);
      const normalizedName = normalize(firstNameInput ? firstNameInput.value : "");
      const normalizedEmail = normalize(emailInput ? emailInput.value : "").split("@")[0];
      const errors = [];

      if (!password) {
        hintsNode.hidden = true;
        hintsNode.innerHTML = "";
        passwordInput.classList.remove("is-invalid", "is-valid");
        return;
      }

      if (normalizedName && normalizedPassword.includes(normalizedName)) {
        errors.push("Your password can’t be too similar to your other personal information.");
      }

      if (normalizedEmail && normalizedEmail.length >= 3 && normalizedPassword.includes(normalizedEmail)) {
        errors.push("Your password can’t be too similar to your other personal information.");
      }

      if (password.length < 8) {
        errors.push("Your password must contain at least 8 characters.");
      }

      if (commonPasswords.has(normalizedPassword)) {
        errors.push("Your password can’t be a commonly used password.");
      }

      if (/^\d+$/.test(password)) {
        errors.push("Your password can’t be entirely numeric.");
      }

      hintsNode.hidden = false;

      if (errors.length) {
        passwordInput.classList.add("is-invalid");
        passwordInput.classList.remove("is-valid");
        hintsNode.classList.remove("checkout-password-hints--valid");
        hintsNode.innerHTML = errors
          .filter(function (item, index, list) {
            return list.indexOf(item) === index;
          })
          .map(function (item) {
            return "<li>" + item + "</li>";
          })
          .join("");
        return;
      }

      passwordInput.classList.remove("is-invalid");
      passwordInput.classList.add("is-valid");
      hintsNode.classList.add("checkout-password-hints--valid");
      hintsNode.innerHTML = "<li>Contrasena valida.</li>";
    };

    passwordInput.addEventListener("input", validatePassword);
    passwordInput.addEventListener("blur", validatePassword);
    if (firstNameInput) {
      firstNameInput.addEventListener("input", validatePassword);
    }
    if (emailInput) {
      emailInput.addEventListener("input", validatePassword);
    }

    if (checkoutForm) {
      checkoutForm.addEventListener("submit", function (event) {
        let hasErrors = false;
        checkoutForm.querySelectorAll("[data-required-field]").forEach(function (field) {
          const value = (field.value || "").trim();
          const isEmpty = !value;
          field.classList.toggle("is-invalid", isEmpty);
          if (isEmpty) {
            hasErrors = true;
          }
        });

        [firstNameInput, emailInput, passwordInput].forEach(function (field) {
          if (!field) {
            return;
          }
          const isEmpty = !(field.value || "").trim();
          field.classList.toggle("is-invalid", isEmpty);
          if (isEmpty) {
            hasErrors = true;
          }
        });

        validatePassword();
        if (passwordInput.classList.contains("is-invalid")) {
          hasErrors = true;
        }

        if (hasErrors) {
          event.preventDefault();
        }
      });
    }
  });
})();
