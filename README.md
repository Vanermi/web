# Vanermi website

Source of [www.vanermi.com](https://www.vanermi.com): a static site in Spanish, with no admin
panel, no plugins and no database.

```
docs/              the site, exactly as it is published
  *.html           one file per page
  css/site.css     the only stylesheet
  img/             logo and icons
  .nojekyll        tells GitHub Pages to serve the files as they are
scripts/check.py   checks the site against the rules below
```

## Build

There is nothing to build and nothing to install. The pages are hand-written HTML, with no
generator and no dependencies (no Hugo, no npm). For seven pages this is simpler than a
generator, and it leaves no supply chain to audit. The files in `docs/` are the site.

## Preview locally

From the repository root, with any Python 3:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 -d docs
```

Then open <http://127.0.0.1:8000/>. Use a local server rather than opening the files directly:
under `file://` some browsers apply the Content-Security-Policy differently and the 404 page
uses root-relative paths.

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
  iframes, and no web fonts: text uses the system font stack. Links to other sites are plain
  links and load nothing.
- **No JavaScript and no cookies.** The site sets no cookies, and the cookie policy says so;
  adding anything that does would make that page false.
- **No forms.** Contact is a `mailto:` link.
- **Security headers as meta tags.** GitHub Pages cannot send custom headers, so every page
  starts its `<head>` with:

  ```html
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'self'; base-uri 'none'; form-action 'none'; upgrade-insecure-requests">
  <meta name="referrer" content="no-referrer">
  ```

  The CSP blocks every script, inline style, font, frame and connection, and allows only
  images and stylesheets from the site itself. A meta tag cannot set `frame-ancestors`,
  `report-uri` or `sandbox`, so those protections are not available on GitHub Pages.
- **Only images Vanermi owns.** `img/` holds the Vanermi logo and its icon, taken from the
  previous site (`wp-content/uploads/2025/10/`).
- **Public repository.** No secrets, no WordPress exports, no internal notes.

## Editing

The header, footer and `<head>` are repeated in every page. When you change one, change all
of them; `scripts/check.py` fails if the security meta tags differ between pages. To add a
page, copy an existing one, update `<title>`, the description and `aria-current="page"` in the
menu, and link it from the header or footer of every page.

Pending content is marked with `TODO` in a visible yellow box (`class="todo"`), so it cannot go
unnoticed in a preview.

## Publishing

Not set up yet: publishing with GitHub Pages comes in a later change. `docs/` is the folder to
publish. Any GitHub Actions workflow added to this repository must pin every action by its full
commit SHA.
