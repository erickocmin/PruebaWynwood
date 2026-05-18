document.querySelectorAll('a[href*="#"]').forEach((anchor) => {
  anchor.addEventListener("click", (event) => {
    const href = anchor.getAttribute("href");
    if (!href || (!href.startsWith("#") && !href.includes("/#"))) {
      return;
    }
    const targetId = href.split("#")[1];
    const target = document.getElementById(targetId);
    if (!target) {
      return;
    }
    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

document.addEventListener("DOMContentLoaded", () => {
  initHeroSearch();
  initDestinationsCarousel();
  initDragCarousel();
  initRealEstateCarousel();
});

function initHeroSearch() {
  const neighborhoodsNode = document.getElementById("city-neighborhoods-data");
  const cityNeighborhoods = neighborhoodsNode ? JSON.parse(neighborhoodsNode.textContent) : {};
  const forms = Array.from(document.querySelectorAll(".home-form"));

  forms.forEach((form) => {
    const cityDropdown = form.querySelector(".new-dropdown");
    const cityTrigger = cityDropdown?.querySelector(".new-search-field");
    const cityLabel = cityDropdown?.querySelector(".new-search-field-city");
    const cityMenu = cityDropdown?.querySelector(".countries-cities-selector");

    const neighborhoodDropdown = form.querySelectorAll(".new-dropdown")[1];
    const neighborhoodTrigger = neighborhoodDropdown?.querySelector(".new-search-field");
    const neighborhoodMenu = neighborhoodDropdown?.querySelector(".neighborhoods-cities-selector");
    const neighborhoodCounter = neighborhoodDropdown?.querySelector(".counter");

    const guestDropdown = form.querySelector(".new-dropdown-guest");
    const guestTrigger = guestDropdown?.querySelector(".new-search-field");

    const dateTrigger = form.querySelector(".daterange");

    const hiddenCity = form.querySelector('input[name="city"]');
    const hiddenNeighborhoods = form.querySelector('input[name="neighborhoods"]');
    const hiddenGuests = form.querySelector('input[name="guests"]');
    const hiddenCheckIn = form.querySelector('input[name="check_in"]');
    const hiddenCheckOut = form.querySelector('input[name="check_out"]');

    if (cityTrigger && cityDropdown) {
      cityTrigger.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleDropdown(cityDropdown);
      });
    }

    if (neighborhoodTrigger && neighborhoodDropdown) {
      neighborhoodTrigger.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleDropdown(neighborhoodDropdown);
      });
    }

    if (guestTrigger && guestDropdown) {
      guestTrigger.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleDropdown(guestDropdown);
      });
    }

    if (cityMenu && cityLabel && hiddenCity && neighborhoodMenu && hiddenNeighborhoods) {
      cityMenu.querySelectorAll("[data-city-id]").forEach((link) => {
        link.addEventListener("click", (event) => {
          event.preventDefault();
          const cityId = String(link.dataset.cityId || "");
          cityLabel.textContent = link.dataset.name || link.textContent.trim();
          hiddenCity.value = cityId;
          hiddenNeighborhoods.value = "";
          if (neighborhoodCounter) {
            neighborhoodCounter.textContent = "";
          }
          renderNeighborhoods(neighborhoodMenu, cityNeighborhoods[cityId] || []);
          closeDropdowns();
        });
      });
    }

    if (neighborhoodMenu && hiddenNeighborhoods) {
      neighborhoodMenu.addEventListener("change", () => {
        const selected = Array.from(
          neighborhoodMenu.querySelectorAll('input[name="home_neighborhood_selected"]:checked')
        ).map((input) => input.value);

        hiddenNeighborhoods.value = selected.join(",");
        if (neighborhoodCounter) {
          neighborhoodCounter.textContent = selected.length ? `(${selected.length})` : "";
        }
      });
    }

    if (dateTrigger && hiddenCheckIn && hiddenCheckOut) {
      const dateMenu = buildDateMenu(dateTrigger, hiddenCheckIn, hiddenCheckOut);
      dateTrigger.insertAdjacentElement("afterend", dateMenu);
      dateTrigger.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        closeDropdowns();
        dateTrigger.classList.toggle("is-open");
      });
    }

    if (guestDropdown && hiddenGuests) {
      initGuestCounter(form, guestDropdown, hiddenGuests);
    }

    if (neighborhoodMenu && !neighborhoodMenu.querySelector('input[name="home_neighborhood_selected"]')) {
      renderNeighborhoods(neighborhoodMenu, []);
    }
  });

  document.addEventListener("click", () => closeDropdowns());
}

