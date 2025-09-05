# HOW_TO_CHECK.md

Guide for verifying each role's code independently.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Goal

Ensure each teammate can validate their work in isolation, without waiting for other roles to finish.


------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


Frontend (Streamlit UI)

What to check:

Run streamlit run app/frontend/Home.py

Use mock API responses (create mock_api.py returning dummy JSON)

Confirm: chat box, map, and charts render correctly with fake data.

Command:

streamlit run app/frontend/Home.py

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Data Manager (Ingestion & DB)

What to check:

Run ingestion script standalone.

Verify Parquet files exist in /data/processed/

Verify tables created in PostgreSQL (psql -d floatchat -c "\dt")

Commands:

python app/ingest/ingest_nc.py --parquet
python app/ingest/ingest_nc.py --sql

Expected:

.parquet files in data/processed/

Tables in PostgreSQL

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

AI / RAG Team

What to check:

Run retriever in isolation with dummy queries.

Mock Postgres + Chroma calls (use stub data).

Ensure ask() returns structured response: {sql, rows, context}.

Command:

python -m app.backend.rag.retriever "Show me salinity near 0,0 in March 2023"

Expected:

Console output with SQL + mock rows + context text.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Backend (FastAPI)

What to check:

Start API even without FE.

Test /rag/ask with curl or Postman.

Commands:

uvicorn app.backend.main:app --reload --port 8000

curl -X POST http://localhost:8000/rag/ask \
  -H 'Content-Type: application/json' \
  -d '{"query":"test"}'

Expected:

JSON response with {sql, rows, context} (even if rows are empty).

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

QA / Integration

What to check:

Run tools/check_progress.py to auto‑update TASKS.md.

Create tools/last_test.txt when test is successful.

Ensure MVP_LOCK is created only when all roles pass isolated tests.

Commands:

python tools/check_progress.py

Expected:

TASKS.md checkboxes updated.

Report shows progress by role.

✅ This way, each member can confirm their code works standalone, avoiding bottlenecks.