# eMuleBB Pages Agent Policy

This repository publishes the public GitHub Pages site for eMule broadband
edition.

Read and follow
`EMULEBB_WORKSPACE_ROOT\repos\emulebb-tooling\docs\WORKSPACE-POLICY.md` first
when this repo is checked out under the canonical eMuleBB workspace. Then read
`docs/SITE-HANDBOOK.md` before making content, layout, SEO, locale, or
publishing-policy changes.

## Hard Rules

- Do not publish mascot, screenshot, copied application artwork, or other brand
  image assets from this repository unless explicitly approved. The current
  image exceptions are the header logo at
  `assets/brand/emulebb-broadband-edition-logo.png`, the favicon at
  `assets/brand/emulebb-favicon.ico`, and Team/lore raster images under
  `assets/team/`.
- Keep the site text-first outside the header logo and bounded Team/lore
  imagery. Do not add image fields to metadata or structured data unless this
  policy changes again.
- Treat `emulebb-tooling` active/reference docs as the source of truth. Pages
  summarizes and links; it does not invent feature or release facts.
- Only shipped, landed, passed, or release-proven features belong in the public
  homepage feature/catalog copy.
- Keep English canonical. Completed locale pages are generated for stock eMule
  languages from `tools\render_pages.py` and JSON copy under `content\`; they
  should match the English section structure, use reciprocal `hreflang` links,
  and stay `index,follow`.
- Use `/languages/` as the language selector. Do not add generic compatibility
  locale chooser URLs such as `/pt/` unless they are real indexable locale
  pages with their own maintained copy.
- The generated HTML pages are committed, but the production source is the
  Jinja2 renderer in `tools\render_pages.py` plus templates under `templates\`.
- Preserve technical terms such as `eD2K`, `Kad`, `REST`, `JSON`, `API`,
  `WebServer`, `VPN/interface binding`, `UPnP/NAT`, `x64`, `ARM64`, `Debug`,
  `Release`, repo names, file paths, URLs, command names, and code identifiers
  in localized copy unless the English source intentionally changes them.
- Use granular commits: separate policy, content, layout, SEO, and locale work.
- Run the static validation checks in `docs/SITE-HANDBOOK.md` before committing
  and pushing.

## Supporting Tooling

- Page production and validation helpers are tracked in
  `..\emulebb-tooling\helpers\pages-site-tools.py`.
- Use `python -m pip install -r requirements.txt` when the local Python
  environment does not already have the renderer dependencies.
- Use `python tools\render_pages.py --lastmod YYYY-MM-DD` to regenerate static
  pages and `python tools\render_pages.py --lastmod YYYY-MM-DD --check` to
  confirm committed HTML is up to date with the templates.
- Use `python ..\emulebb-tooling\helpers\pages-site-tools.py --pages-root . validate`
  before publishing locale, metadata, sitemap, asset-policy, or navigation
  changes.
- Use the renderer to regenerate `sitemap.xml` from the canonical locale table.