function initGuestCounter(form, guestDropdown, hiddenGuests) {
  const config = [
    { type: "Adult", min: 1 },
    { type: "Children", min: 0 },
    { type: "Pets", min: 0 },
  ];

  const updateLabels = () => {
    const adult = getCounterValue(form, "Adult");
    const children = getCounterValue(form, "Children");
    const pets = getCounterValue(form, "Pets");

    const adultLabel = form.querySelector('[id="countAdultLabel"]') || form.querySelector('[id="countAdultFooterLabel"]');
    const childrenLabel = form.querySelector('[id="countChildrenLabel"]') || form.querySelector('[id="countChildrenFooterLabel"]');
    const petsLabel = form.querySelector('[id="countPetsLabel"]') || form.querySelector('[id="countPetsFooterLabel"]');

    if (adultLabel) adultLabel.textContent = "Número de Huespedes";
    if (childrenLabel) childrenLabel.textContent = children ? `, ${children} ${children === 1 ? "Niño" : "Niños"}` : "";
    if (petsLabel) petsLabel.textContent = pets ? `, ${pets} ${pets === 1 ? "Mascota" : "Mascotas"}` : "";

    hiddenGuests.value = adult + children;
  };

  config.forEach(({ type, min }) => {
    const minus = findWithinForm(form, [`#count${type}Rest`, `#count${type}FooterRest`]);
    const plus = findWithinForm(form, [`#count${type}Sum`, `#count${type}FooterSum`]);
    const display = findWithinForm(form, [`#count${type}`, `#count${type}Footer`]);
    const hidden = findWithinForm(form, [`#countInput${type}`, `#countInput${type}Footer`]);

    if (!minus || !plus || !display) {
      return;
    }

    minus.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const nextValue = Math.max(min, Number(display.textContent) - 1);
      display.textContent = String(nextValue);
      if (hidden) hidden.value = String(nextValue);
      updateLabels();
    });

    plus.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const nextValue = Number(display.textContent) + 1;
      display.textContent = String(nextValue);
      if (hidden) hidden.value = String(nextValue);
      updateLabels();
    });
  });

  updateLabels();
}

function getCounterValue(form, type) {
  const display = findWithinForm(form, [`#count${type}`, `#count${type}Footer`]);
  return display ? Number(display.textContent || 0) : 0;
}

function findWithinForm(form, selectors) {
  for (const selector of selectors) {
    const node = form.querySelector(selector);
    if (node) return node;
  }
  return null;
}

function renderNeighborhoods(menu, neighborhoods) {
  const options = neighborhoods.length
    ? neighborhoods
        .map(
          (name, index) => `
            <li>
              <label class="checkbox neighborhood-option" for="home-neighborhood-${index}">
                <input id="home-neighborhood-${index}" name="home_neighborhood_selected" type="checkbox" value="${escapeHtml(name)}">
                <span>${escapeHtml(name)}</span>
              </label>
            </li>
          `
        )
        .join("")
    : `
        <li class="country-divider">
          <span>Selecciona una ciudad primero</span>
        </li>
      `;

  menu.innerHTML = `
    <li>
      <div class="flex align-items-center gap-10">
        <label class="margin-0">Distrito</label>
      </div>
    </li>
    ${options}
  `;
}

function buildDateMenu(trigger, hiddenCheckIn, hiddenCheckOut) {
  const menu = document.createElement("div");
  menu.className = "hero-date-menu";

  const checkInValue = hiddenCheckIn.value || "";
  const checkOutValue = hiddenCheckOut.value || "";

  menu.innerHTML = `
    <div class="hero-date-menu__grid">
      <div>
        <label>Ingreso</label>
        <input type="date" class="hero-date-input hero-date-input--in" value="${checkInValue}">
      </div>
      <div>
        <label>Salida</label>
        <input type="date" class="hero-date-input hero-date-input--out" value="${checkOutValue}">
      </div>
    </div>
    <div class="hero-date-menu__actions">
      <button type="button" class="hero-date-apply">Aplicar</button>
    </div>
  `;

  menu.addEventListener("click", (event) => event.stopPropagation());

  const apply = menu.querySelector(".hero-date-apply");
  const inInput = menu.querySelector(".hero-date-input--in");
  const outInput = menu.querySelector(".hero-date-input--out");
  const textNode = trigger.querySelector(".text");

  apply.addEventListener("click", () => {
    hiddenCheckIn.value = inInput.value;
    hiddenCheckOut.value = outInput.value;
    if (inInput.value && outInput.value) {
      textNode.textContent = `${formatDate(inInput.value)} / ${formatDate(outInput.value)}`;
    } else {
      textNode.textContent = "23 Nov 2023 / 31 Dic 2023";
    }
    trigger.classList.remove("is-open");
  });

  return menu;
}

function toggleDropdown(targetDropdown) {
  const isOpen = targetDropdown.classList.contains("open");
  closeDropdowns();
  if (!isOpen) {
    targetDropdown.classList.add("open");
  }
}

function closeDropdowns() {
  document.querySelectorAll(".new-dropdown.open, .new-dropdown-guest.open").forEach((dropdown) => {
    dropdown.classList.remove("open");
  });
  document.querySelectorAll(".daterange.is-open").forEach((trigger) => {
    trigger.classList.remove("is-open");
  });
}

