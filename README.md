# CT-200 QA Traceability API

A focused FastAPI implementation for the Tri9T AI internship assignment. It ingests the two CT-200 PDF manuals, reconstructs numbered hierarchy, versions the tree, pins selections to node/version/hash snapshots, generates validated QA ideas, and exposes retrieval-time staleness.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is documented at `http://localhost:8000/docs`.

## Ingest v1 → v2

```bash
curl -X POST 'http://localhost:8000/documents/ingest?path=data/ct200_manual_v1.pdf'
curl -X POST 'http://localhost:8000/documents/ingest?path=data/ct200_manual_v2.pdf'
curl 'http://localhost:8000/documents/sections'
```

Create a selection from node IDs returned by the browse endpoints, generate test cases, then retrieve the generation later. The retrieval response recalculates staleness against the latest version and returns reasons such as `node 12 content changed` or `node 14 is absent from latest version`.

## Tests

```bash
pytest -q
```

## Design notes

- Numbering is the primary hierarchy signal; Markdown/PDF typography is only a hint.
- Logical matching uses `(document, normalized numbered path, heading)` and content hashes. This preserves duplicate headings as separate nodes while matching semantically stable nodes across versions.
- Generated output is validated with Pydantic before persistence. The included deterministic adapter makes the repository runnable offline; a provider adapter may replace it but must keep the same validation boundary and retry malformed responses.
- Duplicate generation requests for the same selection snapshot and prompt version are idempotent.
- OCR fallback is intentionally explicit: if text extraction fails, the ingestion command returns an error rather than silently producing an incomplete tree. A production deployment should add OCRmyPDF/Tesseract as a preprocessing step and retain page/geometry evidence.
