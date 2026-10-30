# Evidence Intelligence — Phase 2

This phase adds a local, authenticated extraction path for uploaded evidence. It does not send source files or extracted text to Nebius or another external service.

## Supported files and boundaries

- PDF: embedded text is extracted page by page with PyMuPDF. Scanned-image OCR is not enabled; image-only pages receive an explicit limitation warning.
- CSV: rows become source blocks with header/value pairs and one-based source row numbers.
- JSON: scalar values are flattened with JSON Pointer-style locations such as `$/project/claim`.
- TXT: non-empty lines retain one-based line numbers.
- Existing upload size control remains `MAX_UPLOAD_BYTES` (10 MB by default). Extraction output is capped by `MAX_EXTRACTED_CHARS` (500,000 by default), and blocks/chunks/claims are bounded in the extraction service.
- Upload checks compare the declared MIME type with the extension when the client supplies a specific type, check known binary signatures, validate UTF-8, and parse JSON before storing it.

Text extraction is best-effort. PDF text order may differ from natural reading order, and these deterministic parsers do not establish that a statement is true.

## Candidate claims and provenance

The first-pass claim finder is deterministic and heuristic. It selects source lines/rows/pages/JSON values containing a carbon/claim signal and a number or year. Each result is stored as `heuristic_candidate` with a low, non-calibrated `0.25` confidence and `candidate` status. It is not an AI conclusion, verification result, or certification. A reviewer must assess it before treating it as a finding.

Every candidate links to its evidence-file record and original server-calculated SHA-256 digest. Chunks also retain their source location, character offsets, content hash, and ordering. Full extracted text remains behind the authenticated evidence/project ownership boundary; APIs return a short preview or paginated chunks.

Identical content hashes may reuse extraction output only within the same project, so deduplication does not reveal another project's files. Reuse still creates evidence-specific chunks, claims, and provenance links.

## API

- `POST /api/evidence/{evidence_id}/extract` — extract and persist; safe to repeat for unchanged evidence.
- `GET /api/evidence/{evidence_id}/extraction` — status, limitations, preview, and candidate claims.
- `GET /api/evidence/{evidence_id}/extraction/chunks?offset=0&limit=50` — paginated source chunks.
- `GET /api/evidence/search?project_id=...&q=...` — authenticated case-insensitive lexical search across extracted chunks for one authorized project.

The API rejects files whose on-disk bytes no longer match the upload digest. It returns a clear error for unsupported extraction types, invalid files, encrypted PDFs, and missing PDF support. A parser failure after the file and hash are verified is persisted as failed and may be retried after correcting the underlying file/configuration issue.

Search is lexical substring search. PostgreSQL full-text search, pgvector, OCR, external web research, and AI-based claim extraction are later work; SQLite continues to support local development.

## Dependency reference

[PyMuPDF documentation](https://pymupdf.readthedocs.io/en/latest/recipes-text.html) describes page-level text extraction. The application uses it only for reading text from the original local PDF bytes.
