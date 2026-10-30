# eMuleBB organization website

This repository publishes the organization GitHub Pages site. The public front
door presents CI-gated `emulebb-rust` nightly builds as the primary active-beta
testing channel and eMuleBB MFC `0.7.x` as the maintained Windows line. Beta 3
is expected after a few more weeks of implementation and stabilization. Rust
development is best-effort, and contributors are welcome.

The homepage is the single canonical product page. `/rust/` is retained only as
a no-index compatibility redirect. Only the homepage and FAQ have localized
variants. Localized copy is deliberately minimal and evergreen: it does not
carry versions, beta targets, ETAs, or release-cycle status.

The public site is expected to publish at:

<https://emulebb.github.io/>

## Static Page Production

Generated HTML remains committed as a drift check and branch-publishing
fallback, but source edits go through the Jinja2 renderer and the shared
`emulebb-tooling\manifests\public-presence.v1.json` contract:

```powershell
python -m pip install -r requirements.txt
python ..\emulebb-tooling\helpers\public-presence.py validate
$lastmod = Get-Date -Format yyyy-MM-dd
python tools\render_pages.py --lastmod $lastmod
python tools\render_pages.py --lastmod $lastmod --check
python tools\render_pages.py --lastmod $lastmod --output-root .local\site
```

Run the validation helper before publishing:

```powershell
python ..\emulebb-tooling\helpers\pages-site-tools.py --pages-root .local\site validate
python ..\emulebb-tooling\helpers\check-tooling-doclinks.py --docs-root ..\emulebb-tooling\docs .local\site
```

`.github/workflows/pages.yml` repeats these checks, verifies
`install.ps1.sha256`, uploads only `.local/site`, and deploys through GitHub
Pages Actions on `main`. Scheduled runs validate contract drift without
publishing.

## Markdown Documentation Publishing

Long-form product docs are maintained as Markdown in `emulebb-tooling` and
published as rendered HTML at:

<https://emulebb.github.io/emulebb-tooling/>

Before changing homepage claims, update and validate the source docs. Lifecycle
and direction facts come from `docs/active/PRODUCT-DIRECTION.md`; Rust scope and
active work remain under `docs/products/emulebb-rust/`. Release facts remain
owned by the corresponding product repository:

```powershell
cd ..\emulebb-tooling
python scripts\docs-publish-check.py
```

Then return here, update the structured homepage source, regenerate the static
HTML, and run the Pages validation commands above.
