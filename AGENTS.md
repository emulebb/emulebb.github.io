# Rules

- Read `EMULEBB_WORKSPACE_ROOT\repos\emulebb-tooling\docs\WORKSPACE-POLICY.md`
  first; it is authoritative for workspace-wide rules.
- Start from
  `EMULEBB_WORKSPACE_ROOT\repos\emulebb-tooling\docs\reference\AGENT-CHECKLIST.md`
  for the repeatable operating path.
- Then read `docs/SITE-HANDBOOK.md` before making content, layout, SEO, locale,
  or publishing-policy changes.

This repository publishes the public GitHub Pages site for eMule broadband
edition. Everything below is this repo's local deltas only.

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
- Treat `..\emulebb-tooling\manifests\public-presence.v1.json` as the source
  for current lanes, repository roles, compatibility references, public
  surfaces, and stable-installer ownership.
- Only shipped, landed, passed, or release-proven features belong in the public
  homepage feature/catalog copy.
- Keep English canonical. Only the homepage and FAQ have localized variants.
  Their copy is frozen, minimal, and evergreen: do not add versions, beta
  targets, ETAs, or time-sensitive release status. The English-only `/rust/`
  page owns current Rust product positioning. Locale pages keep the English
  section structure, reciprocal `hreflang` links, and `index,follow`.
- Use `/languages/` as the language selector. Do not add generic compatibility
  locale chooser URLs such as `/pt/` unless they are real indexable locale
  pages with their own maintained copy.
- Generated HTML remains committed as a drift check and branch-publishing
  fallback. Production GitHub Pages deployment uses the clean artifact staged
  by `tools\render_pages.py` from the renderer, templates, structured copy, and
  public-presence contract.
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
  confirm committed HTML is up to date with the templates and public-presence
  contract.
- Use `python tools\render_pages.py --lastmod YYYY-MM-DD --output-root
  .local\site` to stage the bounded deployment artifact.
- Use `python ..\emulebb-tooling\helpers\pages-site-tools.py --pages-root . validate`
  before publishing locale, metadata, sitemap, asset-policy, or navigation
  changes.
- Use the renderer to regenerate `sitemap.xml` from the canonical locale table.
