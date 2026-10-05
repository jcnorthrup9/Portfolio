"""Build a print-ready PDF portfolio from the site's content and images.

Usage (from the repo root):
    pip install pillow            # one-time
    python3 tools/pdf/build.py    # writes John-Northrup-Portfolio.pdf

Requires Node with Playwright (Chromium) available for the final HTML -> PDF step.
Page content lives in PROJECTS below; keep it in sync with projects/*/index.html.
"""
import html
import os
import shutil
import subprocess
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BUILD = os.path.join(ROOT, "tools", "pdf", "build")
OUTPUT = os.path.join(ROOT, "John-Northrup-Portfolio.pdf")

BG = (247, 246, 243)          # site background #f7f6f3
MAX_PX = 1800                 # longest side of exported images (~180dpi across a 10in page)

# Page geometry, inches. US Letter landscape.
PAGE_W, PAGE_H = 11.0, 8.5
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 0.5, 0.75, 0.75
CONTENT_W = PAGE_W - 2 * MARGIN_X
CONTENT_H = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM
GAP = 0.18

PROJECTS = [
    {
        "slug": "prototype",
        "title": "Prototype",
        "eyebrow": "SP26, Prototype, 3GB Studio",
        "color": "#C2A480",
        "hero": "cover.jpg",
        "text": [
            "A generative pipeline for retail architecture and product design, built around a footwear brand's "
            "flagship storefront. Architectural iterations were produced through a custom Flux/ComfyUI pipeline, "
            "while the product line — a technical boot shown here in cutaway and colorway studies — was developed "
            "in parallel through a Gemini-based image pipeline. The two threads feed each other: the building's "
            "industrial material palette of raw wood, steel, and concrete is carried directly into the product's "
            "own construction and display.",
        ],
        "pages": [
            {"rows": [["section-elevation.jpg"], ["interior-1.jpg", "interior-2.jpg"]]},
            {"rows": [["product-1.jpg", "product-colorways.jpg", "product-technical.jpg"]]},
        ],
    },
    {
        "slug": "interface-architecture",
        "title": "Interface Architecture",
        "eyebrow": "3GA Studio",
        "advisor": "Casey Rehm",
        "color": "#984C16",
        "hero": "room-1.jpg",
        "text": [
            "A Cabinet of Curiosities that produces memory artifacts. The installation receives audio input from "
            "the surrounding space; language becomes image through translation of an LLM to 3D object creation "
            "via API calls (Meshy). Objects are automatically optimized for 3D printing — oriented, scaled, and "
            "combined through a Python pipeline.",
        ],
        "pages": [
            {"rows": [["room-2.jpg", "room-3.jpg", "room-4.jpg"], ["cover.png", "detail-2.png"]]},
            {"rows": [["detail-1.png", "detail-3.png", "detail-4.png"]]},
            {"heading": "Object Studies", "rows": [
                ["object-study-1.jpg", "object-study-2.jpg", "object-study-3.jpg"],
                ["object-study-4.jpg", "object-study-5.jpg", "object-study-6.jpg"],
            ]},
        ],
    },
    {
        "slug": "measurement-grids",
        "title": "Performing Arts Theater in Little Tokyo",
        "eyebrow": "FA23, DS 1100, 1GA Studio",
        "advisor": "Matthew Au",
        "color": "#90C5CB",
        "hero": "big-blue-drawing.png",
        "text": [
            "This first semester studio project stems from a study of grid systems, materiality, galleries, and "
            "theatres. The initial measurement grids were carefully constructed, using the limitations of the tape "
            "itself and the gap in named measurements vs. actual measurements. The grids operate in a way that looks "
            "at material falsities, as well as transparency. Through these measurement systems, they are then "
            "expanded into large boards. These boards are then used to produce a massing model. Ultimately realized "
            "as a performing arts theater in the Little Tokyo District, the Measurement Grid is transformed into a "
            "space that offers a place for community to gather in an unconventional theater setting where actors "
            "and patrons are active participants in the shows on display.",
        ],
        "pages": [
            {"heading": "Grid Studies", "rows": [
                ["grid-diagram.png", "figure-1.png", "figure-2.png", "figure-3.png"],
                ["bent-board-1.png", "elevation-2.png", "elevation-1.png"],
            ]},
            {"heading": "Grid Studies", "rows": [["section-1.png", "plan.png"]]},
            {"heading": "Final Model", "rows": [["final-model-1.jpg", "final-model-2.jpg"],
                                                ["final-model-3.jpg", "final-model-5.jpg", "final-model-4.jpg"]]},
            {"heading": "Final Model", "rows": [["final-model-6.jpg", "final-model-7.jpg"]]},
            {"heading": "Final Model", "rows": [["final-model-drawing.jpg"]]},
        ],
    },
    {
        "slug": "van-nuys-municipal",
        "title": "A Municipal Building in Van Nuys",
        "eyebrow": "SP24, DS 1101, 1GB Studio",
        "advisor": "Anna Neimark",
        "color": "#A1A1A3",
        "hero": "cover.png",
        "text": [
            "This studio course explored the unlikely pairings of parking garages and municipal buildings, "
            "producing an interaction between various spaces which often results in overlap, much like a collage of "
            "repurposed materials, the project creates a palimpsest of various conundrums. Through various studies "
            "of redaction, erasure, adaptation, annotation and material/production methodologies these works were "
            "produced. The acts of erasure and redaction are ones often violent or harmful, can also be useful "
            "mechanisms for clearing, filtering, compartmentalizing and synthesizing. Various influences were "
            "combined here, from the base studies of the 17th Century Fortress, Castillo San Marcos, the Faculdade "
            "de Arquitetura, Daniel Libeskind's micromegas. The contrasting components become a study of composed "
            "disorganization, collage, and porosity.",
        ],
        "pages": [
            {"rows": [["detail-1.png", "detail-2.png"]]},
            {"rows": [["detail-3.png"], ["detail-4.png"]]},
        ],
    },
    {
        "slug": "la-dance-shed",
        "title": "LA Dance Shed",
        "eyebrow": "SP24, 2GA Studio, with Milan Sledge",
        "color": "#8D4920",
        "hero": "cover.png",
        "text": [
            "This project for the Los Angeles Dance Project (LADP) seeks to bring the community of Pico-Union "
            "together on a campus that serves and connects the community. Located directly across from the "
            "Pico-Union Project, the site was surgically opened up in order to connect via sightlines and circulation "
            "to this important community asset. A unique goal among this project was to preserve many of the "
            "existing structures on the site and repurposing the materials from buildings that were to be removed. "
            "With a raised circulatory system, visitors are encouraged to meander throughout the site, engaging with "
            "it from within the in-between spaces. The roof serves as not only shade for warm summer days, but also "
            "acts as an organizing device for the discrete elements of the site, bringing them together in a "
            "collective, just as is intended with the surrounding community.",
        ],
        "pages": [
            {"rows": [["detail-1.png", "detail-2.png"], ["detail-3.png", "detail-4.png"]]},
        ],
    },
    {
        "slug": "casa-musica",
        "title": "Casa Musica",
        "eyebrow": "FA24, Visual Studies III, 2GA Studio",
        "advisor": "Marcelo Spina",
        "color": "#9E7A54",
        "hero": "cover.png",
        "text": [
            "Casa Musica sits within an active desert quarry, its long gabled roofs and sawtooth wings pitched to "
            "echo the surrounding excavated terrain. A brick base grounds the structure while a heavy timber roof "
            "structure spans overhead, its gable end fully glazed to frame the quarry and mountains beyond. Inside, "
            "the room is deliberately unfinished — raw stone brought in from the site sits alongside cast furniture, "
            "blurring the line between what was quarried and what was built. The result is a communal gathering "
            "space for music and performance that reads as much as an extension of the landscape as a building set "
            "within it.",
        ],
        "pages": [
            {"rows": [["wormseye-chunk.png"]]},
            {"rows": [["aerial-render.png", "wormseye-1.png"], ["pedestrian-1.png", "pedestrian-2.png"]]},
            {"rows": [["interior.png"]]},
        ],
    },
    {
        "slug": "design-documents",
        "title": "Design Documents",
        "eyebrow": "SP25, Design Documents",
        "advisor": "Herwig Baumgartner",
        "color": "#7D5F30",
        "hero": "cover.png",
        "text": [
            "This course studies the implementation of design, technology, and an understanding of building "
            "systems. Students are tasked with preparing Design Document drawings from a previous year's studio "
            "project and are asked to bring it to life with real-world materials, budgets, and environmental factors.",
        ],
        "pages": [
            {"rows": [["detail-1.png", "detail-2.png"]]},
            {"rows": [["detail-3.png", "detail-4.png"]]},
        ],
    },
    {
        "slug": "advanced-project-delivery",
        "title": "Advanced Project Delivery",
        "eyebrow": "SP25, Advanced Project Delivery",
        "advisor": "Pavel Getov and Karenza Harris",
        "color": "#3F536E",
        "hero": "cover.png",
        "text": [
            "A Construction Documents course focused on taking a design through to buildable detail — resolving "
            "material assemblies, structural connections, and building systems into a coordinated drawing set. Site "
            "plans, reflected ceiling plans, and wall section sheets were developed to real-world standards of "
            "dimension, specification, and constructability.",
        ],
        "pages": [
            {"rows": [["detail-1.png", "detail-2.png"]]},
            {"rows": [["detail-3.png"]]},
        ],
    },
    {
        "slug": "details-details",
        "title": "Details, Details",
        "eyebrow": "F25, Details, Details",
        "advisor": "Dwayne Oyler",
        "color": "#906041",
        "hero": "cover.png",
        "text": [
            "A doorlock mechanism inspired by Frank Lloyd Wright's detail work, specifically the door mechanisms in "
            "the Hollyhock House.",
        ],
        "note": "All work made with partners Chia-Chen Li and Baizhen Yu",
        "pages": [
            {"rows": [["detail-1.png", "detail-2.png"]]},
            {"rows": [["detail-3.png"]]},
        ],
    },
]

