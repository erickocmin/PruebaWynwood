(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const methodInput = document.getElementById("paymentMethodInput");
    const optionButtons = document.querySelectorAll("[data-payment-option]");
    const cardPanel = document.querySelector('[data-payment-panel="card"]');
    const applePanel = document.querySelector('[data-payment-panel="apple"]');
    const googlePanel = document.querySelector('[data-payment-panel="google"]');
    const panels = {
      card: cardPanel,
      apple: applePanel,
      google: googlePanel,
    };
    const optionsWrap = document.querySelector("[data-payment-options]");
    const commonActions = document.querySelector("[data-payment-common-actions]");
    const paymentForm = document.querySelector(".checkout-payment-form");
    const appleModal = document.querySelector("[data-apple-modal]");
    const appleModalContinue = document.querySelector("[data-apple-modal-continue]");
    const appleModalClosers = document.querySelectorAll("[data-apple-modal-close]");
    const googleModal = document.querySelector("[data-google-modal]");
    const googleModalContinue = document.querySelector("[data-google-modal-continue]");
    const googleModalClosers = document.querySelectorAll("[data-google-modal-close]");
    const panelFields = new Map();
    let appleConfirmed = false;
    let googleConfirmed = false;

    Object.entries(panels).forEach(function ([key, panel]) {
      if (!panel) {
        return;
      }
      panelFields.set(
        key,
        Array.from(panel.querySelectorAll("input, select, textarea, button")).filter(function (field) {
          return field.type !== "button" && field.type !== "submit";
        })
      );
    });

    const syncPanelFields = function (method) {
      panelFields.forEach(function (fields, key) {
        const isActive = key === method;
        fields.forEach(function (field) {
          field.disabled = !isActive;
        });
      });
    };

    const toggleMethod = function (method) {
      if (methodInput) {
        methodInput.value = method;
      }
      optionButtons.forEach(function (button) {
        button.classList.toggle("is-selected", button.dataset.paymentOption === method);
      });
      Object.keys(panels).forEach(function (key) {
        panels[key]?.classList.toggle("is-visible", key === method);
      });
      optionsWrap?.classList.toggle("is-hidden", !!method);
      commonActions?.classList.toggle("is-hidden", method !== "card");
      syncPanelFields(method);
    };

    optionButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        toggleMethod(button.dataset.paymentOption);
      });
    });

    document.querySelectorAll(".checkout-payment-change").forEach(function (button) {
        button.addEventListener("click", function () {
        toggleMethod("");
      });
    });

    const closeAppleModal = function () {
      if (appleModal) {
        appleModal.hidden = true;
      }
    };

    const openAppleModal = function () {
      if (appleModal) {
        appleModal.hidden = false;
      }
    };

    const closeGoogleModal = function () {
      if (googleModal) {
        googleModal.hidden = true;
      }
    };

    const openGoogleModal = function () {
      if (googleModal) {
        googleModal.hidden = false;
      }
    };

    appleModalClosers.forEach(function (button) {
      button.addEventListener("click", closeAppleModal);
    });

    googleModalClosers.forEach(function (button) {
      button.addEventListener("click", closeGoogleModal);
    });

    appleModalContinue?.addEventListener("click", function () {
      appleConfirmed = true;
      closeAppleModal();
      paymentForm?.requestSubmit();
    });

    googleModalContinue?.addEventListener("click", function () {
      googleConfirmed = true;
      closeGoogleModal();
      paymentForm?.requestSubmit();
    });

    paymentForm?.addEventListener("submit", function (event) {
      const currentMethod = methodInput?.value || "card";
      if (currentMethod === "apple" && !appleConfirmed) {
        event.preventDefault();
        openAppleModal();
        return;
      }
      if (currentMethod === "google" && !googleConfirmed) {
        event.preventDefault();
        openGoogleModal();
        return;
      }
      appleConfirmed = false;
      googleConfirmed = false;
    });

    const expiryLabel = document.querySelector('input[name="card_expiry_label"]');
    const expiryMonth = document.querySelector('input[name="payment-expiry_month"], select[name="payment-expiry_month"]');
    const expiryYear = document.querySelector('input[name="payment-expiry_year"], select[name="payment-expiry_year"]');

    expiryLabel?.addEventListener("input", function () {
      const digits = expiryLabel.value.replace(/\D/g, "").slice(0, 6);
      let nextValue = digits;
      if (digits.length >= 3) {
        nextValue = `${digits.slice(0, 2)}/${digits.slice(2)}`;
      }
      expiryLabel.value = nextValue;
      if (digits.length >= 2 && expiryMonth) {
        expiryMonth.value = String(Number(digits.slice(0, 2)) || "");
      }
      if (digits.length >= 6 && expiryYear) {
        expiryYear.value = digits.slice(2, 6);
      }
    });

    toggleMethod(methodInput?.value || "");
  });
})();
