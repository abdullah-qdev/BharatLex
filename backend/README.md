# BharatLex Backend

This backend handles MongoDB storage, legal document ingestion, RAG retrieval, constrained Ollama agents, and Gemini final synthesis.

## Current Step

The backend currently supports:

- FastAPI starts
- `backend/.env` loads
- MongoDB Atlas can be reached
- legal PDFs can be previewed and ingested into MongoDB
- optional Ollama embeddings for RAG
- four evidence-bound Ollama debate agents
- Gemini synthesis of the full retrieved evidence and debate

## Environment

Create `backend/.env` from `.env.example`:

```env
MONGODB_URI=mongodb+srv://bharatlex_user:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=bharatlex
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=llama3.1
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_NUM_PREDICT=320
OLLAMA_TEMPERATURE=0.2
OLLAMA_DISABLE_THINKING=true
FINAL_SYNTHESIS_PROVIDER=groq
GROQ_API_KEY=YOUR_GROQ_KEY
GROQ_MODEL=llama-3.3-70b-versatile
RAG_TOP_K=6
RAG_MIN_SCORE=0.2
DEBATE_ROUNDS=2
```

## Run Locally

From `backend/`:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

```txt
http://127.0.0.1:8000/
http://127.0.0.1:8000/health/db
http://127.0.0.1:8000/api/ingest/legal-docs/preview
```

## Legal Docs

Source PDFs can live in either of these folders:

```txt
backend/legal_docs/
  Banking & Payments/
  Consumer Rights/
  Cyber Fraud/
  Insurance/
  Workplace Rights/

backend/statutes/
  Consumer Protection Act, 2019.pdf
  RBI Integrated Ombudsman Scheme.pdf
  ...
```

`backend/statutes/` is the current shared statute corpus from the prototype. `backend/legal_docs/` is still supported for locally added category folders.

## Ingest Legal PDFs

Preview what will be read:

```bash
curl http://127.0.0.1:8000/api/ingest/legal-docs/preview
```

Write document and chunk records to MongoDB:

```bash
curl -X POST http://127.0.0.1:8000/api/ingest/legal-docs
```

Write chunks and generate Ollama embeddings:

```bash
curl -X POST "http://127.0.0.1:8000/api/ingest/legal-docs?embed=true"
```

Before embedding, make sure Ollama is running locally and the embedding model exists:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1
ollama serve
```

## Ask RAG

```bash
curl -X POST http://127.0.0.1:8000/api/rag/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Where should I file this complaint and what is the deadline?\"}"
```

The response includes:

- retrieved PDF chunks with page numbers and extracted citation metadata
- all four Ollama agent responses
- Gemini's final workflow/conclusion

If no relevant document chunk is found, the API stops and returns `no_relevant_evidence` instead of guessing.

You can optionally pass a category to narrow retrieval to the relevant statutes:

```bash
curl -X POST http://127.0.0.1:8000/api/rag/ask \
  -H "Content-Type: application/json" \
  -d "{\"category\":\"consumer\",\"question\":\"An online seller took my money and will not refund. What can I do?\"}"
```

Available categories:

```txt
GET /api/rag/categories
```
