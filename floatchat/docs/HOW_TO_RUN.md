# HOW_TO_RUN.md

Step-by-step guide to run backend, frontend, and ingestion.

# 1. Setup venv
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure Postgres
# Example DSN in .env:
POSTGRES_DSN=postgresql+psycopg://user:pass@localhost:5432/floatchat
CHROMA_PATH=./vectorstore

# 3. Ingest data
python app/ingest/ingest_nc.py --parquet --sql --embed

# 4. Start backend
uvicorn app.backend.main:app --reload --port 8000

# 5. Start frontend
streamlit run app/frontend/Home.py --server.port 8501

# 6. Test query
curl -X POST http://localhost:8000/rag/ask -H 'Content-Type: application/json' -d '{"query":"Show salinity near 0,0 in March 2023"}'