EMAIL = "jcnorthrup@gmail.com"
TAGLINE = "Designer specializing in the intersection of AI, automation, and architecture."
BIO = ("I build custom generative pipelines using Python, Grasshopper, and ComfyUI to solve complex spatial "
       "problems — streamlining 3D workflows through data-driven procedural modeling and advanced digital "
       "fabrication.")

_ratios = {}


def export(slug, name):
    """Downscale/flatten a site image to JPEG in the build dir; return (relative path, aspect ratio)."""
    src = os.path.join(ROOT, "assets", "images", slug, name)
    out_name = f"{slug}--{os.path.splitext(name)[0]}.jpg"
    dst = os.path.join(BUILD, "img", out_name)
    if dst not in _ratios:
        im = Image.open(src)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            flat = Image.new("RGB", im.size, BG)
            flat.paste(im, mask=im.split()[-1])
            im = flat
        else:
            im = im.convert("RGB")
        im.thumbnail((MAX_PX, MAX_PX), Image.LANCZOS)
        im.save(dst, "JPEG", quality=82, optimize=True, progressive=True)
        _ratios[dst] = im.width / im.height
    return f"img/{out_name}", _ratios[dst]


def layout_rows(slug, rows, avail_h):
    """Justified rows: every image in a row shares a height; the block is scaled to fit the page and centered."""
    sized = []
    for row in rows:
        imgs = [export(slug, n) for n in row]
        h = (CONTENT_W - GAP * (len(imgs) - 1)) / sum(r for _, r in imgs)
        sized.append((imgs, h))
    total_h = sum(h for _, h in sized) + GAP * (len(sized) - 1)
    scale = min(1.0, (avail_h - GAP * (len(sized) - 1)) / (total_h - GAP * (len(sized) - 1)))
    parts = []
    for imgs, h in sized:
        h *= scale
        cells = "".join(
            f'<img src="{src}" style="width:{h * r:.3f}in;height:{h:.3f}in" alt="">' for src, r in imgs
        )
        parts.append(f'<div class="row">{cells}</div>')
    return "".join(parts)


