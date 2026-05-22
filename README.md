# eMule broadband edition website

This repository publishes the organization GitHub Pages site for eMule
broadband edition, code name `emulebb`.

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
python ..\eMule-tooling\helpers\pages-site-tools.py --pages-root . validate
```

## Markdown Documentation Publishing

Long-form product docs are maintained as Markdown in `eMule-tooling` and
published as rendered HTML at:

<https://emulebb.github.io/eMule-tooling/>

Before changing homepage claims, update and validate the source docs:

```powershell
cd ..\eMule-tooling
python scripts\docs-publish-check.py
```

Then return here, update the structured homepage source, regenerate the static
HTML, and run the Pages validation commands above.
