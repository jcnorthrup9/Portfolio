// Absolute path to the site's own root — works whether the site is served from the domain root or a
// subpath (e.g. GitHub Pages project sites like /Portfolio/).
const SITE_ROOT = (() => {
  const p = location.pathname;
  return p.includes("/projects/") ? p.split("/projects/")[0] + "/" : p.substring(0, p.lastIndexOf("/") + 1);
})();

function urlForSlug(slug) {
  return slug === "landing" ? `${SITE_ROOT}index.html` : `${SITE_ROOT}projects/${slug}/index.html`;
}

async function loadNav() {
  const res = await fetch(`${SITE_ROOT}partials/nav.html`);
  document.getElementById("nav-mount").innerHTML = await res.text();

  // The partial's hrefs are written for a project page; repoint them from the real site root.
  document.querySelectorAll(".nav [data-project]").forEach((a) => a.setAttribute("href", urlForSlug(a.dataset.project)));
  document.querySelectorAll(".nav [data-anchor]").forEach((a) => a.setAttribute("href", `${urlForSlug("landing")}#${a.dataset.anchor}`));
  document.querySelectorAll(".nav [data-file]").forEach((a) => a.setAttribute("href", SITE_ROOT + a.dataset.file));

  const current = document.body.dataset.project;
  document.querySelectorAll(".nav-projects a").forEach((a) => a.classList.toggle("active", a.dataset.project === current));

  const toggle = document.getElementById("nav-toggle");
  const links = document.getElementById("nav-links");
  toggle.addEventListener("click", () => toggle.setAttribute("aria-expanded", links.classList.toggle("open")));

  setNextLink(current);
}

// "Next" follows the sidebar order and loops; a page not listed there (unlisted work) continues from the top.
function setNextLink(current) {
  const next = document.querySelector(".next-project");
  if (!next) return;
  const links = [...document.querySelectorAll(".nav-projects a[data-project]")];
  if (!links.length) return;
  const target = links[(links.findIndex((a) => a.dataset.project === current) + 1) % links.length];
  next.setAttribute("href", urlForSlug(target.dataset.project));
  const label = next.querySelector("h2");
  if (label) {
    label.textContent = target.textContent;
    label.classList.toggle("keep-case", target.classList.contains("keep-case"));
  }
}

document.addEventListener("DOMContentLoaded", loadNav);
