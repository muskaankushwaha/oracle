"""Tests for oracle/config.py (owner: Muskan)."""

import pytest

from oracle.config import PROJECT_ROOT, load_settings

KEYS = ["LLM_PROVIDER", "GEMINI_API_KEY", "OLLAMA_MODEL", "OLLAMA_HOST",
        "DEMO_REPO_PATH", "DB_PATH", "TEST_TIMEOUT_S"]


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    """Remove every ORACLE setting from the environment, and restore it after the test."""
    for key in KEYS:
        monkeypatch.setenv(key, "x")    # makes pytest remember the original value...
        monkeypatch.delenv(key)         # ...then removes it for this test
    return tmp_path / "missing.env"     # a .env file that does not exist


def test_defaults_work_offline(clean_env):
    s = load_settings(clean_env)
    assert s.llm_provider == "none"
    assert s.test_timeout_s == 60
    assert s.demo_repo_path == PROJECT_ROOT / "workspace" / "eshop"


def test_values_come_from_the_environment(clean_env, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "Ollama")
    monkeypatch.setenv("TEST_TIMEOUT_S", "30")
    s = load_settings(clean_env)
    assert s.llm_provider == "ollama"           # case does not matter
    assert s.test_timeout_s == 30


def test_values_come_from_a_dotenv_file(clean_env, monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_PROVIDER=gemini\nDB_PATH=data/test.db\n")
    s = load_settings(env_file)
    assert s.llm_provider == "gemini"
    assert s.db_path == PROJECT_ROOT / "data" / "test.db"   # relative paths start at the project


def test_unknown_provider_is_rejected(clean_env, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "chatgpt")
    with pytest.raises(ValueError):
        load_settings(clean_env)
