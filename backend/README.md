# AccountIQ — Backend

AI-powered accounting analysis backend.
**KTP Demo Project** — University of Essex × Active Software Platform UK Ltd

## Skills Demonstrated
- Generative AI (Ollama/LLaMA)
- Agentic AI (Junior Assist, Reviewer Assist, document generation)
- Explainable AI — fuzzy logic risk scoring with plain-English explanations
- NLP — entity extraction, transaction classification
- Information Fusion — heterogeneous financial data processing
- GDPR — full audit trail for every AI decision
- FastAPI backend + SQLite/PostgreSQL database
- REST API consumed by Flutter frontend

## Setup

### 1. Install Python dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install and start Ollama (local LLM — no API key needed)
```bash
# Install from https://ollama.com
ollama pull llama3.2
ollama serve
```

### 3. Run the backend
```bash
uvicorn main:app --reload --port 8000
```

### 4. View API docs
Open http://localhost:8000/docs in your browser.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/transactions` | GET | List all transactions |
| `/transactions` | POST | Add + auto-score a transaction |
| `/transactions/analyse-all` | POST | Score all unanalysed transactions |
| `/transactions/stats` | GET | Dashboard statistics |
| `/agents/junior-assist/{id}` | POST | AI categorise one transaction |
| `/agents/reviewer-assist` | POST | Batch anomaly review |
| `/agents/generate-letter` | POST | Generate client letter |
| `/agents/generate-anomaly-report` | POST | Generate anomaly report |
| `/agents/audit-log` | GET | GDPR audit trail |

## Architecture

```
Financial Data (CSV/API)
        │
   NLP Engine (spaCy)
        │
Fuzzy Logic + XAI Engine   ← Prof Hagras's specialism
        │
   ┌────┴────┐────────────┐
Junior    Reviewer    Generative
Assist    Assist      AI
        │
   FastAPI REST API
        │
   Flutter Frontend
```
