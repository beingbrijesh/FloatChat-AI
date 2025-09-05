# TEAM_GUIDE.md

Roles, responsibilities, and collaboration strategy.

-------------- Roles & Responsibilities ----------------------------------------------

-------------- Frontend (Streamlit UI) -----------------------------------------------

Build chat UI, map, depth‑time plots.

Ensure layout is responsive.

Call only /rag/ask backend endpoint.

-------------- Data Manager -----------------------------------------------------------

Own ingestion pipeline (ingest_nc.py).

Maintain schema.sql.

Ensure .nc → Parquet + Postgres + vectors is smooth.

-------------- AI / RAG Team ----------------------------------------------------------

Build retriever.py, mcp_tools.py, prompts.py.

Translate queries → SQL using MCP LLM.

Return {sql, rows, context} consistently.

-------------- Backend / API ----------------------------------------------------------

Own FastAPI app (main.py, router.py).

Integrate .env configs.

Add logging/observability.

Keep interface stable.

-------------- QA / Integration --------------------------------------------------------

Use tools/check_progress.py for auto‑tracking.

Validate MVP queries (salinity near equator, BGC compare, nearest floats).

Confirm FE + BE + data works end‑to‑end.

-------------- Parallel Workflow -------------------------------------------------------

Teams work independently using stubs.

FE can mock API responses.

AI team can mock SQL results.

Data can ingest .nc before AI is ready.

QA locks MVP once all roles complete.