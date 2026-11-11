"""Small, local retrieval layer for grounding ORACLE explanations in source."""

from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}")
SECRET_LINE = re.compile(
    r"(?i)(\b(?:api[_-]?key|client[_-]?secret|password|(?:access|refresh)?[_-]?token|secret|credential|authorization)\b\s*[:=]\s*)(.+)$"
)
PEM_LINE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|-----END [A-Z ]*PRIVATE KEY-----")
TOKEN_VALUE = re.compile(r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})\b")


def redact_source(source: str) -> str:
    """Redact common credential assignments before any text can reach an LLM."""
    safe_lines = []
    inside_private_key = False
    for line in source.splitlines():
        if PEM_LINE.search(line):
            inside_private_key = "BEGIN" in line
            safe_lines.append("[redacted private key]")
            continue
        if inside_private_key:
            if "END " in line:
                inside_private_key = False
            safe_lines.append("[redacted private key]")
            continue
        match = SECRET_LINE.search(line)
        safe_line = f"{line[:match.start(2)]}[redacted]" if match else line
        safe_lines.append(TOKEN_VALUE.sub("[redacted]", safe_line))
    return "\n".join(safe_lines)


def _terms(text: str) -> list[str]:
    return [term.lower() for term in TOKEN_RE.findall(text) if len(term) > 2]


def _chunks(documents: list[dict], chunk_lines: int = 32, overlap: int = 6) -> list[dict]:
    chunks = []
    step = chunk_lines - overlap
    for document in documents:
        path = str(document.get("path", ""))
        lines = redact_source(str(document.get("content", ""))).splitlines()
        for start in range(0, len(lines), step):
            portion = lines[start:start + chunk_lines]
            if not portion:
                continue
            chunks.append({
                "path": path,
                "startLine": start + 1,
                "endLine": start + len(portion),
                "text": "\n".join(line[:200] for line in portion)[:1800],
            })
    return chunks


def retrieve_context(
    query: str,
    documents: list[dict],
    *,
    limit: int = 2,
) -> list[dict]:
    """Rank source chunks with BM25, returning short excerpts and line citations."""
    chunks = _chunks(documents)
    query_terms = _terms(query)
    if not chunks or not query_terms:
        return []

    tokenized = [_terms(f"{chunk['path']} {chunk['text']}") for chunk in chunks]
    frequencies = [Counter(tokens) for tokens in tokenized]
    average_length = sum(map(len, tokenized)) / max(len(tokenized), 1)
    document_frequency = Counter(
        term for term in set(query_terms)
        for document_terms in tokenized if term in set(document_terms)
    )
    scores = []
    for chunk, counts, terms in zip(chunks, frequencies, tokenized):
        length = max(len(terms), 1)
        score = 0.0
        for term in query_terms:
            count = counts[term]
            if not count:
                continue
            inverse = math.log(1 + (len(chunks) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            score += inverse * (count * 2.2) / (count + 1.2 * (0.25 + 0.75 * length / max(average_length, 1)))
        if score > 0:
            scores.append((score, chunk))

    scores.sort(key=lambda item: (-item[0], item[1]["path"], item[1]["startLine"]))
    selected = []
    seen_paths = set()
    for score, chunk in scores:
        if chunk["path"] in seen_paths:
            continue
        selected.append({**chunk, "score": round(score, 4)})
        seen_paths.add(chunk["path"])
        if len(selected) >= limit:
            break
    return selected


def retrieve_for_hypothesis(hypothesis: dict, issue_report: str, documents: list[dict]) -> list[dict]:
    query = " ".join((
        issue_report,
        hypothesis.get("title", ""),
        hypothesis.get("file", ""),
        hypothesis.get("evidence", ""),
        hypothesis.get("category", ""),
        hypothesis.get("suggestion", ""),
    ))
    return retrieve_context(query, documents)
