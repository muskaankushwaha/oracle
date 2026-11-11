"""Read-only GitHub repository tools for the ORACLE web scanner."""

from __future__ import annotations

import asyncio
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .analyzer import analyze_repository
from .workflow import run_investigation

GITHUB_API = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
MAX_TREE_ENTRIES = 10_000
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")

app = FastAPI(
    title="ORACLE Repository Tools",
    description="Read-only GitHub inspection with explainable soft-computing analysis and optional RAG-grounded LLM explanations.",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    issue_report: str = Field(default="", max_length=1000)
    log_text: str = Field(default="", max_length=20000)


class RepositoryInfo(BaseModel):
    full_name: str
    description: str | None = None
    default_branch: str
    html_url: str
    private: bool


class TreeEntry(BaseModel):
    path: str
    type: str
    sha: str
    size: int | None = None


class RepositoryTree(BaseModel):
    repository: RepositoryInfo
    tree: list[TreeEntry]
    truncated: bool


def _github_json(path: str, token: str) -> dict:
    request = Request(
        f"{GITHUB_API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "ORACLE-read-only-investigator",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        remaining = error.headers.get("X-RateLimit-Remaining")
        if error.code == 404:
            detail = "Repository not found or not accessible."
        elif error.code == 401:
            detail = "GitHub sign-in expired. Reconnect GitHub and try again."
        elif error.code == 403 and remaining == "0":
            detail = "GitHub API rate limit reached. Try again later."
        elif error.code == 403:
            detail = "GitHub denied access to this repository."
        else:
            detail = "GitHub could not complete the read-only repository request."
        raise HTTPException(status_code=error.code, detail=detail) from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise HTTPException(
            status_code=502, detail="GitHub could not be reached. Try again shortly."
        ) from None


def _read_repository_tree(owner: str, repo: str, token: str) -> dict:
    metadata = _github_json(f"/repos/{quote(owner)}/{quote(repo)}", token)
    branch = metadata.get("default_branch")
    if not branch:
        raise HTTPException(status_code=400, detail="This repository has no default branch.")

    tree_path = (
        f"/repos/{quote(owner)}/{quote(repo)}/git/trees/"
        f"{quote(branch, safe='')}?recursive=1"
    )
    tree_result = _github_json(tree_path, token)
    entries = tree_result.get("tree", [])
    return {
        "repository": {
            "full_name": metadata.get("full_name", f"{owner}/{repo}"),
            "description": metadata.get("description"),
            "default_branch": branch,
            "html_url": metadata.get("html_url", f"https://github.com/{owner}/{repo}"),
            "private": bool(metadata.get("private", False)),
        },
        "tree": entries[:MAX_TREE_ENTRIES],
        "truncated": bool(tree_result.get("truncated")) or len(entries) > MAX_TREE_ENTRIES,
    }


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/tools/github/{owner}/{repo}/tree", response_model=RepositoryTree)
async def read_github_repository_tree(
    owner: str,
    repo: str,
    authorization: str | None = Header(default=None),
) -> RepositoryTree:
    """Read repository metadata and its default-branch tree without modifying GitHub."""
    if not NAME_PATTERN.fullmatch(owner) or not NAME_PATTERN.fullmatch(repo):
        raise HTTPException(status_code=400, detail="Invalid GitHub owner or repository name.")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="A GitHub session token is required.")

    result = await asyncio.to_thread(_read_repository_tree, owner, repo, token.strip())
    return RepositoryTree(**result)


@app.post("/tools/github/{owner}/{repo}/analyze")
async def analyze_github_repository(
    owner: str,
    repo: str,
    request: AnalyzeRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Run the LangGraph investigation without executing or changing repository code."""
    if not NAME_PATTERN.fullmatch(owner) or not NAME_PATTERN.fullmatch(repo):
        raise HTTPException(status_code=400, detail="Invalid GitHub owner or repository name.")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="A GitHub session token is required.")

    return await asyncio.to_thread(
        run_investigation, owner, repo, token.strip(), request.issue_report,
        _github_json, request.log_text,
    )
