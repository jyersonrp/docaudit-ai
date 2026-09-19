# 🛡️ DocAudit AI: Asynchronous Document Audit & Extraction Engine

[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.13-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Pytest-66%20Passed-4EBA6F?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com)


**DocAudit AI** is a production-grade, asynchronous document intelligence system designed to audit, extract, and quantify operational risk in complex unstructured documents (master services agreements, enterprise software licenses, and 10-K/quarterly financial filings).

Built for enterprise reliability, DocAudit AI combines **Pydantic v2 strict schemas**, a **pluggable Multi-Provider LLM Factory** (Google Gemini 2.5 Flash, OpenAI GPT-4o, Ollama Llama 3, and an offline heuristic fallback engine), **hybrid vector/lexical retrieval with exact page citations**, and **publication-grade multi-format executive reporting** (Executive PDF, Markdown, and JSON).

---

## 🏛️ System Architecture

```
                                  +-----------------------------+
                                  |    DocAudit Web Dashboard   |
                                  |  (React 18 + Tailwind CSS)  |
                                  +--------------+--------------+
                                                 |
                                     REST / RAG Query / WebSocket
                                                 |
                                                 v
+------------------------------------------------------------------------------------------------+
|                                    FASTAPI BACKEND GATEWAY                                     |
|                                                                                                |
|  [ /api/v1/documents ]        [ /api/v1/audit ]        [ /api/v1/chat ]       [ /api/v1/export ]|
+----------------------------------------+-------------------------------------------------------+
                                         |
                       Async Background Task Orchestration
                                         |
                                         v
+------------------------------------------------------------------------------------------------+
|                               ASYNCHRONOUS DOCUMENT PIPELINE                                   |
|                                                                                                |
|   1. INGESTION & PARSING          2. SEMANTIC CHUNKING             3. VECTOR & HYBRID INDEX    |
|   +--------------------------+    +---------------------------+    +-------------------------+ |
|   | PyPDF / Python-Docx      | -> | Clause & Section Aware    | -> | SQLite Local Store      | |
|   | Page-level extraction    |    | Character-boundary window |    | BM25 + Cosine TF-IDF    | |
|   +--------------------------+    +---------------------------+    +-------------------------+ |
|                                                                                                |
|   4. MULTI-PROVIDER AI FACTORY    5. PYDANTIC V2 VALIDATION       6. REPORT GENERATOR        |
|   +--------------------------+    +---------------------------+    +-------------------------+ |
|   | Google Gemini 2.5 Flash  |    | Legal Contract Audit      |    | ReportLab Native PDF    | |
|   | OpenAI GPT-4o Mini       | -> | Financial Statements      | -> | Executive Markdown      | |
|   | Ollama Local (Llama 3)   |    | Custom Criteria Schemas   |    | Structured JSON Schema  | |
|   | Heuristic Fallback Engine|    | Strict Type Invariants    |    +-------------------------+ |
|   +--------------------------+    +---------------------------+                                |
+------------------------------------------------------------------------------------------------+
```

---

## 🌟 Key Technical Highlights & Engineering Decisions

### 1. Multi-Provider LLM Factory Pattern
- **Decoupled Provider Architecture**: Implements a clean `BaseLLMProvider` abstraction allowing seamless runtime switching between:
  - **Google Gemini** (`gemini-2.5-flash`) via the modern `google-genai` SDK with native JSON schema enforcement and asynchronous streaming inference.
  - **OpenAI** (`gpt-4o-mini`) using beta chat completions structured parsing.
  - **Ollama** (`llama3`) for zero-data-leakage on-premises private deployments.
  - **Deterministic Heuristic Engine**: Built-in fallback that runs 100% locally and offline without external API keys or network latency, ensuring the entire test suite and UI are immediately verifiable out-of-the-box.
- **Provider Status Discovery**: API endpoint `/api/v1/audit/providers` dynamically reports availability and defaults based on configured credentials.

### 2. Strict Schema Validation with Pydantic v2
- Audit outputs are validated against rich domain models:
  - **Legal Contracts**: Parties, Governing Law, Jurisdiction, Term, Bilateral/Unilateral Termination Notice, Liability Caps, Indemnification Breadth, Restrictive Covenants, Risk Matrix, and Regulatory Checklist.
  - **Financial Filings**: Revenue Breakdown, Operating Margins, Net Income, Auditor Opinions (Unqualified, Qualified, Adverse), Contingent Liabilities, Debt-to-Equity Covenants, and Tax Exposures.
  - **Custom Audits**: Dynamic key-value extraction against custom natural-language audit prompts.

### 3. Dual-Mode Vector Storage & Hybrid Retrieval
- **Local SQLite Vector Store**: Zero-dependency embedded vector engine computing TF-IDF cosine similarity and lexical keyword ranking. Chunks are persisted alongside page numbers and section headers.
- **Postgres pgvector Ready**: Fully configured Docker Compose service with PostgreSQL 16 and `pgvector` for enterprise scale.

