"""Deterministic, read-only source analysis used by the FastAPI scan endpoint."""

from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Callable
from urllib.parse import quote

from fastapi import HTTPException

GitHubJson = Callable[[str, str], dict]

CHECKS = [
    {
        "id": "js-eval", "severity": "high", "confidence": 0.91,
        "languages": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"},
        "pattern": re.compile(r"\beval\s*\("),
        "title": "Dynamic code execution with eval()", "category": "Security risk",
        "fix": "Avoid evaluating strings as code. Replace this with explicit parsing or a safe lookup table, and validate untrusted input.",
    },
    {
        "id": "python-eval", "severity": "high", "confidence": 0.9,
        "languages": {".py"}, "pattern": re.compile(r"\b(?:eval|exec)\s*\("),
        "title": "Dynamic code execution in Python", "category": "Security risk",
        "fix": "Avoid eval() or exec() on runtime strings. Use a safe parser or explicit operations, especially when input can be influenced by a user.",
    },
    {
        "id": "python-shell-true", "severity": "high", "confidence": 0.87,
        "languages": {".py"},
        "pattern": re.compile(r"\bsubprocess\.(?:run|Popen|call|check_call|check_output)\s*\([^\n]*\bshell\s*=\s*True"),
        "title": "Shell command execution enabled", "category": "Security risk",
        "fix": "Pass an argument list with shell=False (the default). If a shell is essential, never interpolate untrusted input and validate each argument.",
    },
    {
        "id": "tls-verify-disabled", "severity": "high", "confidence": 0.96,
        "languages": {".py"}, "pattern": re.compile(r"\bverify\s*=\s*False\b"),
        "title": "TLS certificate verification is disabled", "category": "Security risk",
        "fix": "Enable certificate verification. For a private certificate authority, configure its CA bundle instead of disabling verification.",
    },
    {
        "id": "js-innerhtml", "severity": "medium", "confidence": 0.78,
        "languages": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"},
        "pattern": re.compile(r"\.innerHTML\s*="),
        "title": "HTML is assigned directly to innerHTML", "category": "Security risk",
        "fix": "Prefer textContent or framework escaping. If HTML is required, sanitize it with a well-maintained sanitizer before insertion.",
    },
    {
        "id": "js-https-disabled", "severity": "high", "confidence": 0.94,
        "languages": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"},
        "pattern": re.compile(r"\brejectUnauthorized\s*:\s*false\b"),
        "title": "HTTPS certificate validation is disabled", "category": "Security risk",
        "fix": "Keep TLS certificate validation enabled. Configure the trusted CA when connecting to services with private certificates.",
    },
    {
        "id": "weak-hash", "severity": "medium", "confidence": 0.82,
        "languages": {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".java"},
        "pattern": re.compile(r"(?:createHash\s*\(\s*['\"](?:md5|sha1)['\"]|hashlib\.(?:md5|sha1)\s*\(|MessageDigest\.getInstance\s*\(\s*['\"](?:MD5|SHA-1)['\"])", re.I),
        "title": "Weak hash algorithm used", "category": "Security risk",
        "fix": "For security-sensitive hashing, use SHA-256 or stronger. Use a password-hashing function such as Argon2, scrypt, or bcrypt for passwords.",
    },
    {
        "id": "hardcoded-credential", "severity": "high", "confidence": 0.75,
        "languages": {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".java", ".rb", ".php", ".env.example"},
        "pattern": re.compile(r"\b(?:api[_-]?key|secret|password|access[_-]?token)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", re.I),
        "title": "Possible hard-coded credential", "category": "Security risk",
        "fix": "Move credentials to a secret manager or environment variable, rotate any real credential that was committed, and avoid logging it.",
    },
    {
        "id": "python-broad-except", "severity": "low", "confidence": 0.7,
        "languages": {".py"}, "pattern": re.compile(r"^\s*except\s*:\s*(?:#.*)?$"),
        "title": "Bare exception handler can hide failures", "category": "Potential bug",
        "fix": "Catch the specific exception types you expect and handle them deliberately. Let unexpected failures surface with useful context.",
    },
]

