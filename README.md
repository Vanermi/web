# Vanermi website

Source of [www.vanermi.com](https://www.vanermi.com): a static copy of the current landing page
(previously built with WordPress and Elementor), plus a legal notice and a privacy page. No
admin panel, no plugins, no database.

```
docs/                     the site, exactly as it is published
  index.html              the landing (English)
  aviso-legal.html        legal notice (Spanish)
  privacidad.html         privacy policy (Spanish)
  css/site.css            the only stylesheet
  fonts/                  Montserrat, served from the site itself, and its licence
  img/                    logo and icons
  .nojekyll               tells GitHub Pages to serve the files as they are
scripts/check.py          checks the site against the rules below
```

## Build

There is nothing to build and nothing to install. The pages are hand-written HTML and CSS,
with no generator and no dependencies (no Hugo, no npm). The files in `docs/` are the site.

## Preview locally

From the repository root, with any Python 3:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 -d docs
```

Then open <http://127.0.0.1:8000/>. Use a local server rather than opening the files directly:
under `file://` browsers apply the Content-Security-Policy differently and may block the
stylesheet and the font.

## Check before every commit

```sh
python3 scripts/check.py
```

It uses only the Python standard library. It fails if a page loads anything from another
origin, contains a script, form, iframe, embed or inline style, lacks the security meta tags,
has a broken internal link, an image without `alt`, or a skipped heading level. It also lists
the outbound links and the pending `TODO`s.

To validate the HTML and CSS as well, the W3C Nu validator can run locally without network
access:

```sh
cd docs && docker run --rm --network none -v "$PWD:/site:ro" -w /site \
  ghcr.io/validator/validator:latest vnu --also-check-css *.html css/*.css
```

Under `file://` it reports the CSP as blocking the stylesheet and images; those notices do not
apply over HTTP.

## Rules

- **Nothing from third parties.** No analytics, trackers, CDNs, embedded videos, maps or
  iframes, and nothing loaded from Google. Links to other sites (the social profiles) are plain
  links and load nothing.
- **No JavaScript and no cookies.** The privacy page says the site sets no cookies; adding
  anything that does would make it false.
- **No forms.** Contact is a `mailto:` link.
- **Security headers as meta tags.** GitHub Pages cannot send custom headers, so every page
  starts its `<head>` with:

  ```html
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'; upgrade-insecure-requests">
  <meta name="referrer" content="no-referrer">
  ```

  The CSP blocks every script, inline style, frame and connection, and allows only images,
  stylesheets and fonts from the site itself. A meta tag cannot set `frame-ancestors`,
  `report-uri` or `sandbox`, so those protections are not available on GitHub Pages.
- **Public repository.** No secrets, no WordPress exports, no internal notes.

## Assets and licences

| File | Origin | Licence |
|---|---|---|
| `img/vanermi-logo.webp` | Previous site: `wp-content/uploads/2025/10/Color-logo-with-background-scaled.webp` | Vanermi |
| `img/apple-touch-icon-180.webp`, `img/favicon-192.webp`, `img/favicon-32.webp` | Previous site: `wp-content/uploads/2025/10/cropped-Color-favicon-no-background-180x180-1-{180x180,192x192,32x32}.webp` | Vanermi |
| `fonts/montserrat-latin.woff2` | Montserrat, Latin subset, weights 300–700, as served by Google Fonts (v31). SHA-256 `06b16db7a969135d48d38c49183be7fb88d4452e2a3011957c7851941f4e4879` | SIL Open Font License 1.1 (`fonts/OFL.txt`, from google/fonts) |
| Social icons, inline SVG in `index.html` | Font Awesome Free brand icons, copied from the previous site's markup | CC BY 4.0 (Font Awesome Free, fontawesome.com/license/free) |

The images are copied unmodified. Montserrat is the only font the landing displays; the
previous site also loaded Poppins but did not display it.

## Editing

The header, footer and `<head>` are repeated in every page. When you change one, change all
of them; `scripts/check.py` fails if the security meta tags differ between pages.

Missing data is marked with `TODO` in a visible yellow box (`class="todo"`), so it cannot go
unnoticed in a preview.

## Publishing

Not set up yet: publishing with GitHub Pages comes in a later change. `docs/` is the folder to
publish. Any GitHub Actions workflow added to this repository must pin every action by its full
commit SHA.