function formatDate(value) {
  const date = new Date(`${value}T00:00:00`);
  return date.toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function initDestinationsCarousel() {
  const track = document.getElementById("destinationsTrack");
  const prev = document.getElementById("destinationsPrev");
  const next = document.getElementById("destinationsNext");

  if (!track || !prev || !next) {
    return;
  }

  const items = Array.from(track.querySelectorAll(".new-destinations-item"));
  const windowEl = track.parentElement;
  let currentPage = 0;

  const getPages = () => {
    if (!items.length) {
      return [0];
    }

    const itemWidth = items[0].offsetWidth;
    const styles = window.getComputedStyle(track);
    const gap = parseFloat(styles.columnGap || styles.gap || "8") || 8;
    const itemSpan = itemWidth + gap;
    const maxOffset = Math.max(0, track.scrollWidth - windowEl.clientWidth);

    if (window.innerWidth <= 768) {
      const mobileVisible = 2;
      const lastStart = Math.max(0, items.length - mobileVisible);
      return Array.from({ length: lastStart + 1 }, (_, index) =>
        Math.min(index * itemSpan, maxOffset),
      );
    }

    const desktopVisible = 5;
    const desktopStep = 2;
    const lastStart = Math.max(0, items.length - desktopVisible);
    const starts = [0];

    for (let start = desktopStep; start < lastStart; start += desktopStep) {
      starts.push(start);
    }

    if (lastStart > 0 && starts[starts.length - 1] !== lastStart) {
      starts.push(lastStart);
    }

    return starts.map((start) => Math.min(start * itemSpan, maxOffset));
  };

  const updateCarousel = () => {
    const pages = getPages();
    currentPage = Math.max(0, Math.min(currentPage, pages.length - 1));
    const offset = pages[currentPage] || 0;

    track.style.transform = `translateX(-${offset}px)`;
    prev.classList.toggle("is-disabled", currentPage === 0);
    next.classList.toggle("is-disabled", currentPage >= pages.length - 1);
  };

  prev.addEventListener("click", () => {
    if (prev.classList.contains("is-disabled")) return;
    currentPage -= 1;
    updateCarousel();
  });

  next.addEventListener("click", () => {
    if (next.classList.contains("is-disabled")) return;
    currentPage += 1;
    updateCarousel();
  });

  window.addEventListener("resize", updateCarousel);
  updateCarousel();
}

function initDragCarousel() {
  const carousel = document.getElementById("rooms_featured");

  if (!carousel) {
    return;
  }

  let isDragging = false;
  let startX = 0;
  let startScrollLeft = 0;
  let moved = false;

  carousel.querySelectorAll("img").forEach((image) => {
    image.setAttribute("draggable", "false");
  });

  carousel.querySelectorAll("a").forEach((link) => {
    link.setAttribute("draggable", "false");
  });

  carousel.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) {
      return;
    }

    event.preventDefault();
    isDragging = true;
    moved = false;
    startX = event.clientX;
    startScrollLeft = carousel.scrollLeft;
    carousel.classList.add("is-dragging");
    carousel.setPointerCapture?.(event.pointerId);
  });

  carousel.addEventListener("pointermove", (event) => {
    if (!isDragging) {
      return;
    }

    event.preventDefault();
    const deltaX = event.clientX - startX;
    if (Math.abs(deltaX) > 4) {
      moved = true;
    }

    carousel.scrollLeft = startScrollLeft - deltaX;
  });

  const stopDragging = (event) => {
    if (!isDragging) {
      return;
    }

    isDragging = false;
    carousel.classList.remove("is-dragging");
    if (event?.pointerId !== undefined) {
      carousel.releasePointerCapture?.(event.pointerId);
    }
  };

  carousel.addEventListener("pointerup", stopDragging);
  carousel.addEventListener("pointercancel", stopDragging);

  carousel.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", (event) => {
      if (moved) {
        event.preventDefault();
        moved = false;
      }
    });
  });
}

function initRealEstateCarousel() {
  const carousel = document.getElementById("carousel-example-generic");

  if (!carousel) {
    return;
  }

  const slides = Array.from(carousel.querySelectorAll(".carousel-inner > .item"));
  const indicators = Array.from(carousel.querySelectorAll(".carousel-indicators > li"));

  if (slides.length < 2) {
    return;
  }

  let currentIndex = Math.max(
    0,
    slides.findIndex((slide) => slide.classList.contains("active")),
  );

  const showSlide = (index) => {
    currentIndex = index;
    slides.forEach((slide, slideIndex) => {
      slide.classList.toggle("active", slideIndex === currentIndex);
    });

    indicators.forEach((indicator, indicatorIndex) => {
      indicator.classList.toggle("active", indicatorIndex === currentIndex);
    });
  };

  indicators.forEach((indicator, indicatorIndex) => {
    indicator.addEventListener("click", () => {
      showSlide(indicatorIndex);
      restartAutoplay();
    });
  });

  let autoplayId = null;

  const startAutoplay = () => {
    autoplayId = window.setInterval(() => {
      showSlide((currentIndex + 1) % slides.length);
    }, 3000);
  };

  const restartAutoplay = () => {
    if (autoplayId) {
      window.clearInterval(autoplayId);
    }
    startAutoplay();
  };

  showSlide(currentIndex);
  startAutoplay();
}