### 4. Interactive RAG with Precise Grounding Citations
- User questions trigger hybrid retrieval over the document index.
- LLM synthesizes responses accompanied by structured `Citation` badges with **exact page numbers**, **relevance scores**, and **verbatim snippet previews**.

### 5. Multi-Format Publication-Grade Export
- **Executive PDF**: Built with `reportlab` using a tailored typography scale, color-coded risk tier badges, structured matrix tables, and actionable remediation callouts.
- **Markdown**: Formatted executive brief with tables and checklists ready for corporate wikis.
- **JSON**: Raw structured payload for integration into downstream ERP and CLM pipelines.

---

## 🚀 Quickstart Guide

### Option A: Immediate Local Run (No Docker Required)

Requires **Python 3.12+** and **Node.js 20+**.

#### 1. Backend Setup
```bash
# Clone the repository
cd docaudit-ai

# Activate virtual environment
.\.venv\Scripts\Activate.ps1   # On Windows
# source .venv/bin/activate     # On Linux/macOS

# Install backend dependencies
pip install -r backend/requirements.txt

# Run backend API server
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```
API will be live at `http://localhost:8000` (Swagger docs at `http://localhost:8000/api/v1/docs`).

#### 2. Frontend Setup
```bash
cd frontend

# Install node dependencies
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:5173` in your browser to access the dashboard.

---

### Option B: Production Docker Compose

Run the entire stack (FastAPI Backend + React Frontend + PostgreSQL 16 pgvector + Redis 7):

```bash
docker-compose up --build
```

- **Frontend Dashboard**: `http://localhost:5173`
- **FastAPI Backend**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/api/v1/docs`
- **PostgreSQL pgvector**: `localhost:5432`
- **Redis Queue**: `localhost:6379`

---

### Option C: 🌐 Deploy to Vercel & Render in 5 Minutes (100% Free)

Deploy a live, production-grade cloud instance with **0 hosting costs** to share on your **CV, Portfolio, and LinkedIn**.

- **Backend API**: Hosted on **Render.com** (Free Web Service tier, native Python 3.12, automated health checks)
- **Frontend Dashboard**: Hosted on **Vercel** (Free Hobby tier, fast global edge CDN, automatic SPA rewrites)
- **Zero Cost & Zero Key Barrier**: Operates 100% free with the built-in deterministic heuristic fallback engine, or optionally connect your Google Gemini / OpenAI API keys for live LLM inference.

```
                           +-------------------------------------+
                           |            USER BROWSER             |
                           +-------------------+-----------------+
                                               |
                          HTTPS / SPA Routes   |   REST / RAG API
                                               v
                        +----------------------+----------------------+
                        |                                             |
                        v                                             v
         +-----------------------------+               +-----------------------------+
         |     VERCEL (EDGE CDN)       |               |    RENDER.COM (WEB SERVICE) |
         |   React 18 Dashboard SPA    | ------------> |    FastAPI Python 3.12      |
         |   Rewrite rules enabled     |  CORS Origin  |    Healthcheck: /health     |
         |  https://<app>.vercel.app   |    Allowed    |  https://<api>.onrender.com |
         +-----------------------------+               +-----------------------------+
```

#### Step 1: Deploy Backend to Render (Free Web Service)

1. Push your repository to your GitHub account:
   ```bash
   git add .
   git commit -m "feat: ci/cd pipeline and cloud deployment readiness"
   git push origin master
   ```
2. Sign in to [Render.com](https://render.com) (free account, no credit card required).
3. From the dashboard, click **New +** > **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically detect [`render.yaml`](file:///render.yaml) and pre-configure the service:
   - **Name**: `docaudit-backend`
   - **Environment**: Python 3.12
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
   - **Plan**: `free`
6. *(Optional)* To enable live Google Gemini or OpenAI LLMs, add your `GEMINI_API_KEY` or `OPENAI_API_KEY` in the Environment Variables table. If left blank, DocAudit AI uses its deterministic heuristic fallback engine out-of-the-box.
7. Click **Apply**. Render will build and deploy the web service in ~2 minutes.
8. Copy your live backend URL (e.g., `https://docaudit-backend.onrender.com`).
   - Confirm it is online by visiting `https://docaudit-backend.onrender.com/health` in your browser.

#### Step 2: Deploy Frontend to Vercel (Free Edge CDN)

