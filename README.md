# Integration Agent

Integration Agent is a local-first AI assistant that can connect to tools, index documents in a lightweight vector store (Chroma), and execute multi-step actions through a simple web UI. Think of it as a bridge between your data and your utilities: ingest files, search semantically, and trigger tool flows — all on your machine.

## What You Can Do
- Ingest local files and embed them into Chroma for fast semantic search.
- Ask the agent to find relevant context and execute tools (e.g., call APIs, run local scripts) using that context.
- Use the React UI to iterate on prompts and actions quickly.
- Keep everything on-device: your data remains in your environment.

## Features
- Local vector search via Chroma DB
- Agent orchestration for tool execution
- Simple React (Vite) frontend for interaction
- FastAPI backend (run locally)
- Docker Compose for provisioning the DB only

## Architecture
- `backend/` — Python FastAPI app and services
- `frontend/` — React + Vite single-page app
- `docker-compose.yml` — Provisioning for Chroma DB only (no backend/frontend containers)
- `backend/chroma_db/` — Local Chroma database files

## Prerequisites
- Docker and Docker Compose
- Node.js 18+ (if running the frontend locally without Docker)
- Python 3.11+ (if running the backend locally without Docker)

## Quick Start (Docker: DB only)
This project uses Docker Compose to provision the Chroma vector database. Backend and frontend are run locally.

1. Ensure Docker is running.
2. From the project root, start the DB:

```bash
docker compose up -d
```

Next, run backend and frontend locally (see below). Default local URLs:
- Backend API: `http://localhost:8000`
- Frontend app: `http://localhost:5173`

Tip: For persistence, the Chroma DB lives in `backend/chroma_db/`. Back up or snapshot this directory to save your embeddings.

## Running Locally (backend + frontend)

### Backend
```bash
# From project root
cd backend

# Create and activate a virtual environment (Windows bash)
python -m venv .venv
source .venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
# From project root
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

- Open http://localhost:5173
- The frontend will call the backend at http://localhost:8000 (adjust in `frontend/src/api.js` if needed)

## API Overview
Key files:
- `backend/app/api/routes.py` — Defines available endpoints
- `backend/app/main.py` — FastAPI app setup
- `backend/app/schemas.py` — Pydantic schemas

Common endpoints (indicative):
- `GET /health` — Health check
- `POST /agent/execute` — Execute a tool/action via the agent

Inspect `routes.py` for complete, up-to-date routes.

## Example Use Case
- You drop a set of CSVs and PDFs into a local directory.
- The backend indexes them into Chroma.
- In the UI, you ask: "Find invoice totals over $5,000 in Q3 and prepare an email to finance." The agent retrieves relevant chunks, composes a response, and—if a mail tool is configured—drafts a message.
- Extend this flow by adding custom tools in `backend/app/services/tool_registry.py` (e.g., Slack notifier, REST integrations).

## Project Structure
```
Integration Agent/
├─ docker-compose.yml
├─ backend/
│  ├─ requirements.txt
│  ├─ test_agent.py
│  ├─ test_db.py
│  └─ app/
│     ├─ main.py
│     ├─ schemas.py
│     ├─ api/routes.py
│     ├─ core/
│     │  ├─ agent.py
│     │  └─ database.py
│     └─ services/
│        ├─ mcp_bridge.py
│        ├─ security.py
│        └─ tool_registry.py
└─ frontend/
   ├─ package.json
   ├─ src/
   │  ├─ api.js
   │  ├─ App.jsx
   │  └─ main.jsx
   └─ public/
```

## Configuration
- Backend environment variables can be added via `.env` in `backend/` and loaded in `app/main.py` or `app/core/database.py` as needed.
- Frontend configuration lives in `frontend/vite.config.js` and `frontend/src/api.js`.


## Version Status
This is the first, basic version focused on local document search and simple tool orchestration. 
