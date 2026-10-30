# eMuleBB Pages Site Handbook

This handbook is the maintainer contract for the public eMule broadband edition
site at `https://emulebb.github.io/`.

The site is the curated public front door for the eMuleBB organization. It
presents CI-gated `emulebb-rust` nightly builds as the active beta testing
channel and eMuleBB MFC `0.7.x` as the maintained Windows lane. Beta 3 is
expected after a few more weeks of implementation and stabilization. Rust
development is best-effort and spare-time, and contributors are welcome. The
site is not the canonical engineering ledger, release ledger, or feature
backlog. Those live in the public `emulebb-tooling` docs and the owning release
repositories.

## Authority And Content Model

- `emulebb-tooling` active/reference docs are authoritative for product, feature,
  release, REST, and validation facts.
- `..\emulebb-tooling\manifests\public-presence.v1.json` is the
  machine-readable authority for current lanes, repository roles,
  compatibility references, public surfaces, and stable-installer ownership.
- If the website conflicts with `emulebb-tooling`, update the website or the
  linked source doc before publishing.
- The homepage summarizes and directs readers. Long-form setup, tuning, release,
  and API details belong in the rendered documentation site at
  `https://emulebb.github.io/emulebb-tooling/`, backed by Markdown in
  `emulebb-tooling`.
- Organization lifecycle status must be derived from
  `docs/active/PRODUCT-DIRECTION.md` in `emulebb-tooling`; Rust scope and active
  work remain in `docs/products/emulebb-rust/`.
- MFC release status must be derived from the retained `0.7.3` release proof,
  notes, and stable changelog under `docs/history/releases/0.7.3/`.
- The current public release is stable `0.7.3` (published 2026-07-05). Older
  `0.7.3-rc.*` releases are historical prerelease evidence, not the current
  install target.
- The active product-development download channel is the CI-gated
  `emulebb-rust` nightly prereleases from `main`. Formal beta tags remain
  immutable release evidence, not the public front-door download target.
- The public Rust status is Active beta. Tell users to choose the newest dated
  nightly prerelease from GitHub Releases. Beta 3 is expected after a few more
  weeks of implementation and stabilization. The approved testing summary is:
  “Repeatedly tested on live eD2K/Kad networks.”
- Rust development is best-effort and spare-time. Public copy should welcome
  contributors and link to the repository's `CONTRIBUTING.md`.
- The historical MFC `0.7.3` suite installer and aMuTorrent package remain
  published artifacts, but “Suite” is not an active umbrella roadmap.
- Feature details should prefer durable reference docs such as:
  - `docs/reference/GUIDE-EMULEBB.md`
  - `docs/reference/DEVELOPMENT-GUIDE.md`
  - `docs/reference/GUIDE-SETUP.md`
  - `docs/reference/GUIDE-NETWORK.md`
  - `docs/reference/GUIDE-DOWNLOADS-SEARCH.md`
  - `docs/reference/GUIDE-SHARING.md`
  - `docs/reference/GUIDE-CONTROLLERS-REST.md`
  - `docs/reference/RELEASED-BEHAVIOR-SUMMARY.md`
  - `docs/reference/GUIDE-PREFERENCES.md`
  - `docs/reference/GUIDE-IP-FILTERS.md`
  - `docs/rest/REST-API-CONTRACT.md`
  - `docs/rest/REST-API-OPENAPI.yaml`

## Voice And Brand

- Tone: technical, credible, direct, and readable for power users.
- Dry humor and eMule lore are allowed in supporting documentation, but public
  homepage copy must remain focused and precise.
- Avoid marketing fog. Prefer concrete behavior: upload slots, Kad, REST,
  shared libraries, validation, release gates.
- Keep every HTML page text-only. Use the `eMuleBB` text wordmark in headers.
- Do not publish logos, screenshots, copied application artwork, mascots, or
  arbitrary raster assets from this repository.
- Do not add copied application resource images such as `Logo.jpg`.
- The browser favicon at `assets/brand/emulebb-favicon.ico` is the only image
  exception.
- Structured data must not include logo or image fields unless this policy is
  explicitly changed first.

## Homepage Section Contract

The English homepage is canonical. Keep this focused order:

1. Hero that defines eMuleBB Rust, with nightlies as the primary action and MFC
   as a secondary link
2. Concise eMuleBB Rust capability summary
3. Essential downloads and documentation
4. Focused repositories

Rules:

- Required navigation anchors must resolve to existing section IDs.
- The hero must explain that eMuleBB Rust is an eD2K/Kad client and name its
  operating surfaces before discussing release posture.
- The second block must summarize the supported search/download,
  share/upload/seed, and WebUI/API operating capabilities.
- Do not add separate feature catalogs, highlights, team/lore, implementation,
  automation, or release sections. Link to the product docs instead.
- Homepage proof may highlight only landed, documented, passed,
  release-proven, or otherwise source-confirmed behavior.
- MFC feature copy must be labeled as stable shipped capability, not active
  broad development. Rust capability claims must be nightly beta-channel
  specific and evidence-bound.
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
- Keep explanatory history, implementation method, automation detail, and lore
  in the rendered documentation site rather than duplicating them on the
  homepage.

## Homepage Proof Policy

Proof entries stay short, verifiable, and limited to the active Rust product:

- live eD2K/Kad network testing
- CI-gated native packages
- checksums and provenance
- the next beta milestone only when the public-presence contract authorizes it

