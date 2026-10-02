# eMuleBB organization website

This repository publishes the organization GitHub Pages site. The public front
door presents `emulebb-rust` as the active experimental beta and eMuleBB MFC
`0.7.x` as the stable long-term maintenance line.

The public site is expected to publish at:

<https://emulebb.github.io/>

## Static Page Production

Generated HTML is committed for GitHub Pages, but source edits should go through
the Jinja2 renderer:

```powershell
python -m pip install -r requirements.txt
python tools\render_pages.py --lastmod 2026-05-16
python tools\render_pages.py --lastmod 2026-05-16 --check
```

Run the validation helper before publishing:

```powershell
python ..\emulebb-tooling\helpers\pages-site-tools.py --pages-root . validate
```

## Markdown Documentation Publishing

Long-form product docs are maintained as Markdown in `emulebb-tooling` and
published as rendered HTML at:

<https://emulebb.github.io/emulebb-tooling/>

Before changing homepage claims, update and validate the source docs. Lifecycle
and roadmap facts come from `PRODUCT-PORTFOLIO.md` and `ROADMAP-SUMMARY.md`;
release facts remain owned by the corresponding product repository:

```powershell
cd ..\emulebb-tooling
python scripts\docs-publish-check.py
```

Then return here, update the structured homepage source, regenerate the static
HTML, and run the Pages validation commands above.
