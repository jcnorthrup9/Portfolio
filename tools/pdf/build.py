"""Build print-ready PDF portfolios straight from the site, so they always match it.

Usage (from the repo root):
    pip install pillow                                # one-time
    npm install --prefix tools/pdf                    # one-time: Playwright for HTML -> PDF
    npx --prefix tools/pdf playwright install chromium
    python tools/pdf/build.py                         # full portfolio + one PDF per sidebar group

Nothing about the projects is written here. The sidebar (partials/nav.html) gives the groups, the project
order and the display names; each project page gives its cover, details line, advisor or role, paragraphs,
gallery images, gallery headings and captions; the landing page gives the cover-page intro. Edit the site and
rebuild — or let the GitHub Action do it on every push to main.

Outputs (repo root):
    John-Northrup-Portfolio.pdf               everything, in sidebar order
    John-Northrup-Portfolio-<group>.pdf       one per sidebar group (code, architecture, drawing, fabrication)
"""
import argparse
import html
import os
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
SITE = "jcnorthrup.com"
EMAIL = "jcnorthrup@gmail.com"

BG = (255, 255, 255)          # site background
MAX_PX = 1400                 # longest side of exported images (~140 dpi across a 10 in page)
JPEG_Q = 76

# Page geometry, inches. US Letter landscape.
PAGE_W, PAGE_H = 11.0, 8.5
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 0.55, 0.75, 0.7
CONTENT_W = PAGE_W - 2 * MARGIN_X
CONTENT_H = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM
GAP = 0.2
CAPTION_H = 0.24              # band under each gallery row for captions
ROW_MIN_H = 2.4               # a row stops taking images once they would get shorter than this
MAX_PER_ROW = 3
MAX_ROWS_PER_PAGE = 2
HEADING_H = 0.4


# ---------- reading the site ----------

class _Parser(HTMLParser):
    """Collects text and attributes while tracking which classed elements we're inside."""

    VOID = {"img", "br", "hr", "meta", "link", "input", "source"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []  # (tag, set(classes))

    def inside(self, cls):
        return any(cls in c for _, c in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get("class") or "").split())
        self.start(tag, a, classes)
        if tag not in self.VOID:
            self.stack.append((tag, classes))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                popped = self.stack[i]
                del self.stack[i:]
                self.end(tag, popped[1])
                break

    def start(self, tag, a, classes):
        pass

    def end(self, tag, classes):
        pass


def _clean(s):
    return re.sub(r"\s+", " ", s).strip()


class NavParser(_Parser):
    def __init__(self):
        super().__init__()
        self.groups = []  # {"key", "title", "projects": [{"slug", "title", "keep_case"}]}
        self._text = None

    def start(self, tag, a, classes):
        if tag == "div" and "nav-group" in classes:
            self.groups.append({"key": a.get("data-section", ""), "title": "", "projects": []})
        elif tag == "a" and "nav-group-title" in classes:
            self._text = ["group"]
        elif tag == "a" and a.get("data-project") and self.inside("nav-projects"):
            self.groups[-1]["projects"].append({"slug": a["data-project"], "title": "",
                                                "keep_case": "keep-case" in classes})
            self._text = ["project"]

    def handle_data(self, data):
        if self._text:
            self._text.append(data)

    def end(self, tag, classes):
        if tag == "a" and self._text:
            kind, text = self._text[0], _clean("".join(self._text[1:]))
            if kind == "group":
                self.groups[-1]["title"] = text
            else:
                self.groups[-1]["projects"][-1]["title"] = text
            self._text = None


