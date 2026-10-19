"""Shared setup for every test.

All tests run with LLM_PROVIDER=offline, so no test ever calls a real language
model or uses up a free-tier limit. The speech models are not preloaded; tests
that need them are marked slow and skipped unless you run: python -m pytest -m slow
"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Set before any project module is imported, so .env cannot override them.
os.environ["LLM_PROVIDER"] = "offline"
os.environ["PRELOAD_MODELS"] = "0"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """The FastAPI app, with its request log written to a temporary folder instead of logs/."""
    from fastapi.testclient import TestClient

    from app import server
    from pipeline import config

    monkeypatch.setattr(config, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(server, "LOG_PATH", tmp_path / "qa_log.jsonl")
    return TestClient(server.app)
