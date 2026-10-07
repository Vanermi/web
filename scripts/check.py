#!/usr/bin/env python3
"""Checks the site in docs/ against the rules in the README.

Standard library only. Run from the repository root:

    python3 scripts/check.py [site-directory]

Exits with status 1 if any rule is broken. Also lists the outbound links
(plain navigation, which loads nothing) and the pending TODOs.
"""

import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

SITE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                    pathlib.Path(__file__).resolve().parent.parent / "docs").resolve()

CSP = ("default-src 'none'; img-src 'self'; style-src 'self'; base-uri 'none'; "
       "form-action 'none'; upgrade-insecure-requests")
REFERRER = "no-referrer"

# Elements that would run code, embed third parties, collect data or need a looser CSP.
FORBIDDEN_TAGS = {"script", "noscript", "iframe", "frame", "frameset", "object", "embed",
                  "applet", "form", "input", "textarea", "select", "button", "video",
                  "audio", "source", "track", "canvas", "base", "style", "portal"}
# Attributes whose value the browser fetches.
RESOURCE_ATTRS = {"src", "srcset", "poster", "data", "background", "action", "formaction",
                  "manifest", "ping"}
ALLOWED_FILES = {".html", ".css", ".webp", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".txt", ""}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []          # (tag, attrs dict, line)
        self.ids = set()
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        self.tags.append((tag, a, self.getpos()[0]))
        if "id" in a:
            self.ids.add(a["id"])

    handle_startendtag = handle_starttag

    def handle_data(self, data):
        self.text.append(data)


def is_offsite(url):
    u = url.strip()
    if u.startswith("//"):
        return True
    scheme = urlsplit(u).scheme.lower()
    return scheme not in ("", "mailto")


def target_file(page_path, url):
    """Resolve a same-site link to a file in docs/, or None if it is not a file link."""
    parts = urlsplit(url)
    if parts.scheme or url.startswith("//"):
        return None
    path = parts.path
    if not path:
        return page_path
    base = SITE if path.startswith("/") else page_path.parent
    f = (base / path.lstrip("/")).resolve()
    return f / "index.html" if path.endswith("/") else f


def main():
    errors, outbound, todos = [], [], []

    def err(where, msg):
        errors.append(f"{where}: {msg}")

    for f in sorted(SITE.rglob("*")):
        if f.is_file() and f.suffix.lower() not in ALLOWED_FILES:
            err(f.relative_to(SITE), "file type not allowed on the site")

    pages = sorted(SITE.rglob("*.html"))
    parsed = {}
    for f in pages:
        p = Page()
        p.feed(f.read_text(encoding="utf-8"))
        parsed[f] = p

    for f, p in parsed.items():
        name = f.relative_to(SITE)
        tags = [t for t, _, _ in p.tags]

        html = next((a for t, a, _ in p.tags if t == "html"), {})
        if html.get("lang") != "es":
            err(name, '<html> must have lang="es"')

        metas = [a for t, a, _ in p.tags if t == "meta"]
        if not metas or metas[0].get("charset", "").lower() != "utf-8":
            err(name, '<meta charset="utf-8"> must be the first meta')
        if len(metas) < 2 or metas[1].get("http-equiv", "").lower() != "content-security-policy":
            err(name, "the CSP meta must come right after the charset, before anything loads")
        csp = [a.get("content") for a in metas if a.get("http-equiv", "").lower() == "content-security-policy"]
        if csp != [CSP]:
            err(name, f"CSP meta missing or different: {csp}")
        ref = [a.get("content") for a in metas if a.get("name") == "referrer"]
        if ref != [REFERRER]:
            err(name, f"referrer meta missing or different: {ref}")
        for a in metas:
            if a.get("http-equiv", "").lower() in ("refresh", "set-cookie"):
                err(name, f"meta http-equiv={a['http-equiv']} not allowed")

        for t, a, line in p.tags:
            where = f"{name}:{line}"
            if t in FORBIDDEN_TAGS:
                err(where, f"<{t}> not allowed")
            if "style" in a:
                err(where, "inline style attribute (blocked by the CSP)")
            for k in a:
                if k.startswith("on"):
                    err(where, f"event handler attribute {k}")
            for k in RESOURCE_ATTRS & a.keys():
                for url in re.split(r"\s*,\s*", a[k]) if k == "srcset" else [a[k]]:
                    url = url.split()[0] if url.strip() else ""
                    if is_offsite(url):
                        err(where, f"{k}={url!r} loads something from another origin")
                    elif url and not target_file(f, url).is_file():
                        err(where, f"{k}={url!r} does not exist")
            if t == "link":
                url = a.get("href", "")
                if is_offsite(url):
                    err(where, f"<link href={url!r}> loads something from another origin")
                elif not target_file(f, url).is_file():
                    err(where, f"<link href={url!r}> does not exist")
            if t == "img":
                if "alt" not in a:
                    err(where, "<img> without alt")
                if not (a.get("width") and a.get("height")):
                    err(where, "<img> without width and height")
            if t == "a" and "href" in a:
                url = a["href"]
                if url.startswith("javascript:"):
                    err(where, "javascript: link")
                elif url.startswith("mailto:"):
                    pass
                elif is_offsite(url):
                    outbound.append((str(name), url))
                else:
                    target = target_file(f, url)
                    frag = urlsplit(url).fragment
                    if not target.is_file():
                        err(where, f"broken link {url!r}")
                    elif frag and frag not in parsed.get(target, Page()).ids:
                        err(where, f"broken anchor {url!r}")

        headings = [int(t[1]) for t in tags if re.fullmatch(r"h[1-6]", t)]
        if headings.count(1) != 1:
            err(name, f"needs exactly one <h1>, has {headings.count(1)}")
        for prev, cur in zip(headings, headings[1:]):
            if cur > prev + 1:
                err(name, f"heading level jumps from h{prev} to h{cur}")

        n = len(re.findall(r"\bTODO\b", "".join(p.text)))
        if n:
            todos.append((str(name), n))

    for f in sorted(SITE.rglob("*.css")):
        css = f.read_text(encoding="utf-8")
        if "@import" in css:
            err(f.relative_to(SITE), "@import not allowed")
        for url in re.findall(r"url\(\s*['\"]?([^'\")]+)", css):
            if is_offsite(url):
                err(f.relative_to(SITE), f"url({url}) loads something from another origin")

    # Belt and braces: every absolute URL anywhere in the text files.
    found = []
    for f in sorted(SITE.rglob("*")):
        if f.is_file() and f.suffix in (".html", ".css", ".txt"):
            for m in re.finditer(r"(?:https?:)?//[^\s\"'<>)]+", f.read_text(encoding="utf-8")):
                found.append((str(f.relative_to(SITE)), m.group(0)))
    nav = set(outbound)
    for item in found:
        if item not in nav:
            err(item[0], f"absolute URL outside an <a href>: {item[1]}")

    print(f"Pages ({len(pages)}): " + ", ".join(str(f.relative_to(SITE)) for f in pages))
    print("\nOutbound links (navigation only, nothing is loaded from them):")
    for page, url in sorted(set(outbound)):
        print(f"  {page}: {url}")
    print("\nPending TODOs:")
    for page, n in todos:
        print(f"  {page}: {n}")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print(f"  {e}")
        return 1
    print("\nOK: no rule broken.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