def esc(s):
    return html.escape(s, quote=True)


def chrome(label, folio):
    return (f'<div class="running"><span>John Northrup</span><span>{esc(label)}</span></div>'
            f'<div class="folio">{folio:02d}</div>')


def build_html():
    pages = []
    contents = []
    page_no = 3  # cover = 1, contents = 2

    for i, p in enumerate(PROJECTS, 1):
        contents.append((i, p, page_no))
        page_no += 1 + len(p["pages"])

    # Cover
    mosaic = "".join(
        f'<div class="tile"><img src="{export(p["slug"], p["hero"])[0]}" alt=""></div>' for p in PROJECTS
    )
    pages.append(f"""
<section class="page cover">
  <div class="cover-text">
    <div class="eyebrow">Portfolio · 2023–2026</div>
    <h1>John Northrup</h1>
    <p class="tagline">{esc(TAGLINE)}</p>
    <p class="bio">{esc(BIO)}</p>
    <div class="contact"><a href="mailto:{EMAIL}">{EMAIL}</a><a href="https://jcnorthrup.com">jcnorthrup.com</a></div>
  </div>
  <div class="mosaic">{mosaic}</div>
</section>""")

    # Contents
    items = "".join(
        f'<li><span class="idx">{i:02d}</span><span class="t">{esc(p["title"])}</span>'
        f'<span class="e">{esc(p["eyebrow"])}</span><span class="pg">{pg:02d}</span></li>'
        for i, p, pg in contents
    )
    pages.append(f"""
<section class="page contents">
  {chrome("Contents", 2)}
  <div class="contents-inner">
    <div class="eyebrow">Contents</div>
    <ol>{items}</ol>
  </div>
</section>""")

    folio = 3
    for i, p in enumerate(PROJECTS, 1):
        hero_src, hero_r = export(p["slug"], p["hero"])
        advisor = f'<div class="advisor">Advisor: {esc(p["advisor"])}</div>' if p.get("advisor") else ""
        body = "".join(f"<p>{esc(t)}</p>" for t in p["text"])
        note = f'<p class="note">*{esc(p["note"])}</p>' if p.get("note") else ""
        text_block = (f'<div class="num">{i:02d}</div><div class="eyebrow">{esc(p["eyebrow"])}</div>'
                      f'<h2>{esc(p["title"])}</h2>{advisor}<div class="swatch" style="background:{p["color"]}"></div>'
                      f'{body}{note}')
        label = f'{i:02d} — {p["title"]}'

        if hero_r >= 1.6:
            img_h = min(CONTENT_W / hero_r, 4.3)
            pages.append(f"""
<section class="page opener top">
  {chrome(label, folio)}
  <img class="hero" src="{hero_src}" style="width:{img_h * hero_r:.3f}in;height:{img_h:.3f}in" alt="">
  <div class="opener-text cols">{text_block}</div>
</section>""")
        else:
            box_w, box_h = 6.3, CONTENT_H
            w = min(box_w, box_h * hero_r)
            pages.append(f"""
<section class="page opener side">
  {chrome(label, folio)}
  <div class="hero-box" style="width:{box_w}in;height:{box_h}in">
    <img class="hero" src="{hero_src}" style="width:{w:.3f}in;height:{w / hero_r:.3f}in" alt="">
  </div>
  <div class="opener-text">{text_block}</div>
</section>""")
        folio += 1

        for spec in p["pages"]:
            heading = f'<h3 class="gallery-heading">{esc(spec["heading"])}</h3>' if spec.get("heading") else ""
            avail = CONTENT_H - (0.4 if heading else 0)
            pages.append(f"""
<section class="page gallery">
  {chrome(label, folio)}
  {heading}
  <div class="rows" style="height:{avail:.3f}in">{layout_rows(p["slug"], spec["rows"], avail)}</div>
</section>""")
            folio += 1

    css = open(os.path.join(os.path.dirname(__file__), "print.css")).read()
    css = (css.replace("{{PAGE_W}}", f"{PAGE_W}in").replace("{{PAGE_H}}", f"{PAGE_H}in")
              .replace("{{MX}}", f"{MARGIN_X}in").replace("{{MT}}", f"{MARGIN_TOP}in")
              .replace("{{MB}}", f"{MARGIN_BOTTOM}in").replace("{{GAP}}", f"{GAP}in"))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>John Northrup — Portfolio</title>
<style>{css}</style></head>
<body>{''.join(pages)}</body></html>"""


def main():
    shutil.rmtree(BUILD, ignore_errors=True)
    os.makedirs(os.path.join(BUILD, "img"))
    shutil.copytree(os.path.join(os.path.dirname(__file__), "fonts"), os.path.join(BUILD, "fonts"))
    html_path = os.path.join(BUILD, "portfolio.html")
    with open(html_path, "w") as f:
        f.write(build_html())
    subprocess.run(["node", os.path.join(os.path.dirname(__file__), "render.js"), html_path, OUTPUT], check=True)
    print(f"Wrote {OUTPUT} ({os.path.getsize(OUTPUT) / 1e6:.1f} MB)")


if __name__ == "__main__":
    sys.exit(main())