class ProjectParser(_Parser):
    def __init__(self):
        super().__init__()
        self.hero = None
        self.eyebrow = ""
        self.advisor = ""
        self.advisor_is_role = False
        self.title = ""
        self.paragraphs = []
        self.items = []  # ("heading", text) | ("figure", src, caption, is_video)
        self._text = None
        self._fig = None

    def start(self, tag, a, classes):
        if tag == "img" and self.inside("project-hero") and not self.hero:
            self.hero = a.get("src")
        elif self.inside("project-intro") and tag in ("div", "h1", "p"):
            if tag == "div" and "advisor" in classes:
                self.advisor_is_role = "role" in classes
            if tag == "p" or classes & {"eyebrow", "advisor"} or tag == "h1":
                self._text = [tag if tag != "div" else ("advisor" if "advisor" in classes else "eyebrow")]
        elif tag == "h2" and "gallery-heading" in classes:
            self._text = ["heading"]
        elif tag == "figure" and self.inside("project-gallery"):
            self._fig = {"src": None, "caption": "", "video": False}
        elif self._fig is not None and tag == "img" and not self._fig["src"]:
            self._fig["src"] = a.get("src")
        elif self._fig is not None and tag == "video":
            self._fig["src"], self._fig["video"] = a.get("poster"), True
        elif self._fig is not None and tag == "figcaption":
            self._text = ["caption"]

    def handle_data(self, data):
        if self._text:
            self._text.append(data)

    def end(self, tag, classes):
        if self._text and tag in ("div", "h1", "p", "h2", "figcaption"):
            kind, text = self._text[0], _clean("".join(self._text[1:]))
            self._text = None
            if kind == "eyebrow":
                self.eyebrow = text
            elif kind == "advisor":
                self.advisor = text
            elif kind == "h1":
                self.title = text
            elif kind == "p" and text:
                self.paragraphs.append(text)
            elif kind == "heading":
                self.items.append(("heading", text))
            elif kind == "caption" and self._fig is not None:
                self._fig["caption"] = text
        if tag == "figure" and self._fig is not None:
            if self._fig["src"]:
                self.items.append(("figure", self._fig["src"], self._fig["caption"], self._fig["video"]))
            self._fig = None


class LandingParser(_Parser):
    def __init__(self):
        super().__init__()
        self.tagline = ""
        self.bio = ""
        self._text = None

    def start(self, tag, a, classes):
        if self.inside("landing") and tag in ("h1", "p"):
            self._text = [tag]

    def handle_data(self, data):
        if self._text:
            self._text.append(data)

    def end(self, tag, classes):
        if self._text and tag in ("h1", "p"):
            text = _clean("".join(self._text[1:]))
            if tag == "h1":
                self.tagline = text
            elif not self.bio:
                self.bio = text
            self._text = None


def _parse(parser, path):
    with open(path, encoding="utf-8") as f:
        parser.feed(f.read())
    return parser


def read_site():
    nav = _parse(NavParser(), os.path.join(ROOT, "partials", "nav.html"))
    landing = _parse(LandingParser(), os.path.join(ROOT, "index.html"))
    groups = []
    for g in nav.groups:
        projects = []
        for entry in g["projects"]:
            page_dir = os.path.join(ROOT, "projects", entry["slug"])
            p = _parse(ProjectParser(), os.path.join(page_dir, "index.html"))
            resolve = lambda src: os.path.normpath(os.path.join(page_dir, src))
            notes = [t[1:].strip() for t in p.paragraphs if t.startswith("*")]
            projects.append({
                "slug": entry["slug"],
                "title": entry["title"] or p.title,
                "keep_case": entry["keep_case"],
                "eyebrow": p.eyebrow,
                "advisor": p.advisor,
                "advisor_label": "Role" if p.advisor_is_role else "Advisor",
                "text": [t for t in p.paragraphs if not t.startswith("*")],
                "notes": notes,
                "hero": resolve(p.hero) if p.hero else None,
                "items": [it if it[0] == "heading" else ("figure", resolve(it[1]), it[2], it[3]) for it in p.items],
            })
        groups.append({"key": g["key"], "title": g["title"], "projects": projects})
    return landing.tagline, landing.bio, groups


# ---------- images ----------

_exported = {}


