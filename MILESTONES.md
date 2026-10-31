# Portfolio Milestones

A running log of major progress on this site.

## Scaffold & navigation mechanics (Aug 2026)

- Built as a plain static HTML/CSS/JS site — no framework, no build step.
- Design direction: minimalist, image-centric, modeled on anne-porter.com's secondary project pages, where the
  visitor is never forced back to a landing/grid page to keep browsing.
- Sidebar nav (`partials/nav.html`) injected on every page via `fetch()`, avoiding duplicated markup per page.
- Continuous-scroll mechanic: scrolling to the bottom of one project fetches and appends the next project's content
  in place, so the whole site reads as one uninterrupted scroll rather than page-by-page clicks.
- Scrollspy (`IntersectionObserver`) drives active nav highlighting, the browser URL/title (via `history.pushState`),
  and a scroll-linked cross-fade between projects.

## Content build-out (Aug 2026)

- Replaced placeholder/scaffold content across projects with real work: **Prototype** (AI-generated retail
  architecture + product design pipeline), **Interface Architecture** (Cabinet of Curiosities installation, real
  render/photo set plus burnt-wood object studies), **Performing Arts Theater in Little Tokyo** (formerly
  "Measurement Grids" — real studio boards, drawings, and model photography), **Casa Musica**, and a proper split of
  **Design Documents** vs. **Advanced Project Delivery** (the latter reflecting its actual Construction Documents
  course content).
- Cleaned up numerous images with baked-in gray/tan mat borders from source exports — content-aware cropping so
  every image fills its frame with no visible background.
- Landing page bio rewritten from placeholder copy; project grid tiles gained a hover-reveal color swatch showing
  each project's title, term, and a dimmed preview grid of that project's own images.
- Added a large centered title overlay that briefly flashes over each project's hero image as it scrolls into view,
  so it's unambiguous when you've entered a new project.
- Turned the project chain into a true infinite loop: scrolling past the last project loads back into the first
  and repeats indefinitely, instead of stopping.
- Valiant and Elf-O-Matic-3000 temporarily unlisted from nav/landing pending real content — pages still exist,
  not deleted.

## Hosting (Aug 2026)

- Converted every absolute site path (`/assets/...`, `/projects/...`, the nav-loading `fetch()` call) to
  relative paths plus a small JS-computed site-root constant, so the site works correctly whether served from a
  domain root or a GitHub Pages project subpath.
- Published to GitHub (`github.com/jcnorthrup9/Portfolio`) and connected the custom domain **jcnorthrup.com** via a
  `CNAME` file and Cloudflare DNS (A records to GitHub Pages, DNS-only/unproxied to avoid interfering with GitHub's
  domain verification and HTTPS provisioning).
- Site is live at both the custom domain and the default GitHub Pages URL.

## PDF portfolio (Oct 2026)

- Added a print/email version of the site: `John-Northrup-Portfolio.pdf` (33 pages, US Letter landscape) with a
  cover, contents page, and an opener plus image pages for each project, using the site's copy and images.
- Landing page links to the PDF ("Download portfolio (PDF, 11 MB)") under the bio, served at
  jcnorthrup.com/John-Northrup-Portfolio.pdf.
- **Rebuilt late Oct 2026 to follow the site automatically.** `tools/pdf/build.py` no longer holds any project
  content: it reads `partials/nav.html` (groups, order, names, `keep-case`), each project page (cover, details
  line, advisor/role, paragraphs, gallery headings, images, captions; videos use their poster frame) and the
  landing intro. Gallery pages lay themselves out as justified rows with captions. Styled like the site
  (white, Marcellus, bundled under its OFL).
- Outputs the full `John-Northrup-Portfolio.pdf` (~9 MB, kept under the common 10 MB upload limit via
  `MAX_PX`/`JPEG_Q`) plus `John-Northrup-Portfolio-<group>.pdf` for each sidebar group (code, architecture,
  drawing, fabrication) for tailored applications.
- `.github/workflows/build-pdf.yml` rebuilds and commits the PDFs on every push to `main` that touches the site,
  then asks Pages to redeploy. Local build: `npm install --prefix tools/pdf` once, then
  `python tools/pdf/build.py` (`--full-only` skips the group PDFs).

## Resume link (Oct 2026)

- Added `John-Northrup-Resume.pdf` (one page, real selectable text) at jcnorthrup.com/John-Northrup-Resume.pdf.
  Its source is the Processing sketch at `D:\OneDrive\Employment\00-JobSearch\Materials\Resume\resume\resume.pde`
  (moved 2026-10-23); re-export there and copy the PDF in when the resume changes.
- Landing page now shows two links under the bio: "Download portfolio ↓" (downloads) and "Resume ↗" (opens in a
  new tab). Dropped the "(PDF, 11 MB)" note from the portfolio label.

## Redesign: grouped sidebar, calm pages (Oct 2026)

- Replaced the continuous-scroll/cross-fade/hero-flash mechanics with ordinary pages, modeled on the calm,
  white, captioned layout of xinyanhe.com. A short-lived category *filter* (tabs) was tried first and dropped:
  hiding work read worse than showing it grouped.
- Sidebar (`partials/nav.html`) groups projects under **Architecture · Drawing & Documentation · Fabrication &
  Mechanical · Code & AI**, each project under one heading; Resume, Portfolio PDF and Email sit at the bottom.
  The list order also drives every page's "Next" link (`main.js`), looping back to the top.
- Landing page: short positioning line, then captioned 4:3 tiles in the same four sections. Section ids make
  tailored links like `jcnorthrup.com/#drawing` jump straight to one group.
- Project pages keep their original markup; the new `style.css` reflows them into one centered column (intro
  first, each image on its own row) and every figure got a `<figcaption>` from its alt text — edit captions
  directly in each page.
