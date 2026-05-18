document.addEventListener("DOMContentLoaded", () => {
  initResultCardGalleries();
  initResultsMap();
});

function initResultCardGalleries() {
  const cards = document.querySelectorAll(".result-card");

  cards.forEach((card) => {
    const image = card.querySelector(".result-card__image");
    const dots = Array.from(card.querySelectorAll(".result-card__dot"));
    const rawGallery = card.dataset.gallery || "[]";
    let gallery = [];

    try {
      gallery = JSON.parse(rawGallery);
    } catch (error) {
      gallery = image?.src ? [image.src] : [];
    }

    if (!gallery.length || !image || dots.length <= 1) {
      return;
    }

    let currentIndex = 0;

    const updateGallery = (nextIndex) => {
      currentIndex = nextIndex;
      image.src = gallery[currentIndex];
      dots.forEach((dot, index) => {
        dot.classList.toggle("is-on", index === currentIndex);
      });
    };

    const dotsWrap = card.querySelector(".result-card__dots");
    dotsWrap?.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      updateGallery((currentIndex + 1) % gallery.length);
    });
  });
}

function initResultsMap() {
  const mapNode = document.getElementById("resultsMapCanvas");
  const mapDataNode = document.getElementById("results-map-data");
  if (!mapNode || !mapDataNode || typeof L === "undefined") {
    return;
  }

  let mapResults = [];

  try {
    mapResults = JSON.parse(mapDataNode.textContent);
  } catch (error) {
    mapResults = [];
  }

  const fallbackCenter = [40.4168, -3.7038];
  const firstResult = mapResults[0];
  const map = L.map(mapNode, {
    zoomControl: false,
    scrollWheelZoom: true,
  }).setView(firstResult ? [firstResult.lat, firstResult.lng] : fallbackCenter, firstResult ? 11 : 5);

  L.control.zoom({ position: "bottomright" }).addTo(map);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const bounds = [];

  mapResults.forEach((result, index) => {
    const latLng = [result.lat, result.lng];
    bounds.push(latLng);

    const marker = L.marker(latLng, {
      icon: L.divIcon({
        className: "",
        html: `<div class="results-map-pin${index % 3 === 2 ? " is-light" : ""}">$${result.price}</div>`,
        iconSize: [56, 56],
        iconAnchor: [28, 28],
      }),
    }).addTo(map);

    marker.bindPopup(
      `<div class="results-map-popup"><strong>${escapeHtml(result.title)}</strong><span>${escapeHtml(result.city)}</span></div>`
    );

    marker.on("click", () => {
      map.flyTo(latLng, 13, { duration: 0.6 });
    });
  });

  if (bounds.length > 1) {
    map.fitBounds(bounds, { padding: [40, 40] });
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
