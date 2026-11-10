# eMuleBB organization website

The public front door for eMuleBB Rust gives equal space to using the client
and developing with its REST API. CI-gated nightly packages are the active-beta
testing channel; Beta 3 is the next development target.

**Contents:** [Read the site](#read-the-site) · [Maintain the source](#static-page-production) · [Validate and publish](#validation-and-publication)

## Read the site

- [Use eMuleBB Rust](https://emulebb.github.io/emulebb-tooling/products/emulebb-rust/reference/GUIDE-GETTING-STARTED/)
- [Choose a platform and package](https://emulebb.github.io/emulebb-tooling/products/emulebb-rust/reference/GUIDE-DOWNLOADS-PLATFORMS/)
- [Develop with the client](https://emulebb.github.io/emulebb-tooling/products/emulebb-rust/reference/GUIDE-CONTRIBUTING/)
- [Build against the REST API](https://emulebb.github.io/emulebb-tooling/products/emulebb-rust/api/GUIDE-API-CONSUMERS/)

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
python -B ..\emulebb-tooling\helpers\public-presence.py validate
$lastmod = Get-Date -Format yyyy-MM-dd
python -B tools\render_pages.py --lastmod $lastmod
python -B tools\render_pages.py --lastmod $lastmod --check
```

Run the validation helper before publishing:

```powershell
python -B ..\emulebb-tooling\helpers\pages-site-tools.py --pages-root . validate
python -B ..\emulebb-tooling\helpers\check-tooling-doclinks.py --docs-root ..\emulebb-tooling\docs .
```

## Validation and publication

The workspace manager probes `tools/render_pages.py --capabilities` and stages
the site in a fresh owned `OUTPUT/artifacts/public-presence/<run>/site`
directory. Explicit staging requires both `--output-root` and
`--workspace-output-root`; the latter must match the inherited output boundary.
Existing site directories and redirected paths are refused. Keep generated
scratch outside the checkout and leave inherited workspace variables unchanged.

The proposal-1 identity derivatives are supplied assets. Preserve their bytes,
dimensions and recorded SHA-256 values; do not regenerate them.

`.github/workflows/pages.yml` repeats the checks, verifies
`install.ps1.sha256`, uploads only the staged site, and deploys through GitHub
Pages Actions on `main`. Scheduled runs validate without publishing.

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