IGNORED_PATH = re.compile(r"(^|/)(?:node_modules|vendor|dist|build|\.git|coverage|\.next|\.venv)(/|$)", re.I)
CODE_EXTENSIONS = set().union(*(check["languages"] for check in CHECKS))
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
FILE_LIMIT = 35
BYTE_LIMIT_PER_FILE = 80_000
MAX_TREE_ENTRIES = 10_000
MAX_TEST_HISTORY_BYTES = 100_000
TEST_HISTORY_PATHS = {"oracle-test-history.json", ".oracle/test-history.json"}
TEST_FILE_PATTERN = re.compile(
    r"(?:^|/)(?:(?:tests?|__tests__)/.*|test_[^/]+|[^/]+_test|[^/]+\.(?:test|spec))\.(?:py|js|jsx|mjs|cjs|ts|tsx|go|java|rb|php)$",
    re.I,
)


def _redacted_evidence(line: str, rule_id: str) -> str:
    if rule_id == "hardcoded-credential":
        return re.sub(r"(['\"])[^'\"\s]{8,}\1", r"\1[redacted]\1", line)
    return line.strip()[:240]


def analyze_text(file_path: str, source: str) -> list[dict]:
    extension = PurePosixPath(file_path).suffix.lower()
    findings = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        for check in CHECKS:
            if extension in check["languages"] and check["pattern"].search(line):
                findings.append({
                    "id": f"{check['id']}:{file_path}:{line_number}",
                    "rule": check["id"],
                    "title": check["title"],
                    "category": check["category"],
                    "severity": check["severity"],
                    "confidence": check["confidence"],
                    "file": file_path,
                    "line": line_number,
                    "evidence": _redacted_evidence(line, check["id"]),
                    "suggestion": check["fix"],
                })
    return findings


def _discover_test_candidates(entries: list[dict], source_paths: list[str]) -> list[dict]:
    """Find test-file paths and infer likely file coverage from shared names."""
    candidates = []
    for entry in entries[:MAX_TREE_ENTRIES]:
        path = entry.get("path", "")
        if entry.get("type") != "blob" or not TEST_FILE_PATTERN.search(path):
            continue
        stem = PurePosixPath(path).stem.lower()
        stem = re.sub(r"^(?:test_|tests_)", "", stem)
        stem = re.sub(r"(?:_test|\.test|\.spec)$", "", stem)
        test_tokens = set(re.findall(r"[a-z0-9]+", stem)) - {"test", "tests", "unit", "spec"}
        covers = []
        for source_path in source_paths:
            source_stem = PurePosixPath(source_path).stem.lower()
            source_tokens = set(re.findall(r"[a-z0-9]+", source_stem)) - {"test", "tests"}
            if test_tokens & source_tokens or (source_stem and source_stem in stem):
                covers.append(source_path)
        candidates.append({
            "id": path,
            "covers": sorted(covers),
            "coverageSource": "inferred from matching file names",
            "duration_s": 1.0,
            "durationSource": "assumed 1 second; repository run history is not available",
        })
    return candidates[:500]


def _apply_test_history(
    owner: str, repo: str, candidates: list[dict], entries: list[dict], source_paths: list[str],
    token: str, github_json: GitHubJson,
) -> dict:
    """Apply an opt-in repository report with measured timings and file coverage."""
    history_entry = next(
        (item for item in entries if item.get("path") in TEST_HISTORY_PATHS and item.get("type") == "blob"),
        None,
    )
    if not history_entry:
        return {
            "available": False, "appliedTests": 0, "source": None,
            "note": "No oracle-test-history.json report found; durations and coverage remain estimates.",
        }
    if not isinstance(history_entry.get("size"), int) or history_entry["size"] > MAX_TEST_HISTORY_BYTES:
        return {
            "available": False, "appliedTests": 0, "source": history_entry["path"],
            "note": "Test-history report was too large or missing a valid size; estimates remain in use.",
        }

    try:
        blob = github_json(
            f"/repos/{quote(owner)}/{quote(repo)}/git/blobs/{quote(history_entry['sha'])}", token
        )
        if blob.get("encoding") != "base64" or not blob.get("content"):
            raise ValueError("report blob was not base64 encoded")
        compact = re.sub(r"\s+", "", blob["content"])
        decoded = base64.b64decode(compact)
        if len(decoded) > MAX_TEST_HISTORY_BYTES:
            raise ValueError("report content exceeded the size limit")
        report = json.loads(decoded.decode("utf-8"))
        if report.get("schemaVersion") != 1 or not isinstance(report.get("tests"), list):
            raise ValueError("expected schemaVersion 1 and a tests array")
    except Exception:
        return {
            "available": False, "appliedTests": 0, "source": history_entry["path"],
            "note": "Test-history report was invalid or unreadable; estimates remain in use.",
        }

    candidate_map = {item["id"]: item for item in candidates}
    valid_sources = set(source_paths)
    applied = 0
    for row in report["tests"]:
        if not isinstance(row, dict):
            continue
        candidate = candidate_map.get(row.get("id"))
        try:
            duration = float(row.get("durationSeconds"))
        except (TypeError, ValueError):
            continue
        if not candidate or duration <= 0 or duration > 3600:
            continue

        covers = row.get("covers", [])
        valid_covers = sorted({path for path in covers if isinstance(path, str) and path in valid_sources}) if isinstance(covers, list) else []
        candidate["duration_s"] = duration
        candidate["durationSource"] = "measured duration from oracle-test-history.json"
        if valid_covers:
            candidate["covers"] = valid_covers
            candidate["coverageSource"] = "reported CI coverage from oracle-test-history.json"
        applied += 1

    return {
        "available": applied > 0,
        "appliedTests": applied,
        "source": history_entry["path"],
        "note": (
            f"Applied recorded timings and coverage metadata for {applied} discovered test file(s)."
            if applied else "No valid matching test records were found; estimates remain in use."
        ),
    }


