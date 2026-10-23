# CT-200 Approach Document

## 1. Scope and observed document structure

The two supplied PDFs are treated as engineering/regulatory source documents, not as clean Markdown. Their visible structure includes numbered headings, Markdown-like heading marks in extracted text, paragraphs, lists, tables, and formatting inconsistencies. The extraction review found:

- `3.4` appears before `3.3`, so source order must be retained while parentage comes from numbering.
- `2.1 General Specifications` is formatted differently from other headings.
- `2.1.1.1` is nested under `2.1` despite skipping intermediate numbers.
- `1.3` appears twice under the same parent in the source material; duplicate headings cannot be used as IDs.
- A standalone `-` follows the classification list.
- Some paragraphs wrap across PDF lines and one v1 paragraph is split around a page/text extraction boundary.
- v1 contains E6 and CSV export content that v2 removes.
- v1 and v2 change safety-relevant values, including inflation increment, battery threshold, battery life, and E3 timing.

## 2. OCR and extraction approach

The implementation uses `pypdf` for text-layer extraction because the supplied manuals contain a usable text layer. The parser is isolated behind `extract_pdf()`. If extraction fails, ingestion stops loudly instead of silently storing a partial tree. The production extension point is OCRmyPDF/Tesseract preprocessing, followed by the same normalization/parser contract. Page coordinates and OCR confidence should be added before regulatory use.

The parser recognizes numeric heading prefixes such as `1`, `1.1`, and `2.1.1.1`; it does not trust boldness, hash count, or exact spacing. Non-heading lines accumulate as body text. Tables remain textual in this starter version; a production parser would emit table blocks with page/row provenance.

## 3. Hierarchy reconstruction

A stack holds the most recent node at each level. A new heading pops nodes at the same or deeper level, then attaches to the nearest shallower node. The numeric depth determines level, so out-of-order siblings such as 3.4 then 3.3 remain siblings. A skipped numeric depth such as 2.1.1.1 is retained as a child at depth four rather than invented intermediate nodes.

Flattened logical keys contain the parent path, sibling ordinal, and heading. The ordinal is deliberate: duplicate headings become separate logical nodes and separate database IDs.

## 4. Versioning and matching

Each ingestion creates an immutable `DocumentVersion`. Nodes are never deleted from earlier versions. The matching key is a normalized structural path plus sibling ordinal and heading. The content hash is SHA-256 over normalized heading and body text. A node is semantically unchanged only when its matching key remains stable and its hash is unchanged.

This is intentionally explainable rather than fuzzy. It breaks when sections are reordered, renumbered, or split/merged. A production version would add a candidate matcher using heading similarity, parent similarity, and body similarity, but would require an ambiguity queue rather than silently choosing.

## 5. API and persistence

SQLite/SQLAlchemy stores documents, immutable versions, nodes, selections, selection items, and generation metadata. Selections store node ID, version ID, and content hash, so they always resolve to the exact source snapshot. A JSON generation payload stores the generated cases and input snapshot; this is the justified local NoSQL store for the assignment and can be replaced by MongoDB without changing the API contract.

Implemented routes include:

- `POST /documents/ingest`
- `GET /documents/sections`
- `GET /nodes/{id}`
- `GET /search`
- `GET /nodes/{id}/compare`
- `POST /selections`
- `POST /generations`
- `GET /generations/{id}` and `GET /generations`

## 6. LLM prompt and malformed-output policy

The included generator is deterministic so the repository runs without credentials. The provider boundary is `app/generator.py`. An LLM adapter should instruct the model to return only JSON matching: 3–5 test cases, each with title, preconditions, steps, expected result, severity, and source node IDs. Responses must pass Pydantic validation before persistence. On malformed JSON or incomplete fields, retry once with the validation error and original source text; if the second attempt fails, persist a failed generation record and return a clear 502 rather than storing invented or partial QA cases.

Repeated identical submissions are idempotent by `(selection snapshot, prompt version)`. A deliberate prompt-version change creates a new generation even for the same selection.

## 7. Staleness and impact detection

At retrieval time, the system compares every pinned selection hash with the latest matching logical node. It returns `stale=true` plus node-level reasons and a unified diff for direct node comparison. This catches any text change, including a one-word wording change. It does not determine semantic risk: changing a pressure threshold and changing punctuation both appear as changed. A production enhancement would classify diffs by safety-critical fields and route high-impact changes for review.

## 8. Validation methodology

Validation combines manual PDF inspection, parser unit tests, API smoke tests, v1/v2 comparison, and an end-to-end demo. The three explicit parser tests cover duplicate headings, out-of-order numbering, and stray/unformatted body fragments. The most important additional validation is fixture-based: assert that v1-only E6/CSV nodes disappear in v2, that changed values produce different hashes, and that a generation created from v1 is stale after v2 ingestion.

## 9. Decision log

### 1. Most likely silent failure

The highest-risk silent failure is incorrect parent assignment when numbering and visual formatting disagree. I would catch it with a structural validation report: headings whose numeric prefix conflicts with inferred depth, skipped levels, duplicate sibling titles, orphan body text, and a page-by-page visual/text comparison. The parser should fail review, not quietly publish a clean-looking tree.

### 2. Simplicity over correctness

I chose a deterministic path-plus-ordinal matcher and textual table retention rather than implementing fuzzy semantic matching and table geometry in the time available. Production would first break on section renumbering or split/merged sections, and table cells would lose machine-readable structure.

### 3. Unsupported input

I do not fully handle scanned PDFs with no text layer, rotated multi-column pages, or OCR confidence below an acceptance threshold. The current behavior is to stop ingestion with an explicit extraction error rather than save a partial hierarchy. The next step is OCR preprocessing plus confidence/page evidence in the node model.

## 10. What the initial implementation failed to handle

A naive heading parser based only on Markdown `#` markers would miss headings with inconsistent formatting, mis-parent `3.4`/`3.3`, collapse duplicate titles, and treat `2.1.1.1` as malformed. A naive version diff based only on heading text would miss body-only safety changes. These failures motivated numeric-depth parsing, ordinal-aware logical keys, immutable versions, and content hashes.

## 11. With more time

Add OCRmyPDF/Tesseract, page/box provenance, table extraction, an ambiguity review endpoint, migration scripts, provider adapters with retry telemetry, richer semantic impact classification, and a full integration test that asserts every known v1/v2 change.