1. Sign in to [Vercel.com](https://vercel.com) (free account).
2. Click **Add New...** > **Project**.
3. Import your GitHub repository.
4. Configure your project settings:
   - **Framework Preset**: Vite
   - **Root Directory**: Click *Edit* and select `frontend`
5. Expand **Environment Variables** and add:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://docaudit-backend.onrender.com` *(paste your live Render backend URL from Step 1 without trailing slash)*
6. Click **Deploy**.
7. In ~45 seconds, your frontend will be live at `https://your-project.vercel.app`!

#### Step 3: Test & Verify Live Deployment

1. Open your live Vercel URL in your browser.
2. Verify the status indicator shows **System Online** with health status 200.
3. Click **Load Sample Legal Contract** or **Load Financial Statement** for instant zero-key auditing.
4. Ask questions in the interactive RAG Chat with page-level citations.
5. Download publication-grade executive **PDF**, **Markdown**, and **JSON** reports directly from the live web UI.

#### 💼 Showcase on Your CV & LinkedIn

Paste these links directly into your resume bullet points and LinkedIn Featured Projects section:
- **Live Interactive Demo**: `https://your-project.vercel.app`
- **Interactive OpenAPI / Swagger Documentation**: `https://your-backend.onrender.com/api/v1/docs`
- **GitHub Repository**: `https://github.com/your-username/docaudit-ai`

---


## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Healthcheck and active AI provider info |
| `POST` | `/api/v1/documents/upload` | Upload PDF/DOCX file and trigger async audit pipeline |
| `POST` | `/api/v1/documents/sample` | Instant 1-click sample document creation (`legal` or `financial`) |
| `GET` | `/api/v1/documents` | List all processed documents with status and metadata |
| `GET` | `/api/v1/documents/{doc_id}` | Get document processing status and progress (0-100%) |
| `DELETE` | `/api/v1/documents/{doc_id}` | Delete document, index chunks, and stored audit results |
| `GET` | `/api/v1/audit/{doc_id}/result` | Retrieve structured Pydantic v2 audit findings |
| `GET` | `/api/v1/audit/providers` | List configured AI providers and availability |
| `POST` | `/api/v1/chat/query` | Interactive RAG question answering with page citations |
| `GET` | `/api/v1/export/{doc_id}/pdf` | Download publication-grade executive PDF report |
| `GET` | `/api/v1/export/{doc_id}/markdown` | Download formatted Markdown report |
| `GET` | `/api/v1/export/{doc_id}/json` | Download raw structured JSON data |

### Example cURL Queries

#### 1. Generate Sample Legal Contract Audit
```bash
curl -X POST "http://localhost:8000/api/v1/documents/sample?sample_type=legal"
```

#### 2. Query Document with RAG & Citations
```bash
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "<DOC_ID>",
    "question": "What is the liability cap under this agreement?",
    "top_k": 3
  }'
```

#### 3. Download Executive PDF Report
```bash
curl -O -J "http://localhost:8000/api/v1/export/<DOC_ID>/pdf"
```

---

## ⚙️ Automated CI/CD Pipeline

Every `push` and `pull_request` targeting `main` or `master` triggers our GitHub Actions CI pipeline ([`.github/workflows/ci.yml`](file:///.github/workflows/ci.yml)):

- **Backend Quality & Tests (`backend-checks`)**:
  - Sets up Python 3.12 with pip cache acceleration.
  - Installs production dependencies and test harness.
  - Runs Flake8 static analysis enforcing zero critical syntax (`E9`) and undefined variable (`F63`, `F7`, `F82`) defects.
  - Executes the full 66-test Pytest suite with isolated mock fallback fixtures.
- **Frontend Build & Quality (`frontend-checks`)**:
  - Sets up Node.js 20.x with npm dependency caching.
  - Performs clean installation via `npm ci`.
  - Executes `npm run build` validating production Vite asset bundling and zero JSX/syntax errors.

---

## 🧪 Automated Test Suite

The test suite covers unit extraction (PDF, Word DOCX, corrupted formats), semantic chunking with clause boundary detection, local vector store SQLite operations, multi-provider factory fallbacks, Ollama integration, security hardening (magic bytes, path traversal, XML injection), CORS preflight & Vercel domain regex matching, and full end-to-end FastAPI endpoint workflows.

```bash
# Run pytest with verbose reporting
pytest -v
```

### Test Summary
- `test_ai_providers.py`: MockProvider heuristic extraction, schema compliance, LLMFactory auto-resolution.
- `test_api_endpoints.py`: End-to-end pipeline execution, sample seeding, RAG query with citations, multi-format exports, and CORS preflight / production origin verification.
- `test_chunker.py`: Semantic paragraph and section heading detection with token windows.
- `test_extractor.py`: PDF rendering & parsing, DOCX tables & paragraph extraction, format validation.
- `test_ollama_provider.py`: Ollama HTTP client integration, custom schemas, retry logic, timeout resilience, and streaming.
- `test_report_generator.py`: PDF binary generation, Markdown templating, JSON schema compliance.
- `test_security_and_optimizations.py`: Magic bytes validation, path traversal prevention, prompt injection mitigation, XML escaping, rate limiting, and in-memory LRU caching.
- `test_vector_store.py`: SQLite index creation, TF-IDF hybrid search, document-level isolation, and cascading deletion.

**Result: 66 passed, 0 failures, 100% green.**

---

## 📄 License
MIT License. Created by Jyers as a demonstration of production-grade AI systems engineering.