def analyze_repository(owner: str, repo: str, token: str, github_json: GitHubJson) -> dict:
    metadata = github_json(f"/repos/{quote(owner)}/{quote(repo)}", token)
    if metadata.get("private"):
        raise HTTPException(status_code=400, detail="Only public repositories are supported in this MVP.")
    branch = metadata.get("default_branch")
    if not branch:
        raise HTTPException(status_code=400, detail="This repository has no default branch to analyze.")

    tree_path = f"/repos/{quote(owner)}/{quote(repo)}/git/trees/{quote(branch, safe='')}?recursive=1"
    tree_result = github_json(tree_path, token)
    entries = tree_result.get("tree", [])
    candidates = [
        entry for entry in entries[:MAX_TREE_ENTRIES]
        if entry.get("type") == "blob"
        and not IGNORED_PATH.search(entry.get("path", ""))
        and PurePosixPath(entry.get("path", "")).suffix.lower() in CODE_EXTENSIONS
        and isinstance(entry.get("size"), int)
        and entry["size"] <= BYTE_LIMIT_PER_FILE
    ]

    findings = []
    scanned_files = []
    scanned_bytes = 0
    failed_files = 0
    for entry in candidates[:FILE_LIMIT]:
        try:
            blob = github_json(
                f"/repos/{quote(owner)}/{quote(repo)}/git/blobs/{quote(entry['sha'])}", token
            )
            if blob.get("encoding") != "base64" or not blob.get("content"):
                continue
            compact = re.sub(r"\s+", "", blob["content"])
            source = base64.b64decode(compact).decode("utf-8", errors="replace")
            scanned_bytes += len(source.encode("utf-8"))
            scanned_files.append(entry["path"])
            findings.extend(analyze_text(entry["path"], source))
        except Exception:
            failed_files += 1

    findings.sort(key=lambda item: (
        SEVERITY_ORDER.get(item["severity"], 99), item["file"], item["line"]
    ))
    source_paths = [path for path in scanned_files if not TEST_FILE_PATTERN.search(path)]
    test_candidates = _discover_test_candidates(entries, source_paths)
    test_history = _apply_test_history(
        owner, repo, test_candidates, entries, source_paths, token, github_json
    )
    return {
        "repository": {
            "name": metadata.get("full_name", f"{owner}/{repo}"),
            "description": metadata.get("description"),
            "branch": branch,
            "url": metadata.get("html_url", f"https://github.com/{owner}/{repo}"),
        },
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "scan": {
            "filesFound": len(candidates),
            "filesScanned": len(scanned_files),
            "fileLimit": FILE_LIMIT,
            "byteLimitPerFile": BYTE_LIMIT_PER_FILE,
            "scannedBytes": scanned_bytes,
            "truncated": len(candidates) > FILE_LIMIT or len(entries) > MAX_TREE_ENTRIES or bool(tree_result.get("truncated")),
            "failedFiles": failed_files,
            "testFilesFound": len(test_candidates),
            "measuredTestFiles": test_history["appliedTests"],
            "method": "Read-only deterministic checks on source files from the default branch via FastAPI.",
        },
        "files": scanned_files,
        "testCandidates": test_candidates,
        "testHistory": test_history,
        "findings": findings,
        "disclaimer": "Heuristic findings need engineer review. A clean scan does not prove the repository is free of bugs or security issues.",
    }
