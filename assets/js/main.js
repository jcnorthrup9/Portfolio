const PROJECT_TITLES = {
  "measurement-grids": "Performing Arts Theater in Little Tokyo",
  "elevation-final-model": "Elevation Study — Final Model",
  "van-nuys-municipal": "A Municipal Building in Van Nuys",
  "la-dance-shed": "LA Dance Shed",
  "casa-musica": "Casa Musica",
  "design-documents": "Design Documents",
  "advanced-project-delivery": "Advanced Project Delivery",
  "prototype": "Prototype",
};

const loadedSlugs = new Set();
let scrollSpyObserver;
let frontierObserver;
let currentUrlSlug;
const fadeArticles = [];
let fadeRaf = null;

async function loadNav() {
  const res = await fetch("/partials/nav.html");
  const html = await res.text();
  const mount = document.getElementById("nav-mount");
  mount.innerHTML = html;

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
  document.querySelectorAll(".nav-links a").forEach((a) => {
    a.classList.toggle("active", a.dataset.project === current);
  });
}

function setActiveNavByProject(slug) {
  document.querySelectorAll(".nav-links a").forEach((a) => {
    a.classList.toggle("active", a.dataset.project === slug);
  });
}

function initScrollSpy() {
  currentUrlSlug = document.body.dataset.project;
  loadedSlugs.add(currentUrlSlug);

  scrollSpyObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const slug = entry.target.dataset.spyProject;
        setActiveNavByProject(slug);

        if (slug !== currentUrlSlug) {
          currentUrlSlug = slug;
          history.pushState({ slug }, "", `/projects/${slug}/index.html`);
          if (PROJECT_TITLES[slug]) document.title = `${PROJECT_TITLES[slug]} — John Northrup`;
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

function observeFrontier(anchor) {
  const slug = anchor.dataset.spyProject;
  if (loadedSlugs.has(slug)) return; // closes the loop back to an already-shown project — leave as a plain clickable link

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
  if (loadedSlugs.has(slug)) return;

  const href = anchor.getAttribute("href");
  const res = await fetch(href);
  const html = await res.text();
  const fetchedDoc = new DOMParser().parseFromString(html, "text/html");
  const article = fetchedDoc.querySelector(".project");
  if (!article) return;

  const nextAnchor = fetchedDoc.querySelector(".next-project");

  anchor.replaceWith(article);
  loadedSlugs.add(slug);
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
  const fadeZone = Math.min(vh * 0.85, 900);

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
