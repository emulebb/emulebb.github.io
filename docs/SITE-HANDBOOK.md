# eMuleBB Pages Site Handbook

This handbook is the maintainer contract for the public eMule broadband edition
site at `https://emulebb.github.io/`.

The site is a curated product presentation for eMule broadband edition, compactly
eMuleBB. It is not the canonical engineering ledger, release ledger, or feature
backlog. Those live in the public `emulebb-tooling` docs.

## Authority And Content Model

- `emulebb-tooling` active/reference docs are authoritative for product, feature,
  release, REST, and validation facts.
- If the website conflicts with `emulebb-tooling`, update the website or the
  linked source doc before publishing.
- The homepage summarizes and directs readers. Long-form setup, tuning, release,
  and API details belong in the rendered documentation site at
  `https://emulebb.github.io/emulebb-tooling/`, backed by Markdown in
  `emulebb-tooling`.
- Release status must be derived from the `0.7.3` active release docs:
  `RELEASE-0.7.3.md`, `RELEASE-0.7.3-CHECKLIST.md`,
  `RELEASE-0.7.3-RUNBOOK.md`, and `RELEASE-0.7.3-GATE-HISTORY.md`.
- The first public release candidate is `0.7.3-rc.1`; the first stable target
  is `0.7.3`. Both must be described as planned and not yet released until the
  release docs and user confirmation say otherwise.
- Feature details should prefer durable reference docs such as:
  - `docs/reference/GUIDE-EMULEBB.md`
  - `docs/reference/DEVELOPMENT-GUIDE.md`
  - `docs/reference/GUIDE-SETUP.md`
  - `docs/reference/GUIDE-NETWORK.md`
  - `docs/reference/GUIDE-DOWNLOADS-SEARCH.md`
  - `docs/reference/GUIDE-SHARING.md`
  - `docs/reference/GUIDE-CONTROLLERS-REST.md`
  - `docs/reference/FEATURE-BROADBAND.md`
  - `docs/reference/FEATURE-MODERN-LIMITS.md`
  - `docs/reference/FEATURE-KAD.md`
  - `docs/reference/FEATURE-PEERS-BANS.md`
  - `docs/rest/REST-API-CONTRACT.md`
  - `docs/rest/REST-API-OPENAPI.yaml`

## Voice And Brand

- Tone: technical, credible, direct, and readable for power users.
- Dry humor and eMule lore are allowed, especially in bounded sections such as
  Team, but factual sections must remain precise.
- Avoid marketing fog. Prefer concrete behavior: upload slots, Kad, REST,
  shared libraries, validation, release gates.
- Keep the site text-first outside the header logo and bounded Team/lore
  imagery.
- Do not publish favicon, screenshot, copied application artwork, or arbitrary
  brand image assets from this repository.
- Do not add copied application resource images such as `Logo.jpg`.
- The only current logo asset is
  `assets/brand/emulebb-broadband-edition-logo.png`, used in the site header.
- The Team/lore section may use small generated raster illustrations under
  `assets/team/` when explicitly requested. They must stay decorative,
  section-local, and separate from favicon or external product screenshots.
- Structured data must not include logo or image fields unless this policy is
  explicitly changed first.

## Homepage Section Contract

The English homepage is canonical. Keep this order unless a deliberate site
structure update changes the contract:

1. Header and primary navigation
2. Hero
3. Intro
4. Why/motivation
5. Features
6. Short guide
7. Team/lore
8. Docs
9. Implementation method
10. Automation
11. Release
12. Repositories
13. Footer

Rules:

- Required navigation anchors must resolve to existing section IDs.
- Keep one homepage capability section: `Features`. Do not add separate
  Highlights, Catalog, or similar duplicate feature sections.
- The homepage feature copy may highlight only landed, documented,
  passed, release-proven, or otherwise source-confirmed features.
- Open, deferred, exploratory, or future backlog items must not be presented as
  shipped homepage features.
- Future-facing items must stay out of homepage feature copy.
- The Docs section may link to source documents that contain roadmap or backlog
  material, but the homepage must not rephrase those items as product features.
- The Docs section should link to durable source documents rather than copying
  long explanations into the homepage.
- Public navigation and Docs-section links should target rendered pages under
  `https://emulebb.github.io/emulebb-tooling/`; link to GitHub blob Markdown only
  when a rendered page does not exist.
- The Why section may explain the learning and modernization exercise behind
  the project, but it must not blur planned release status or imply a rewrite.
- The Implementation method section may summarize engineering practice,
  compatibility boundaries, API contracts, and release proof, but source docs
  remain authoritative for detailed procedures.
- The Team section may use sarcasm and lore, but it must not obscure product
  facts or make claims about unshipped behavior.

## Feature Policy

Feature entries should be short, verifiable, and grouped by operator mental
model:

- Broadband upload and seeding
- Large-library and file handling
- Search, server, and Kad
- VPN/interface binding and WebServer exposure policy
- Modern performance limits
- Kad hardening and peer protection
- NAT/UPnP and network adversity validation
- REST, controllers, and automation
- Desktop power-user ergonomics
- Reliability and release proof