def export(src):
    """Flatten and downscale a site image (first frame for GIFs) to a JPEG in the build dir.
    Returns (relative path, aspect ratio)."""
    if src not in _exported:
        rel = os.path.relpath(src, os.path.join(ROOT, "assets", "images"))
        out_name = re.sub(r"[^A-Za-z0-9]+", "-", os.path.splitext(rel)[0]).strip("-") + ".jpg"
        im = Image.open(src)
        im.seek(0)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            flat = Image.new("RGB", im.size, BG)
            flat.paste(im, mask=im.split()[-1])
            im = flat
        else:
            im = im.convert("RGB")
        im.thumbnail((MAX_PX, MAX_PX), Image.LANCZOS)
        im.save(os.path.join(BUILD, "img", out_name), "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
        _exported[src] = (f"img/{out_name}", im.width / im.height)
    return _exported[src]


# ---------- layout ----------

def esc(s):
    return html.escape(s, quote=True)


def title_html(p, tag, cls=""):
    classes = " ".join(c for c in (cls, "keep-case" if p["keep_case"] else "") if c)
    attr = f' class="{classes}"' if classes else ""
    return f'<{tag}{attr}>{esc(p["title"])}</{tag}>'


def gallery_segments(items):
    """Split a page's gallery into (heading, [figures]) runs; a gallery heading starts a new run."""
    segments = [(None, [])]
    for it in items:
        if it[0] == "heading":
            segments.append((it[1], []))
        else:
            segments[-1][1].append(it)
    return [s for s in segments if s[1]]


def pack_rows(figures):
    """Greedy justified rows: add images to a row until they'd drop below ROW_MIN_H or MAX_PER_ROW."""
    rows, row = [], []
    for fig in figures:
        ratio = export(fig[1])[1]
        trial = row + [(fig, ratio)]
        h = (CONTENT_W - GAP * (len(trial) - 1)) / sum(r for _, r in trial)
        if row and (h < ROW_MIN_H or len(trial) > MAX_PER_ROW):
            rows.append(row)
            row = [(fig, ratio)]
        else:
            row = trial
    if row:
        rows.append(row)
    return rows


def row_height(row):
    return (CONTENT_W - GAP * (len(row) - 1)) / sum(r for _, r in row)


def paginate(rows, avail_h):
    """Group rows onto pages, at most MAX_ROWS_PER_PAGE, as long as they fit without shrinking much."""
    pages, page, used = [], [], 0.0
    for row in rows:
        h = min(row_height(row), avail_h - CAPTION_H) + CAPTION_H
        if page and (len(page) >= MAX_ROWS_PER_PAGE or used + GAP + h > avail_h * 1.15):
            pages.append(page)
            page, used = [], 0.0
        page.append(row)
        used += h + (GAP if len(page) > 1 else 0)
    if page:
        pages.append(page)
    return pages


def render_rows(rows, avail_h, slug):
    """Every image in a row shares a height; the block scales down to fit the page."""
    natural = [row_height(r) for r in rows]
    fixed = CAPTION_H * len(rows) + GAP * (len(rows) - 1)
    scale = min(1.0, (avail_h - fixed) / sum(natural))
    out = []
    for row, h in zip(rows, natural):
        h *= scale
        cells = []
        for (fig, ratio) in row:
            src, _ = export(fig[1])
            caption = fig[2] + (f" (video: {SITE}/projects/{slug})" if fig[3] else "")
            cells.append(f'<figure style="width:{h * ratio:.3f}in"><img src="{src}" '
                         f'style="width:{h * ratio:.3f}in;height:{h:.3f}in" alt="">'
                         f'<figcaption>{esc(caption)}</figcaption></figure>')
        out.append(f'<div class="row">{"".join(cells)}</div>')
    return "".join(out)


def chrome(label, folio):
    return (f'<div class="running"><span>John Northrup</span><span>{label}</span></div>'
            f'<div class="folio">{folio:02d}</div>')


def build_html(tagline, bio, groups, subtitle):
    projects = [p for g in groups for p in g["projects"]]

    # Lay out every project first so the contents page knows its page numbers.
    project_pages = []  # (group, project, [page html builders])
    for g in groups:
        for p in g["projects"]:
            pages = []
            for heading, figures in gallery_segments(p["items"]):
                avail = CONTENT_H - (HEADING_H if heading else 0)
                for page_rows in paginate(pack_rows(figures), avail):
                    pages.append((heading, page_rows, avail))
            project_pages.append((g, p, pages))

    out = []
    # Cover: intro on the left, a mosaic of the first six covers on the right.
    tiles = "".join(f'<div class="tile"><img src="{export(p["hero"])[0]}" alt=""></div>'
                    for p in [q for q in projects if q["hero"]][:6])
    out.append(f"""
<section class="page cover">
  <div class="cover-text">
    <div class="eyebrow">{esc(subtitle)}</div>
    <h1>John<br>Northrup</h1>
    <p class="tagline">{esc(tagline)}</p>
    <p class="bio">{esc(bio)}</p>
    <div class="contact"><a href="mailto:{EMAIL}">{EMAIL}</a><a href="https://{SITE}">{SITE}</a></div>
  </div>
  <div class="mosaic">{tiles}</div>
</section>""")

    # Contents, grouped like the sidebar.
    page_no, rows_html, n = 3, [], 0
    for g in groups:
        rows_html.append(f'<li class="group">{esc(g["title"])}</li>')
        for gg, p, pages in project_pages:
            if gg is not g:
                continue
            n += 1
            rows_html.append(f'<li><span class="idx">{n:02d}</span>{title_html(p, "span", "t")}'
                             f'<span class="e">{esc(p["eyebrow"])}</span><span class="pg">{page_no:02d}</span></li>')
            page_no += 1 + len(pages)
    out.append(f"""
<section class="page contents">
  {chrome("Contents", 2)}
  <div class="contents-inner"><ol>{''.join(rows_html)}</ol></div>
</section>""")

    folio, n = 3, 0
    for g, p, pages in project_pages:
        n += 1
        label = f'{esc(g["title"])} · <span class="{"keep-case" if p["keep_case"] else ""}">{esc(p["title"])}</span>'
        advisor = (f'<div class="advisor">{p["advisor_label"]} · {esc(p["advisor"])}</div>' if p["advisor"] else "")
        body = "".join(f"<p>{esc(t)}</p>" for t in p["text"])
        notes = "".join(f'<p class="note">*{esc(t)}</p>' for t in p["notes"])
        text_block = (f'<div class="num">{n:02d}</div>{title_html(p, "h2")}'
                      f'<div class="eyebrow">{esc(p["eyebrow"])}</div>{advisor}{body}{notes}')
        if p["hero"]:
            hero_src, hero_r = export(p["hero"])
        else:
            hero_src, hero_r = None, 1.0
        long_text = sum(len(t) for t in p["text"]) > 900
        if hero_src and hero_r >= 1.6 and not long_text:
            img_h = min(CONTENT_W / hero_r, 4.2)
            out.append(f"""
<section class="page opener top">
  {chrome(label, folio)}
  <img class="hero" src="{hero_src}" style="width:{img_h * hero_r:.3f}in;height:{img_h:.3f}in" alt="">
  <div class="opener-text cols">{text_block}</div>
</section>""")
        else:
            box_w, box_h = 5.6, CONTENT_H
            w = min(box_w, box_h * hero_r)
            hero = (f'<img class="hero" src="{hero_src}" style="width:{w:.3f}in;height:{w / hero_r:.3f}in" alt="">'
                    if hero_src else "")
            out.append(f"""
<section class="page opener side">
  {chrome(label, folio)}
  <div class="hero-box" style="width:{box_w}in;height:{box_h}in">{hero}</div>
  <div class="opener-text">{text_block}</div>
</section>""")
        folio += 1

        for heading, page_rows, avail in pages:
            head = f'<h3 class="gallery-heading">{esc(heading)}</h3>' if heading else ""
            out.append(f"""
<section class="page gallery">
  {chrome(label, folio)}
  {head}
  <div class="rows" style="height:{avail:.3f}in">{render_rows(page_rows, avail, p["slug"])}</div>
</section>""")
            folio += 1

    css = open(os.path.join(HERE, "print.css"), encoding="utf-8").read()
    for k, v in {"PAGE_W": PAGE_W, "PAGE_H": PAGE_H, "MX": MARGIN_X, "MT": MARGIN_TOP,
                 "MB": MARGIN_BOTTOM, "GAP": GAP, "CAP": CAPTION_H}.items():
        css = css.replace("{{" + k + "}}", f"{v}in")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>John Northrup — Portfolio</title>
<style>{css}</style></head>
<body>{''.join(out)}</body></html>"""


def render(groups, tagline, bio, subtitle, output):
    html_path = os.path.join(BUILD, os.path.splitext(os.path.basename(output))[0] + ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(tagline, bio, groups, subtitle))
    subprocess.run(["node", os.path.join(HERE, "render.js"), html_path, output], check=True)
    print(f"Wrote {os.path.relpath(output, ROOT)} ({os.path.getsize(output) / 1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--full-only", action="store_true", help="skip the per-group PDFs")
    args = ap.parse_args()

    shutil.rmtree(BUILD, ignore_errors=True)
    os.makedirs(os.path.join(BUILD, "img"))
    shutil.copytree(os.path.join(HERE, "fonts"), os.path.join(BUILD, "fonts"))

    tagline, bio, groups = read_site()
    render(groups, tagline, bio, "Portfolio · 2023–2026", os.path.join(ROOT, "John-Northrup-Portfolio.pdf"))
    if not args.full_only:
        for g in groups:
            if g["projects"]:
                render([g], tagline, bio, f'Portfolio · {g["title"]}',
                       os.path.join(ROOT, f'John-Northrup-Portfolio-{g["key"]}.pdf'))


if __name__ == "__main__":
    sys.exit(main())