Confirm every claim against `emulebb-tooling` docs, the public-presence
contract, or the owning source repository. Put protocol detail, feature catalogs,
controller workflows, historical releases, and future backlog in the rendered
documentation rather than expanding the homepage.

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
- Localized homepage and FAQ copy is intentionally frozen, minimal, and
  evergreen. It may link to GitHub Releases and the Rust product docs, but must not contain
  versions, beta targets, ETAs, nightly status, or other release-cycle claims.
  Future Rust status changes are made only in canonical English surfaces.
- Completed locale pages use `index,follow`.
- `/languages/` is the indexable language selector and is included in
  `sitemap.xml`.
- `/faq/` is the canonical English FAQ. Completed FAQ translations are
  published under selected locale directories: `/it/faq/`, `/es/faq/`,
  `/pt-br/faq/`, `/pt-pt/faq/`, `/fr/faq/`, `/de/faq/`, `/pl/faq/`,
  `/nl/faq/`, `/ru/faq/`, `/tr/faq/`, `/uk/faq/`, `/ko/faq/`, `/ar-ae/faq/`,
  `/zh-cn/faq/`, and `/ja/faq/`.
- `/rust/` is a no-index compatibility redirect to `/`. Do not add product
  content, localized variants, `hreflang` alternates, or a sitemap entry there.
- Do not add generic compatibility chooser URLs such as `/pt/`; Portuguese is
  represented by the real regional pages `/pt-br/` and `/pt-pt/`.
- Complete localized pages must:
  - match the English section contract
  - use the frozen translated titles, descriptions, headings, and body copy
  - remain evergreen instead of mirroring current release facts
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
- reciprocal `hreflang` alternates for localized homepage and FAQ families;
  the `/rust/` compatibility redirect intentionally has none
- Open Graph title, description, type, and URL where appropriate
- structured data only when it can be kept accurate

Search/publishing rules:

- `robots.txt` must point to `sitemap.xml`.
- `sitemap.xml` must include only complete, indexable pages.
- Locale stubs and non-indexable compatibility chooser pages stay out of
  `sitemap.xml`.
- Metadata and structured data must not mention or point to logos or images.

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

3. Commit the tooling-docs or public-presence contract slice in its owning
   repository.
4. Return to `emulebb-pages`, update any site-owned structured copy, then
   regenerate committed HTML with `tools\render_pages.py`.
5. Commit the Pages slice independently. Each repository publishes itself;
   cross-repository automation validates drift but does not push content.

Homepage copy should say less than the product guide and link to the rendered
HTML docs for the details. Testing, SBOM, package, release, REST, and
performance claims must be true in `emulebb-tooling` before they are repeated on
the static pages.

## Required Validation

Run these checks before committing and pushing:

```powershell
python -m pip install -r requirements.txt
python ..\emulebb-tooling\helpers\public-presence.py validate
$lastmod = ([regex]::Match((Get-Content -Raw sitemap.xml), '<lastmod>([^<]+)</lastmod>')).Groups[1].Value
python tools\render_pages.py --lastmod $lastmod --check
python tools\render_pages.py --lastmod (Get-Date -Format yyyy-MM-dd) --output-root .local\site
python ..\emulebb-tooling\helpers\pages-site-tools.py --pages-root .local\site validate
python ..\emulebb-tooling\helpers\check-tooling-doclinks.py --docs-root ..\emulebb-tooling\docs .local\site
$expected = (((Get-Content .local\site\install.ps1.sha256) -split '\s+')[0]).ToUpperInvariant()
$actual = (Get-FileHash -Algorithm SHA256 .local\site\install.ps1).Hash
if ($actual -ne $expected) { throw 'Stable installer checksum mismatch' }
git diff --check
```

`.github/workflows/pages.yml` performs the same contract, generated-output,
link, static-site, and installer checks. It uploads only the clean staged site
artifact. Pushes to `main` and manual dispatches may deploy; scheduled runs are
validation-only drift detection.

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
  if ($file -notmatch '\\rust\\index\.html$' -and $html -notmatch 'hreflang="x-default"') {
    throw "Missing x-default: $file"
  }
  if ($file -match '\\rust\\index\.html$' -and $html -match 'hreflang=') {
    throw "Rust redirect must not publish hreflang alternates: $file"
  }
  if ($file -match '\\rust\\index\.html$') {
    if ($html -notmatch 'content="noindex,follow"') { throw "Rust redirect is indexable: $file" }
  } elseif ($html -notmatch 'content="index,follow"') {
    throw "Locale not indexable: $file"
  }
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
- `rust/index.html`: no-index compatibility redirect to the homepage
- locale `index.html` files under the stock eMule language directories listed
  in the Localization Policy
- `languages/index.html`: indexable language selector
- `faq/index.html`: canonical English FAQ
- selected locale FAQ pages under `/it/faq/`, `/es/faq/`, `/pt-br/faq/`,
  `/pt-pt/faq/`, `/fr/faq/`, `/de/faq/`, `/pl/faq/`, `/nl/faq/`, `/ru/faq/`,
  `/tr/faq/`, `/uk/faq/`, `/ko/faq/`, `/ar-ae/faq/`, `/zh-cn/faq/`, and
  `/ja/faq/`
- `styles.css`: shared styles
- `assets/brand/emulebb-favicon.ico`: browser favicon
- `robots.txt`: crawler policy
- `sitemap.xml`: indexable URL list
- `AGENTS.md`: short agent policy
- `docs/SITE-HANDBOOK.md`: this handbook