Before adding or changing a feature entry:

- Confirm the claim against `emulebb-tooling` docs or the relevant source repo.
- Refresh `docs/reference/GUIDE-EMULEBB.md` and focused guide chapters first
  when the homepage is summarizing newly landed behavior.
- Use `docs/reference/DEVELOPMENT-GUIDE.md` for the recurring product-guide and
  development-guide refresh workflow.
- Avoid ambiguous labels like "modernized" unless the concrete behavior is named.
- If a feature is not landed, documented, or source-confirmed, keep it out of
  homepage feature copy.
- Interface/VPN binding may be described as bind-target support and live-test
  policy. Do not describe the external VPN kill-switch design as built into
  eMuleBB.
- If a feature has changed status, update the source documentation first or link
  to the updated source.

## Localization Policy

- English (`/`) is canonical.
- Static locale pages are generated from the English structure for the stock
  eMule language set:
  `/ar-ae/`, `/eu/`, `/bg/`, `/ca/`, `/cs/`, `/da/`, `/el/`, `/es/`,
  `/ast/`, `/et/`, `/fa/`, `/fi/`, `/br/`, `/pt-br/`, `/pt-pt/`, `/gl/`,
  `/he/`, `/hu/`, `/it/`, `/ja/`, `/ko/`, `/lt/`, `/lv/`, `/mt/`, `/nb/`,
  `/ru/`, `/de/`, `/fr/`, `/pl/`, `/nl/`, `/nn/`, `/ro/`, `/sl/`, `/sq/`,
  `/sv/`, `/tr/`, `/uk/`, `/ug-cn/`, `/ca-valencia/`,
  `/ca-valencia-racv/`, `/vi/`, `/zh-cn/`, and `/zh-tw/`.
- Generated HTML is committed for GitHub Pages, but localized homepage content
  must be changed through structured JSON under `content/` or the shared
  renderer rules in `tools/render_pages.py`, then rendered through the Jinja2
  templates under `templates/`.
- Completed locale pages use `index,follow`.
- `/languages/` is the indexable language selector and is included in
  `sitemap.xml`.
- `/faq/` is the canonical English FAQ. Completed FAQ translations are
  published under selected locale directories: `/it/faq/`, `/es/faq/`,
  `/pt-br/faq/`, `/fr/faq/`, `/de/faq/`, `/pl/faq/`, `/nl/faq/`, `/ru/faq/`,
  `/uk/faq/`, `/zh-cn/faq/`, and `/ja/faq/`.
- Do not add generic compatibility chooser URLs such as `/pt/`; Portuguese is
  represented by the real regional pages `/pt-br/` and `/pt-pt/`.
- Complete localized pages must:
  - match the English section contract
  - use translated titles, descriptions, headings, and body copy
  - keep the same product facts and docs authority
  - include reciprocal `hreflang` alternates
  - be added to `sitemap.xml`
  - switch from `noindex,follow` to `index,follow`
- Do not let localized pages independently diverge in feature claims or release
  status.
- Preserve established technical terms in localized copy, including `eD2K`,
  `Kad`, `REST`, `JSON`, `API`, `WebServer`, `VPN/interface binding`,
  `UPnP/NAT`, `x64`, `ARM64`, `Debug`, `Release`, repo names, paths, URLs,
  commands, and code identifiers.

## SEO And Metadata Policy

Every indexable page must have:

- one clear `<title>`
- one useful meta description
- `robots` policy
- canonical URL
- reciprocal `hreflang` alternates
- Open Graph title, description, type, and URL where appropriate
- structured data only when it can be kept accurate

Search/publishing rules:

- `robots.txt` must point to `sitemap.xml`.
- `sitemap.xml` must include only complete, indexable pages.
- Locale stubs and non-indexable compatibility chooser pages stay out of
  `sitemap.xml`.
- Metadata and structured data must not mention or point to logos/images. The
  header logo is a visible page asset only.

## Layout And CSS Policy

- Keep UI dense, readable, and text-first.
- Do not put cards inside cards.
- Keep cards at `8px` border radius or less.
- Maintain stable section IDs for anchor navigation.
- Sticky-header anchor behavior must be tested on desktop and mobile.
- Mobile nav should remain usable without horizontal scrolling; the current
  pattern is a wrapped grid on small screens and a horizontal nav on desktop.
- Use CSS variables in `:root` for shared colors.
- Do not introduce a one-hue palette; retain restrained contrast across teal,
  blue, green, red, and gold accents.

## Update Workflow

Use granular commits. Split unrelated work:

- policy/documentation
- homepage content
- layout/CSS
- SEO/metadata/sitemap
- locale structure/content

Commit messages should name the slice, for example:

- `Document site maintenance policy`
- `Update feature copy`
- `Fix mobile anchor layout`
- `Refresh SEO metadata`
- `Generate Spanish page`

