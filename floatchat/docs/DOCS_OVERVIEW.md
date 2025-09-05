# DOCS_OVERVIEW.md

Index explaining the purpose of each document.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Purpose

This document explains the role of each file in /docs so new contributors can quickly understand what to read and why.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#PROJECT.md

High‑level description of the project.

States the problem, solution approach, and MVP scope.

First doc every new contributor should read.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#TASKS.md

Role‑based checklist of tasks.

Automatically updated by tools/check_progress.py.

Source of truth for tracking progress.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#TECH_STACK.md

Lists all technologies, dependencies, and versions.

Includes pinned requirements.txt.

Ensures the whole team uses the same setup.
Goal

Ensure each teammate can validate their work in isolation, without waiting for other roles to finish.

Frontend (Streamlit UI)

What to check:

Run streamlit run app/frontend/Home.py

Use mock API responses (create mock_api.py returning dummy JSON)

Confirm: chat box, map, and charts render correctly with fake data.

Command:

streamlit run app/frontend/Home.py

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

AI / RAG Team

What to check:

Run retriever in isolation with dummy queries.

Mock Postgres + Chroma calls (use stub data).

Ensure ask() returns structured response: {sql, rows, context}.

Command:

python -m app.backend.rag.retriever "Show me salinity near 0,0 in March 2023"

Expected:

Console output with SQL + mock rows + context text.

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
#RULES.md

Hard rules for Cursor prompts and coding.

Defines non‑negotiable constraints (stack, structure, observability, etc.).

Used to prevent accidental scope creep.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#TEAM_GUIDE.md

Explains team roles and responsibilities.

Helps each member know what they own.

Outlines parallel workflow strategy.

#HOW_TO_RUN.md

Step‑by‑step instructions to run the app locally.

Includes venv setup, DB config, ingestion, backend, and frontend startup.

QA team uses this for end‑to‑end testing.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#HOW_TO_CHECK.md

Explains how each role can validate their code independently.

Provides commands and expected outputs for unit‑level verification.

Ensures members don’t block each other.

#DOCS_OVERVIEW.md (this file)

Explains the purpose of all other docs.

Serves as an index for onboarding new contributors.

✅ With this, every teammate knows where to look and why each doc exists.