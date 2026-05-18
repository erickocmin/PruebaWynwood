(function () {
  "use strict";

  function formatUSD(amount) {
    return `US$ ${Number(amount || 0).toFixed(2)}`;
  }

  function calculateNights(startValue, endValue) {
    if (!startValue || !endValue) {
      return 0;
    }
    const start = new Date(startValue);
    const end = new Date(endValue);
    const diff = end.getTime() - start.getTime();
    return diff > 0 ? Math.round(diff / (1000 * 60 * 60 * 24)) : 0;
  }

  function initGallery() {
    const gallery = document.querySelector(".property-gallery");
    const mainImage = document.getElementById("propertyGalleryMain");
    if (!gallery || !mainImage) {
      return;
    }
    let images = [];
    try {
      images = JSON.parse(gallery.dataset.gallery || "[]");
    } catch (error) {
      images = [];
    }
    let currentIndex = 0;

    const swapImage = function (nextIndex) {
      if (!images[nextIndex]) {
        return;
      }
      currentIndex = nextIndex;
      mainImage.src = images[nextIndex];
      mainImage.onerror = function () {
        this.onerror = null;
        this.src = "/media/properties/natural1brwithprivateterrace2.png";
      };
      document
        .querySelectorAll(".property-gallery__thumb")
        .forEach(function (thumb, index) {
          thumb.classList.toggle("is-active", index + 1 === nextIndex);
        });
    };

    document
      .querySelectorAll(".property-gallery__thumb")
      .forEach(function (thumb) {
        thumb.addEventListener("click", function () {
          const nextIndex = Number(thumb.dataset.galleryIndex || 0);
          if (
            thumb.classList.contains("property-gallery__thumb--more") &&
            images.length > 3
          ) {
            swapImage((currentIndex + 1) % images.length);
            return;
          }
          swapImage(nextIndex);
        });
      });
  }

  function initBookingCard() {
    const form = document.getElementById("propertyBookingForm");
    if (!form) {
      return;
    }
    const summary = form.querySelector(".booking-summary");
    const checkIn = form.querySelector('input[name="check_in"]');
    const checkOut = form.querySelector('input[name="check_out"]');
    const priceLine = document.querySelector(".property-booking-card__price");
    const nightsLabel = document.getElementById("bookingNightsLabel");
    const nightsAmount = document.getElementById("bookingNightsAmount");
    const cleaningAmount = document.getElementById("bookingCleaningAmount");
    const serviceAmount = document.getElementById("bookingServiceAmount");
    const totalAmount = document.getElementById("bookingTotalAmount");
    const dailyRate = Number(summary?.dataset.nightly || 0);
    const cleaningFee = Number(summary?.dataset.cleaning || 0);
    const serviceFee = Number(summary?.dataset.service || 0);

    const refreshSummary = function () {
      if (
        !summary ||
        !nightsLabel ||
        !nightsAmount ||
        !cleaningAmount ||
        !serviceAmount ||
        !totalAmount
      ) {
        return;
      }
      const nights = calculateNights(checkIn?.value, checkOut?.value);
      const nightlySubtotal = nights * dailyRate;
      const total =
        nights > 0
          ? nightlySubtotal + cleaningFee + serviceFee
          : dailyRate + cleaningFee + serviceFee;
      nightsLabel.textContent =
        nights > 0
          ? `${formatUSD(dailyRate)} x ${nights} ${nights === 1 ? "noche" : "noches"}`
          : "Selecciona tus fechas";
      nightsAmount.textContent = formatUSD(nightlySubtotal);
      cleaningAmount.textContent = formatUSD(cleaningFee);
      serviceAmount.textContent = formatUSD(serviceFee);
      totalAmount.textContent = formatUSD(total);
    };

    [checkIn, checkOut].forEach(function (field) {
      field?.addEventListener("change", refreshSummary);
    });

    document.querySelectorAll(".property-tab").forEach(function (tab) {
      tab.addEventListener("click", function () {
        document.querySelectorAll(".property-tab").forEach(function (node) {
          node.classList.remove("is-active");
        });
        tab.classList.add("is-active");
        if (priceLine) {
          priceLine.textContent =
            tab.dataset.rateMode === "monthly"
              ? priceLine.dataset.monthly
              : priceLine.dataset.daily;
        }
      });
    });

    refreshSummary();
  }

  function initMap() {
    const mapNode = document.getElementById("propertyDetailMap");
    const rawData = document.getElementById("property-detail-map-data");
    if (!mapNode || !rawData || typeof L === "undefined") {
      return;
    }
    const data = JSON.parse(rawData.textContent);
    const map = L.map(mapNode, {
      zoomControl: true,
      scrollWheelZoom: false,
    }).setView([data.lat, data.lng], 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap",
    }).addTo(map);

    L.marker([data.lat, data.lng]).addTo(map);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initGallery();
    initBookingCard();
    initMap();
  });
})();