Push after each coherent commit when the user has requested publishing.

## Source Markdown To Public HTML

The long-form documentation site is generated from Markdown in
`emulebb-tooling`, not from this repository. Use this sequence when public
homepage copy depends on product-guide, release, REST, or evidence claims:

1. Update the owning Markdown source under `..\emulebb-tooling\docs`.
2. Validate the Markdown-to-HTML publish gate:

   ```powershell
   cd ..\emulebb-tooling
   python scripts\docs-publish-check.py
   ```

3. Commit and push the tooling-docs slice so GitHub Actions can publish
   `https://emulebb.github.io/emulebb-tooling/`.
4. Return to `emulebb-pages`, update the structured homepage source, then
   regenerate committed HTML with `tools\render_pages.py`.

Homepage copy should say less than the product guide and link to the rendered
HTML docs for the details. Testing, SBOM, package, release, REST, and
performance claims must be true in `emulebb-tooling` before they are repeated on
the static pages.

## Required Validation

Run these checks before committing and pushing:

```powershell
python -m pip install -r requirements.txt
python tools\render_pages.py --lastmod 2026-05-23 --check
python ..\emulebb-tooling\helpers\pages-site-tools.py --pages-root . validate
git diff --check
rg -n "emule-logo|Logo\.jpg|favicon|screenshot" index.html styles.css ar-ae eu bg ca cs da el es ast et fa fi br pt-br pt-pt gl he hu it ja ko lt lv mt nb ru de fr pl nl nn ro sl sq sv tr uk ug-cn ca-valencia ca-valencia-racv vi zh-cn zh-tw languages
```

Anchor check:

```powershell
$html = Get-Content -Raw index.html
$ids = [regex]::Matches($html, 'id="([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
$anchors = [regex]::Matches($html, 'href="#([^"]+)"') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
foreach ($anchor in $anchors) {
  if ($ids -notcontains $anchor) {
    throw "Missing anchor target: #$anchor"
  }
}
```

Curated rendered-doc link check:

```powershell
$files = Get-ChildItem -Recurse -Filter index.html |
  Where-Object { $_.FullName -notmatch '\\.git\\' } |
  ForEach-Object { $_.FullName }
foreach ($file in $files) {
  $html = Get-Content -Raw $file
  $urls = [regex]::Matches($html, 'https://emulebb.github.io/emulebb-tooling/([^\"#?]+)') |
    ForEach-Object { $_.Groups[1].Value } |
    Sort-Object -Unique
  foreach ($urlPath in $urls) {
    if ($urlPath -eq '' -or $urlPath -eq 'INDEX/') {
      continue
    }
    $path = 'docs/' + ($urlPath.TrimEnd('/') -replace '/', '\') + '.md'
    $local = Join-Path '..\emulebb-tooling' $path
    if (-not (Test-Path -LiteralPath $local)) {
      throw "Missing rendered-doc source: ${file}: $urlPath -> $path"
    }
  }
}
```

Locale metadata check:

```powershell
$files = Get-ChildItem -Recurse -Filter index.html |
  Where-Object { $_.FullName -notmatch '\\.git\\' } |
  ForEach-Object { $_.FullName }
foreach ($file in $files) {
  $html = Get-Content -Raw $file
  if ($html -notmatch '<title>') { throw "Missing title: $file" }
  if ($html -notmatch '<link[^>]+rel="canonical"') { throw "Missing canonical: $file" }
  if ($html -notmatch 'hreflang="x-default"') { throw "Missing x-default: $file" }
  if ($html -notmatch 'content="index,follow"') { throw "Locale not indexable: $file" }
}
if (Test-Path -LiteralPath 'pt/index.html') { throw 'Unexpected generic Portuguese chooser' }
```

Robots and sitemap check:

```powershell
$xml = [xml](Get-Content -Raw sitemap.xml)
if (-not $xml.urlset.url.loc) { throw 'Sitemap has no URLs' }
if ((Get-Content -Raw robots.txt) -notmatch 'Sitemap: https://emulebb.github.io/sitemap.xml') {
  throw 'Missing sitemap directive'
}
```

For layout, anchor, or navigation changes, also manually review desktop and
mobile rendering before pushing.

## Current Public Structure

Current public files:

- `index.html`: canonical English page
- locale `index.html` files under the stock eMule language directories listed
  in the Localization Policy
- `languages/index.html`: indexable language selector
- `faq/index.html`: canonical English FAQ
- selected locale FAQ pages under `/it/faq/`, `/es/faq/`, `/pt-br/faq/`,
  `/fr/faq/`, `/de/faq/`, `/pl/faq/`, `/nl/faq/`, `/ru/faq/`, `/uk/faq/`,
  `/zh-cn/faq/`, and `/ja/faq/`
- `styles.css`: shared styles
- `robots.txt`: crawler policy
- `sitemap.xml`: indexable URL list
- `AGENTS.md`: short agent policy
- `docs/SITE-HANDBOOK.md`: this handbook