- Type: Marcellus (Google Fonts), light classical capitals for names, labels and captions. **Superseded late
  Oct 2026** by a pairing: Marcellus kept for the name and project titles (`--display`); Inter (`--sans`, OFL,
  same family as the resume) for body text, sidebar, labels and captions, a Swiss, drawing-sheet voice. Chosen
  over Swiss 721, which John liked but is a commercial Bitstream font (his copy came with AutoCAD) and can't be
  hosted. The PDF uses the same pairing (`tools/pdf/fonts`, both OFL).
- PDFs (resume, portfolio) open in the browser's viewer instead of downloading. Casa Musica and A Municipal
  Building in Van Nuys unlisted (pages kept). Landing bio rewritten to the "draws it, builds it, automates it"
  positioning; site resume replaced with the 2026-10-23 version.

## New and rebuilt projects (Oct 2026)

- Group order is now **Code & AI · Architecture · Drawing & Documentation · Fabrication & Mechanical**.
  Interface Architecture moved to Code & AI; "Performing Arts Theater in Little Tokyo" renamed
  "Little Tokyo Theater".
- **memoryMachine** (M.Arch thesis, SU26, Casey Rehm) added first under Code & AI: zoning-field cover, a 36 s
  screen-recorded tour of the app (generate → massing → drawings → diagnostics), installation photos,
  generated plan/axo and a precedent drawing; text is the final thesis statement. The name keeps its camelCase
  via a `keep-case` class. Sources are archived in SCI-Arc OneDrive `2026_Summer\Thesis\Archive_Final`.
- **Design School in Mexico City** (SP25 2GB, Zeina Koreitem, with Nate Smith) added first under Architecture:
  full-res model photos plus Nate's finished sections and plan (with his OK).
- **LA Dance Shed**: drawings added (axon, two plans, sections, elevations) stitched from the split two-page
  PDF spreads in the studio's `Archive_Final`; date corrected to FA24.
- **Elf-O-Matic-3000** listed under Fabrication & Mechanical with real photos and the running loop (brings in
  the unpublished `elf-o-matic-media` branch work). `.advisor.role` labels a job role instead of an advisor.
- Project intros are now left-aligned with justified paragraphs; gallery headings and the Next link are
  left-aligned; captions stay centered under their images. Videos (`<video>`) sit in galleries like images.

## Amenity Deck Engines: zone diagram and model view (Oct 2026)

- Added the **three privacy zones** diagram under "The secondary definition", ahead of the zonal curves, so the
  section reads intent then execution. Taken from the design-narrative page of the submission PDF — the
  *embedded* image rather than the rasterised page, because the slide cropped its left edge off. Its real
  detail ceiling is 777×612 px, so it is upscaled; re-export from the original Illustrator/Affinity file if a
  crisper version is ever needed. Checked clean of firm/project identifiers before publishing.
- Added **`pavilion-model.jpg`**, the raw Rhino viewport the AI-enhanced `hero-pool-2.jpg` was rendered from,
  placed directly above it so the pair reads model → render. Cropped to drop the clipped foreground band and
  its red construction curves.
- **Dropped the "Zonal curves" figure.** Its geometry came from reconstructed `ProgramZones` curves, not the
  originals, so it did not match the design it illustrated. The zone diagram now carries the spatial intent.

## Design School in Mexico City: John's own plans (Oct 2026)

John's plan drawings replaced Nate's single dressed export (`plan-ground.jpg`, kept in the repo but no longer
referenced). Nate's two sections stay. Source is `250328_Plans_Sections_24x36.pdf` pp. 1–2 in the studio
archive — `Plan1.pdf`/`Plan2.pdf` there are bare linework with no title block, legend or scale bar, so they are
not usable alone. **Working files and a full README are archived at**
`R:\SCI-Arc_Archive\2025_2GB_Spring\01_Studio\EXERCISE_5_DRAWINGS\InDesign\Portfolio_Rework_2026-10-31\` —
go there first, the PDFs are still vector and editable.

- **Title block** — filled the template's `FIRST LAST` and `DESCRIPTION OF IMAGE` placeholders. Note the sheets
  now read `NATE SMITH` by John's choice, while Nate's own drawings are signed `NATHANIEL SMITH`.
- **Legend** — replaced John's older taxonomy with Nate's renumbering. It turned out to be the same template
  with one extra column, so it drops onto the same x positions.
- **Callouts** — none existed. Ground floor mirrors Nate's; cores read **6** per the legend, where his sheet
  still says `8` (his own leftover). **The second-floor callouts are inferred and unverified**, and `3.4`
  (dressing rooms) / `3.6` (lobby) have no matching rooms in John's drawings.
- **Ink weight** — the drawing set `0 0 0 RG` at the head of six content streams, so every wall rendered pure
  black, far heavier than Nate's sections. Now **0.48 grey**, matched to the darkest decile of his drawings.
  Line *width* is not a useful lever here: at 2500 px the strokes are already sub-pixel.
- **Scale** — sheet 2 was drawn **1.31×** larger than sheet 1 (column grid 64.1 px against 49.0 px). Its
  drawing content is wrapped in a scale transform so both agree; the title block is left at template size, and
  the scale bar and north arrow are composited in from sheet 1.
- **IMSS poché** — transferred from Nate's drawing by image registration, then its top edge straightened to the
  wall line and the wall-enclosed corner pockets filled. A morphological closing was tried for those pockets
  and rejected: it rounds the boundary outward into the plaza. Sheet 2's poché **assumes the existing building
  keeps its ground-floor footprint** one level up.
- **Final model photo** (`cover.jpg`, also the landing tile and Prototype's Next preview) was lifted with a
  1.35 gamma and re-saturated ×1.45 in one pass, matching the truss close-up beside it.
