# RULES.md

Hard rules for Cursor prompts and coding.

Do not change tech stack: Streamlit + FastAPI + PostgreSQL + Chroma + xarray/netCDF4 + Plotly/Leaflet.

Keep files small & modular; never mix UI and data logic.

Paths fixed: .nc → data/raw/; Parquet to data/processed/; vectors to ./vectorstore/.

API contract stable: only POST /rag/ask {query}.

SQL safety: Read‑only queries only.

Reproducibility: All scripts runnable as python script.py --help using .env.

Observability: Print SQL + top vector hits in API response.

Secrets in .env, never in code.

Type hints & docstrings required in backend.

At least one happy‑path unit test per new function.