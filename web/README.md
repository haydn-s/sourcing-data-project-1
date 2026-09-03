This `web/` folder provides a static HTML viewer that loads JSON exports
from `web/data/` and renders interactive charts using Plotly.

How to host on Hugging Face Spaces (static):

- Ensure the repository is pushed to a Hugging Face Space (select a "Static" or
  "Gradio/Streamlit" runtime and point to this repo). The `web/` folder can be
  served as static files. Alternatively, create a simple Space that serves
  `web/index.html`.
- Run the exporter locally before pushing so `web/data/*.json` exists:

```bash
python -m src.export_for_web
```

Then push the repo to Hugging Face and the static `index.html` will be available.
