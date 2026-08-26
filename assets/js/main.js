const PROJECT_TITLES = {
  "interface-architecture": "Interface Architecture",
  "measurement-grids": "Performing Arts Theater in Little Tokyo",
  "elevation-final-model": "Elevation Study — Final Model",
  "van-nuys-municipal": "A Municipal Building in Van Nuys",
  "la-dance-shed": "LA Dance Shed",
  "casa-musica": "Casa Musica",
  "design-documents": "Design Documents",
  "advanced-project-delivery": "Advanced Project Delivery",
  "details-details": "Details, Details",
  "prototype": "Prototype",
};

let scrollSpyObserver;
let frontierObserver;
let currentUrlSlug;
const fadeArticles = [];
let fadeRaf = null;

// Absolute path to the site's own root, computed once from the real initial URL
// (before any pushState can mutate it) — works whether the site is served from
// the domain root or a subpath (e.g. GitHub Pages project sites like /Portfolio/).
const SITE_ROOT = (() => {
  const p = location.pathname;
  return p.includes("/projects/") ? p.split("/projects/")[0] + "/" : p.substring(0, p.lastIndexOf("/") + 1);
})();

function urlForSlug(slug) {
  return slug === "landing" ? `${SITE_ROOT}index.html` : `${SITE_ROOT}projects/${slug}/index.html`;
}

async function loadNav() {
  const res = await fetch(`${SITE_ROOT}partials/nav.html`);
  const html = await res.text();
  const mount = document.getElementById("nav-mount");
  mount.innerHTML = html;

  document.querySelectorAll(".nav-links a, .nav-name").forEach((a) => {
    if (a.dataset.project) a.setAttribute("href", urlForSlug(a.dataset.project));
  });

  const toggle = document.getElementById("nav-toggle");
  const links = document.getElementById("nav-links");
  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open);
  });

  setActiveNav();
  initScrollSpy();
  initInfiniteScroll();
  initFadeTransitions();
}

function setActiveNav() {
  const current = document.body.dataset.project;
  if (!current) return;
  document.querySelectorAll(".nav-links a, .nav-name").forEach((a) => {
    a.classList.toggle("active", a.dataset.project === current);
  });
}

function setActiveNavByProject(slug) {
  document.querySelectorAll(".nav-links a, .nav-name").forEach((a) => {
    a.classList.toggle("active", a.dataset.project === slug);
  });
}

function ensureHeroTitleCard(hero) {
  let card = hero.querySelector(".hero-title-card");
  if (!card) {
    const slug = hero.dataset.spyProject;
    const title = PROJECT_TITLES[slug] || "";
    const eyebrowEl = hero.parentElement && hero.parentElement.querySelector(".project-intro .eyebrow");
    const eyebrow = eyebrowEl ? eyebrowEl.textContent : "";

    card = document.createElement("div");
    card.className = "hero-title-card";
    card.innerHTML = `
      ${eyebrow ? `<span class="hero-title-eyebrow">${eyebrow}</span>` : ""}
      <span class="hero-title-main">${title}</span>
    `;
    hero.appendChild(card);
  }
  return card;
}

function flashHeroTitle(hero) {
  const card = ensureHeroTitleCard(hero);
  card.classList.remove("flash");
  void card.offsetWidth; // force reflow so the animation restarts on repeat entries
  card.classList.add("flash");
}

function initScrollSpy() {
  currentUrlSlug = document.body.dataset.project;

  scrollSpyObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const slug = entry.target.dataset.spyProject;
        setActiveNavByProject(slug);

        if (entry.target.classList.contains("project-hero")) {
          flashHeroTitle(entry.target);
        }

        if (slug !== currentUrlSlug) {
          currentUrlSlug = slug;
          history.pushState({ slug }, "", urlForSlug(slug));
          document.title = slug === "landing" ? "John Northrup — Portfolio" : (PROJECT_TITLES[slug] ? `${PROJECT_TITLES[slug]} — John Northrup` : document.title);
        }
      });
    },
    { rootMargin: "-40% 0px -40% 0px", threshold: 0 }
  );

  document.querySelectorAll("[data-spy-project]").forEach((section) => scrollSpyObserver.observe(section));
}

function initInfiniteScroll() {
  const anchor = document.querySelector(".next-project");
  if (anchor) observeFrontier(anchor);
}

function normalizeAnchorHref(anchor) {
  const slug = anchor.dataset.spyProject;
  if (slug) anchor.setAttribute("href", urlForSlug(slug));
}

function observeFrontier(anchor) {
  normalizeAnchorHref(anchor);

  if (frontierObserver) frontierObserver.disconnect();
  frontierObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          frontierObserver.disconnect();
          appendNextProject(entry.target);
        }
      });
    },
    { rootMargin: "1000px 0px 1000px 0px" }
  );
  frontierObserver.observe(anchor);
}

async function appendNextProject(anchor) {
  const slug = anchor.dataset.spyProject;

  const res = await fetch(urlForSlug(slug));
  const html = await res.text();
  const fetchedDoc = new DOMParser().parseFromString(html, "text/html");
  const article = fetchedDoc.querySelector(".project");
  if (!article) return;

  const nextAnchor = fetchedDoc.querySelector(".next-project");

  anchor.replaceWith(article);
  registerFadeArticle(article);

  const hero = article.querySelector(".project-hero");
  if (hero) scrollSpyObserver.observe(hero);

  if (nextAnchor) {
    document.querySelector("main").appendChild(nextAnchor);
    observeFrontier(nextAnchor);
  }

  updateFades();
}

/* ---------- scroll-linked cross-fade between projects ---------- */
function initFadeTransitions() {
  document.querySelectorAll(".project").forEach(registerFadeArticle);
  window.addEventListener("scroll", scheduleFadeUpdate, { passive: true });
  window.addEventListener("resize", scheduleFadeUpdate);
  updateFades();
}

function registerFadeArticle(article) {
  fadeArticles.push(article);
}

function scheduleFadeUpdate() {
  if (fadeRaf) return;
  fadeRaf = requestAnimationFrame(() => {
    fadeRaf = null;
    updateFades();
  });
}

function updateFades() {
  const vh = window.innerHeight;
  const fadeZone = Math.min(vh * 0.3, 350);

  fadeArticles.forEach((article) => {
    const rect = article.getBoundingClientRect();
    let opacity = 1;

    if (rect.bottom < fadeZone) {
      // this project is finishing — its bottom edge is exiting past the top of the window
      opacity = Math.max(0, rect.bottom / fadeZone);
    } else if (rect.top > vh - fadeZone) {
      // this project is just beginning — its top edge hasn't cleared the fade zone yet
      opacity = Math.max(0, (vh - rect.top) / fadeZone);
    }

    article.style.opacity = opacity;
  });
}

document.addEventListener("DOMContentLoaded", loadNav);
