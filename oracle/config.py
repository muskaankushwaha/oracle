"""Settings, read from the .env file (copy .env.example to .env to start).

Owner: Muskan Kushwaha
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv not installed: fall back to real environment variables
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALID_PROVIDERS = {"none", "gemini", "ollama"}


@dataclass(frozen=True)
class Settings:
    llm_provider: str = "none"
    gemini_api_key: str = ""
    ollama_model: str = "llama3.2:3b"
    ollama_host: str = "http://localhost:11434"
    demo_repo_path: Path = PROJECT_ROOT / "workspace" / "eshop"
    db_path: Path = PROJECT_ROOT / "oracle.db"
    test_timeout_s: int = 60


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def load_settings(env_file: Path | None = None) -> Settings:
    """Read settings from .env (if present) and the environment."""
    if load_dotenv is not None:
        load_dotenv(env_file or PROJECT_ROOT / ".env", override=False)

    provider = os.getenv("LLM_PROVIDER", "none").strip().lower() or "none"
    if provider not in VALID_PROVIDERS:
        raise ValueError(f"LLM_PROVIDER must be one of {sorted(VALID_PROVIDERS)}, got {provider!r}")

    return Settings(
        llm_provider=provider,
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        ollama_model=os.getenv("OLLAMA_MODEL", Settings.ollama_model),
        ollama_host=os.getenv("OLLAMA_HOST", Settings.ollama_host),
        demo_repo_path=_resolve(os.getenv("DEMO_REPO_PATH", "workspace/eshop")),
        db_path=_resolve(os.getenv("DB_PATH", "oracle.db")),
        test_timeout_s=int(os.getenv("TEST_TIMEOUT_S", "60")),
    )
