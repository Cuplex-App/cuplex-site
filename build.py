#!/usr/bin/env python3
"""Genera il sito statico di Cuplex in _site/ (solo libreria standard di Python 3).

    python3 build.py            # genera _site/
    python3 build.py --serve    # genera e apre un server locale su http://localhost:8000

Ogni pagina e' un frammento HTML in content/<lingua>/<pagina>.html, inserito in templates/layout.html.
I testi comuni (menu, piè di pagina, titoli) stanno in content/strings.json; i dati del titolare, le email e i
link stanno in site.json: un valore null diventa un segnaposto evidenziato nella pagina.
"""

import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"
LANGS = ["it", "en", "fr", "es"]  # la prima e' alla radice del sito, le altre in /<lingua>/
PAGES = ["index", "plus", "privacy", "terms", "support"]
TOKEN = re.compile(r"\{\{\s*([a-z_:]+)\s*\}\}")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def page_href(lang, page, from_lang):
    """Link relativo alla pagina `page` in `lang`, visto da una pagina in `from_lang`."""
    prefix = "" if from_lang == LANGS[0] else "../"
    folder = "" if lang == LANGS[0] else f"{lang}/"
    name = "" if page == "index" else f"{page}.html"
    return f"{prefix}{folder}{name}" or "./"


class Renderer:
    def __init__(self, site, strings):
        self.site = site
        self.strings = strings
        self.unresolved = {}

    def placeholder(self, lang, key):
        label = self.strings[lang]["placeholders"].get(key) or self.strings[LANGS[0]]["placeholders"][key]
        self.unresolved.setdefault(key, self.strings[LANGS[0]]["placeholders"][key])
        return f'<mark class="todo">[{html.escape(label)}]</mark>'

    def value(self, lang, key):
        if key not in self.site["values"]:
            raise SystemExit(f"Segnaposto sconosciuto: {{{{{key}}}}} ({lang})")
        return self.site["values"][key]

    def token(self, lang, match, root):
        name = match.group(1)
        if name == "root":
            return root
        if name.startswith("mailto:"):
            key = name[len("mailto:"):]
            v = self.value(lang, key)
            if not v:
                return self.placeholder(lang, key)
            e = html.escape(v)
            return f'<a href="mailto:{e}">{e}</a>'
        if name.startswith("link:"):
            key = name[len("link:"):]
            v = self.value(lang, key)
            if not v:
                return self.placeholder(lang, key)
            e = html.escape(v)
            return f'<a href="{e}">{e}</a>'
        if name == "last_updated":
            return html.escape(self.site["last_updated"])
        v = self.value(lang, name)
        return html.escape(v) if v else self.placeholder(lang, name)

    def fill(self, lang, text, root=""):
        return TOKEN.sub(lambda m: self.token(lang, m, root), text)


def nav(lang, page, s):
    items = [("index", s["nav_home"]), ("plus", s["nav_plus"]), ("privacy", s["nav_privacy"]), ("terms", s["nav_terms"]),
             ("support", s["nav_support"])]
    out = []
    for p, label in items:
        current = ' aria-current="page"' if p == page else ""
        out.append(f'<li><a href="{page_href(lang, p, lang)}"{current}>{html.escape(label)}</a></li>')
    return "\n          ".join(out)


def lang_switch(lang, page, strings):
    out = []
    for l in LANGS:
        s = strings[l]
        current = ' aria-current="true"' if l == lang else ""
        out.append(
            f'<li><a href="{page_href(l, page, lang)}" lang="{l}" hreflang="{l}"{current}>'
            f'<abbr title="{html.escape(s["language_name"])}">{l.upper()}</abbr></a></li>'
        )
    return "\n          ".join(out)


def alternates(page, base_url):
    if not base_url:
        return ""
    base = base_url.rstrip("/") + "/"
    out = []
    for l in LANGS:
        folder = "" if l == LANGS[0] else f"{l}/"
        name = "" if page == "index" else f"{page}.html"
        out.append(f'<link rel="alternate" hreflang="{l}" href="{base}{folder}{name}">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{base}{"" if page == "index" else page + ".html"}">')
    return "\n  ".join(out)


def check_links(path, text):
    """Controlla che i link interni (relativi, .html o cartelle) puntino a file generati."""
    missing = []
    for href in re.findall(r'href="([^"#:?]+)(?:#[^"]*)?"', text):
        if href.startswith(("http", "mailto", "//")):
            continue
        target = (path.parent / href).resolve()
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            missing.append(href)
    return missing


def build():
    site = load_json(ROOT / "site.json")
    strings = load_json(ROOT / "content" / "strings.json")
    layout = (ROOT / "templates" / "layout.html").read_text(encoding="utf-8")
    r = Renderer(site, strings)

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")
    if site["values"].get("domain"):
        (OUT / "CNAME").write_text(site["values"]["domain"] + "\n")

    written = []
    for lang in LANGS:
        s = strings[lang]
        for page in PAGES:
            body = (ROOT / "content" / lang / f"{page}.html").read_text(encoding="utf-8")
            meta = s["pages"][page]
            is_legal = page in ("privacy", "terms")
            draft = ""
            if is_legal and site["draft"]:
                draft = f'<p class="draft-banner" role="note"><strong>{html.escape(s["draft_title"])}</strong> {html.escape(s["draft_text"])}</p>'
            root = "" if lang == LANGS[0] else "../"
            subs = {
                "lang": lang,
                "title": html.escape(meta["title"]),
                "description": html.escape(meta["description"]),
                "root": root,
                "home": page_href(lang, "index", lang),
                "skip": html.escape(s["skip"]),
                "nav_label": html.escape(s["nav_label"]),
                "lang_label": html.escape(s["lang_label"]),
                "nav": nav(lang, page, s),
                "langs": lang_switch(lang, page, strings),
                "alternates": alternates(page, site["values"].get("base_url")),
                "draft": draft,
                "body_class": f"page-{page}",
                "main": r.fill(lang, body, root),
                "footer": r.fill(lang, s["footer"]),
                "trademarks": html.escape(s["trademarks"]),
            }
            text = layout
            for k, v in subs.items():
                text = text.replace("{{" + k + "}}", v)
            leftover = TOKEN.findall(text)
            if leftover:
                raise SystemExit(f"Token non sostituiti in {lang}/{page}: {leftover}")
            dest = OUT / ("" if lang == LANGS[0] else lang) / f"{page}.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            written.append(dest)

    broken = {str(p.relative_to(OUT)): m for p in written if (m := check_links(p, p.read_text(encoding="utf-8")))}
    if broken:
        raise SystemExit(f"Link interni rotti: {broken}")

    print(f"Generate {len(written)} pagine in {OUT.relative_to(ROOT)}/")
    if r.unresolved:
        print("Segnaposto da compilare in site.json:")
        for key, label in sorted(r.unresolved.items()):
            print(f"  - {key}: {label}")
        if not site["draft"]:
            raise SystemExit("site.json ha draft=false ma restano segnaposto: compilali prima di pubblicare.")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import functools
        import http.server

        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("http://localhost:8000")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
