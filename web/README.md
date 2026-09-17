# `web/` — the static story page

A single static page that leads with the analysis and keeps an interactive
explorer underneath it. In page order:

- **The story** — six of the eight figures in `figures/`, as four reasons and a
  result, each with the reasoning behind it. They are interactive Plotly charts
  backed by the generated JSON, with the original PNGs kept as no-JavaScript
  fallbacks. The two decomposition figures (03 and 07) are methodology and stay
  in the top-level README; `tests/test_web_page.py` records why.
- **Four forces** — location, the housing market and rates, macro trends, and
  debt and savings, with the regional comparison of all 20 Case-Shiller metros
  under Location.
- **House hacking** and the **action plan** — what a buyer can do about it.
- **Explore the source data** — every national FRED series the project
  downloads plus the engineered measures, one chart each, drawn with Plotly from
  the JSON in `web/data/`. This part needs `fetch()`, which browsers block on
  `file://` URLs.
- **Limitations** and **Sources**.

## Running it locally

Serve from the **repository root**, not from inside `web/`:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/web/>.

The root matters: the fallback story figures are referenced as
`../figures/*.png` so that the repository keeps exactly one copy of each image.
Serving `web/` as the root puts those files outside the document root and every
fallback figure 404s.

Every interactive chart fetches `web/data/*.json`, and browsers block `fetch()`
on `file://` URLs. Opened straight from disk, or when the data fails to load for
any other reason, the page shows a notice with the command above, the story
swaps each chart for its PNG, and the regional chart and data explorer say the
data could not load.

## Regenerating the data

`web/data/*.json` is written by `src/export_for_web.py` from the CSVs in
`data/processed/`. It runs as the last step of the pipeline:

```bash
python src/run_all.py
```

or on its own:

```bash
python src/export_for_web.py
```

Run it as a **script path**, not as `python -m src.export_for_web` — `src/` has
no `__init__.py`, and the modules import their siblings directly (`from config
import ...`), which only resolves when Python puts the script's own directory on
`sys.path`.

The JSON duplicates `data/processed/*.csv` and is committed only so the page
works from a fresh clone. It is written with compact separators for that reason.

## Deploying with GitHub Pages

`.github/workflows/pages.yml` publishes the site whenever a change reaches
`main`. The workflow stages a deployment artifact rather than changing the
source layout:

1. The contents of `web/` become the root of the published site.
2. `figures/` is copied into the artifact for the no-JavaScript fallbacks.
3. The fallback paths in the staged `index.html` are changed from
   `../figures/` to `figures/`.

The rewrite happens only in the temporary artifact. Local development therefore
continues to use the repository-root server described above, while the deployed
site is available at:

<https://haydn-s.github.io/sourcing-data-project-1/>

To enable the first deployment, open the repository's **Settings → Pages** and
select **GitHub Actions** as the source. No Python runs during deployment: the
workflow serves the committed files in `web/data/`, so regenerate and commit
those files before publishing updated analysis.

## Files

| File | Purpose |
|---|---|
| `index.html` | Page structure and all prose |
| `styles.css` | Layout and the palette shared with `src/eda.py` |
| `main.js` | Loads the JSON bundles, renders one chart per card, drives the tabs |
| `data/*.json` | Generated — do not edit by hand |
