# BharatLex Backend

This backend will handle MongoDB storage, legal document ingestion, RAG retrieval, and the multi-agent legal workflow.

## Current Step

This starter only verifies that:

- FastAPI starts
- `backend/.env` loads
- MongoDB Atlas can be reached
- legal PDFs can be previewed and ingested into MongoDB

## Environment

Create `backend/.env` from `.env.example`:

```env
MONGODB_URI=mongodb+srv://bharatlex_user:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=bharatlex
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

Put source PDFs here:

```txt
backend/legal_docs/
  Banking & Payments/
  Consumer Rights/
  Cyber Fraud/
  Insurance/
  Workplace Rights/
```

The PDFs are ignored by Git by default because they are local source data and can be large.

## Ingest Legal PDFs

Preview what will be read:

```bash
curl http://127.0.0.1:8000/api/ingest/legal-docs/preview
```

Write document and chunk records to MongoDB:

```bash
curl -X POST http://127.0.0.1:8000/api/ingest/legal-docs
```
