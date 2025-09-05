# PROJECT.md

High-level description of the FloatChat MVP, problem statement, and solution scope.


Title: FloatChat — AI Conversational Interface for ARGO (NetCDF) DataGoal: Enable natural‑language exploration of ARGO float data, backed by RAG pipelines and visual dashboards.

Scope (MVP):

Ingest local .nc files → structured tables (PostgreSQL) + Parquet.

Create vector store (Chroma) of per‑profile summaries/metadata for retrieval.

Backend (FastAPI) using MCP tools to call: sql.query, vector.search, files.read.

Streamlit frontend: chatbot + map (Leaflet) + depth‑time Plotly.

Queries supported (examples): salinity profiles near lat/lon + month; compare BGC params; nearest floats.

High‑level Architecture:

[NetCDF (.nc)] → [Ingestor (xarray)] → [Parquet] → [PostgreSQL]
                                    ↘→ [Chroma vectors]
Streamlit UI ⇄ FastAPI RAG API ⇄ (MCP tools: Postgres, Chroma, Files)


Data placement:

/data/raw/*.nc            # drop your NetCDF files here
/data/processed/*.parquet
/vectorstore/             # Chroma persistence