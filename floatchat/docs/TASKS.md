# TASKS.md

Role-based step checklist with auto-ticking support.


# Build Checklist (by Role)

## Frontend (Streamlit UI Team)
- [ ] FE1: Setup venv & install deps
- [ ] FE2: Implement chat interface (chat.py)
- [ ] FE3: Implement map component (map.py)
- [ ] FE4: Implement depth‑time charts (charts.py)
- [ ] FE5: Layout dashboard (Home.py)
- [ ] FE6: Connect UI to backend `/rag/ask`

## Data Manager (Ingestion & DB Team)
- [ ] DM1: Place .nc files in /data/raw
- [ ] DM2: Implement to_rows() in ingest_nc.py
- [ ] DM3: Run ingestion → Parquet (/data/processed)
- [ ] DM4: Load data into PostgreSQL
- [ ] DM5: Generate embeddings → Chroma vectorstore
- [ ] DM6: Maintain schema.sql & validate sample queries

## AI / RAG Team
- [ ] AI1: Implement vector_search() in mcp_tools.py
- [ ] AI2: Wire sql_query() to PostgreSQL (MCP)
- [ ] AI3: Implement prompt builder in prompts.py
- [ ] AI4: Implement ask() pipeline in retriever.py
- [ ] AI5: Ensure responses = {sql, rows, context}
- [ ] AI6: Provide fallback query for demo

## Backend / API Team
- [ ] BE1: Finalize FastAPI main.py & rag/router.py
- [ ] BE2: Integrate .env config (DSN, Chroma path)
- [ ] BE3: Add observability (log SQL + vector hits)
- [ ] BE4: Keep API stable for FE integration

## QA / Integration
- [ ] QA1: Run tools/check_progress.py
- [ ] QA2: Test sample queries end‑to‑end
- [ ] QA3: Verify outputs (SQL, rows, map, plots)
- [ ] QA4: Create MVP_LOCK when stable