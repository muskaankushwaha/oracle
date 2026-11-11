"""Tests for the FastAPI-backed repository analysis pipeline."""

import base64
import json

from oracle_api.analyzer import analyze_repository, analyze_text


def test_analyze_text_returns_line_evidence_and_suggestion():
    findings = analyze_text("src/app.js", "const result = eval(input);\n")

    assert len(findings) == 1
    assert findings[0]["rule"] == "js-eval"
    assert findings[0]["line"] == 1
    assert findings[0]["evidence"] == "const result = eval(input);"
    assert findings[0]["suggestion"]


def test_credential_evidence_is_redacted():
    findings = analyze_text("settings.py", 'API_KEY = "topsecretvalue123"')

    assert findings[0]["rule"] == "hardcoded-credential"
    assert "topsecretvalue123" not in findings[0]["evidence"]
    assert "[redacted]" in findings[0]["evidence"]


def test_repository_scan_reads_blobs_and_skips_ignored_paths():
    source = "value = eval(user_input)\n"
    encoded = base64.b64encode(source.encode()).decode()

    def fake_github_json(path, token):
        assert token == "session-token"
        if path == "/repos/example/project":
            return {
                "full_name": "example/project",
                "description": "demo",
                "default_branch": "main",
                "html_url": "https://github.com/example/project",
                "private": False,
            }
        if "/git/trees/" in path:
            return {
                "tree": [
                    {"path": "src/app.js", "type": "blob", "sha": "ok", "size": 30},
                    {"path": "node_modules/pkg/index.js", "type": "blob", "sha": "skip", "size": 30},
                    {"path": "tests/test_app.js", "type": "blob", "sha": "test", "size": 40},
                    {"path": "oracle-test-history.json", "type": "blob", "sha": "history", "size": 120},
                ],
                "truncated": False,
            }
        if path.endswith("/git/blobs/ok"):
            return {"encoding": "base64", "content": encoded}
        if path.endswith("/git/blobs/test"):
            test_source = base64.b64encode(b"describe('app', () => {});\n").decode()
            return {"encoding": "base64", "content": test_source}
        if path.endswith("/git/blobs/history"):
            history = json.dumps({
                "schemaVersion": 1,
                "tests": [{
                    "id": "tests/test_app.js",
                    "durationSeconds": 4.7,
                    "covers": ["src/app.js"],
                }],
            }).encode()
            return {"encoding": "base64", "content": base64.b64encode(history).decode()}
        raise AssertionError(f"Unexpected GitHub API path: {path}")

    result = analyze_repository("example", "project", "session-token", fake_github_json)

    assert result["repository"]["name"] == "example/project"
    assert result["scan"]["filesScanned"] == 2
    assert result["files"] == ["src/app.js", "tests/test_app.js"]
    assert result["findings"][0]["rule"] == "js-eval"
    assert result["scan"]["testFilesFound"] == 1
    assert result["testCandidates"][0]["id"] == "tests/test_app.js"
    assert result["testCandidates"][0]["covers"] == ["src/app.js"]
    assert result["testCandidates"][0]["duration_s"] == 4.7
    assert result["testCandidates"][0]["coverageSource"].startswith("reported CI")
    assert result["testHistory"]["appliedTests"] == 1
