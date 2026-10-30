from __future__ import annotations

import csv
import hashlib
import io
import itertools
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from ..config import MAX_EXTRACTED_CHARS

MAX_SOURCE_BLOCKS = 5_000
MAX_CHUNK_CHARS = 1_800
CHUNK_OVERLAP_CHARS = 160
MAX_CLAIMS = 250


class DocumentProcessingError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SourceBlock:
    location: str
    text: str


@dataclass(frozen=True)
class TextChunk:
    location: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class CandidateClaim:
    location: str
    text: str
    sha256: str


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    blocks: list[SourceBlock]
    chunks: list[TextChunk]
    claims: list[CandidateClaim]
    page_count: int
    warning: str | None


def _decode_utf8(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentProcessingError("text_encoding_unsupported", "Document text must use UTF-8 encoding.") from exc


def _clean(text: str) -> str:
    return re.sub(r"[\t\u00a0 ]+", " ", text).strip()


def _flatten_json(value: object, path: str = "$", depth: int = 0) -> Iterator[SourceBlock]:
    if depth > 30:
        yield SourceBlock(path, "[nested value omitted: maximum JSON depth reached]")
    elif isinstance(value, dict):
        if not value:
            yield SourceBlock(path, "{}")
        for key, child in list(value.items())[:MAX_SOURCE_BLOCKS]:
            safe_key = str(key).replace("~", "~0").replace("/", "~1")[:120]
            yield from _flatten_json(child, f"{path}/{safe_key}", depth + 1)
    elif isinstance(value, list):
        if not value:
            yield SourceBlock(path, "[]")
        for index, child in enumerate(value[:MAX_SOURCE_BLOCKS]):
            yield from _flatten_json(child, f"{path}/{index}", depth + 1)
    else:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        if text.strip():
            yield SourceBlock(path, str(text))


def _read_text_blocks(data: bytes, suffix: str) -> tuple[list[SourceBlock], int, str | None]:
    text = _decode_utf8(data)
    if suffix == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DocumentProcessingError("invalid_json", "The JSON document could not be parsed.") from exc
        blocks = list(itertools.islice(_flatten_json(value), MAX_SOURCE_BLOCKS + 1))
        overflow = len(blocks) > MAX_SOURCE_BLOCKS
        warning = "Only the first 5,000 JSON scalar values were processed." if overflow else None
        return blocks[:MAX_SOURCE_BLOCKS], 0, warning
    if suffix == ".csv":
        try:
            rows = csv.reader(io.StringIO(text, newline=""))
            headers = next(rows, [])
        except (csv.Error, StopIteration) as exc:
            raise DocumentProcessingError("invalid_csv", "The CSV document could not be parsed.") from exc
        headers = [str(x).strip()[:160] or f"column_{i + 1}" for i, x in enumerate(headers)]
        blocks = []
        for row_number, row in enumerate(rows, start=2):
            fields = [f"{headers[i] if i < len(headers) else f'column_{i + 1}'}: {value.strip()}" for i, value in enumerate(row) if value.strip()]
            if fields:
                blocks.append(SourceBlock(f"row {row_number}", "; ".join(fields)))
            if len(blocks) >= MAX_SOURCE_BLOCKS:
                break
        warning = "Only the first 5,000 non-empty CSV rows were processed." if len(blocks) >= MAX_SOURCE_BLOCKS else None
        return blocks, 0, warning
    blocks = []
    overflow = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if len(blocks) >= MAX_SOURCE_BLOCKS:
            overflow = True
            break
        blocks.append(SourceBlock(f"line {line_number}", line.strip()))
    warning = "Only the first 5,000 non-empty text lines were processed." if overflow else None
    return blocks, 0, warning


def _read_pdf_blocks(data: bytes) -> tuple[list[SourceBlock], int, str | None]:
    try:
        import pymupdf
    except ImportError as exc:
        raise DocumentProcessingError("pdf_support_unavailable", "PDF processing dependency is unavailable; install the API requirements.") from exc
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise DocumentProcessingError("invalid_pdf", "The PDF file could not be opened.") from exc
    try:
        if document.needs_pass:
            raise DocumentProcessingError("encrypted_pdf", "Password-protected PDFs are not supported.")
        if document.page_count > MAX_SOURCE_BLOCKS:
            raise DocumentProcessingError("pdf_page_limit", "PDFs may contain at most 5,000 pages for extraction.")
        blocks = []
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")
            cleaned = _clean(text)
            if cleaned:
                blocks.append(SourceBlock(f"page {page_number}", cleaned))
        warning = None if blocks else "No embedded text was found. Scanned-image OCR is not enabled in this phase."
        return blocks, document.page_count, warning
    finally:
        document.close()


def _bounded_text(blocks: list[SourceBlock]) -> tuple[list[SourceBlock], str, str | None]:
    output: list[SourceBlock] = []
    pieces: list[str] = []
    remaining = MAX_EXTRACTED_CHARS
    truncated = False
    for block in blocks:
        text = _clean(block.text)
        if not text or remaining <= 0:
            if text:
                truncated = True
            continue
        prefix = f"[{block.location}] "
        available = max(0, remaining - len(prefix) - (2 if pieces else 0))
        if available <= 0:
            truncated = True
            continue
        if len(text) > available:
            text = text[:available]
            truncated = True
        output.append(SourceBlock(block.location, text))
        rendered = f"{prefix}{text}"
        pieces.append(rendered)
        remaining -= len(rendered) + (2 if len(pieces) > 1 else 0)
    warning = "Extracted text was capped at the configured maximum character count." if truncated else None
    return output, "\n\n".join(pieces), warning


def _split_block(block: SourceBlock) -> list[TextChunk]:
    text = block.text
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_CHARS, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + MAX_CHUNK_CHARS // 2, end)
            if boundary > start:
                end = boundary
        raw_piece = text[start:end]
        leading = len(raw_piece) - len(raw_piece.lstrip())
        piece = raw_piece.strip()
        if piece:
            actual_start = start + leading
            chunks.append(TextChunk(block.location, actual_start, actual_start + len(piece), piece))
        if end >= len(text):
            break
        start = max(start + 1, end - CHUNK_OVERLAP_CHARS)
    return chunks


CLAIM_SIGNAL = re.compile(r"\b(claim(?:s|ed)?|report(?:s|ed)?|estimate(?:s|d)?|credit(?:s|ed)?|issued|reduced|removed|avoided|baseline|methodolog(?:y|ies)|tco2e|co2e|tonnes?|tons?|hectares?|percent|%)\b", re.I)
CLAIM_VALUE = re.compile(r"(?:\d[\d,]*(?:\.\d+)?\s*(?:%|tco2e|co2e|tonnes?|tons?|hectares?|ha|kg)?|\b(?:19|20)\d{2}\b)", re.I)


def _candidate_claims(blocks: list[SourceBlock]) -> list[CandidateClaim]:
    found: list[CandidateClaim] = []
    seen: set[str] = set()
    for block in blocks:
        for sentence in re.split(r"(?<=[.!?])\s+|\s*\|\s*", block.text):
            sentence = _clean(sentence)
            if len(sentence) < 12 or not CLAIM_SIGNAL.search(sentence) or not CLAIM_VALUE.search(sentence):
                continue
            claim_text = sentence[:1_000]
            digest = hashlib.sha256(claim_text.casefold().encode("utf-8")).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            found.append(CandidateClaim(block.location, claim_text, digest))
            if len(found) >= MAX_CLAIMS:
                return found
    return found


def extract_document(filename: str, data: bytes) -> ExtractionResult:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".csv", ".json", ".txt"}:
        raise DocumentProcessingError("document_type_unsupported", "Extraction supports PDF, CSV, JSON, and plain text files.")
    if suffix == ".pdf":
        blocks, page_count, warning = _read_pdf_blocks(data)
    else:
        blocks, page_count, warning = _read_text_blocks(data, suffix)
    blocks, full_text, size_warning = _bounded_text(blocks)
    if warning and size_warning:
        warning = f"{warning} {size_warning}"
    else:
        warning = warning or size_warning
    chunks = [chunk for block in blocks for chunk in _split_block(block)]
    if len(chunks) > MAX_SOURCE_BLOCKS:
        chunks = chunks[:MAX_SOURCE_BLOCKS]
        warning = (warning + " " if warning else "") + "Chunk output was capped at 5,000 segments."
    claims = _candidate_claims(blocks)
    return ExtractionResult(full_text, blocks, chunks, claims, page_count, warning)
