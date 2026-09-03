# `web/` — the static story page

A single static page that leads with the analysis and keeps an interactive
explorer underneath it:

- **The story** — the seven figures from `figures/`, in narrative order, each
  with the reasoning behind it. These are plain `<img>` tags, so they render
  with no server and no JavaScript.
- **Explore the source data** — every series the project downloads, one chart
  per series, drawn with Plotly from the JSON in `web/data/`. This part needs
  `fetch()`, which browsers block on `file://` URLs.
- **Limitations** and **Sources**.

## Running it locally

Serve from the **repository root**, not from inside `web/`:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/web/>.

The root matters: the story figures are referenced as `../figures/*.png` so that
the repository keeps exactly one copy of each image. Serving `web/` as the root
puts those files outside the document root and every figure 404s. Opening
`index.html` straight off disk shows the figures but leaves the explorer empty,
and the page says so in a banner rather than failing silently.

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

## Deploying

Any static host works as long as the **repository root** is the document root,
so that both `web/` and `figures/` are reachable — GitHub Pages serving from the
repo root is the path of least resistance.

If you ever need to serve `web/` as its own root (some Spaces configurations do
this), copy `figures/` into `web/figures/` at build time and update the `src`
attributes to match. Nothing else in the page reaches outside `web/`.

## Files

| File | Purpose |
|---|---|
| `index.html` | Page structure and all prose |
| `styles.css` | Layout and the palette shared with `src/eda.py` |
| `main.js` | Loads the JSON bundles, renders one chart per card, drives the tabs |
| `data/*.json` | Generated — do not edit by hand |
