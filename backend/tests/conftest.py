import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Tests never touch a real database or a real model provider.
os.environ.setdefault("DATABASE_URL", "")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("ENV", "test")

import pytest


@pytest.fixture(autouse=True)
def _isolate_singletons():
    """Settings and the gateway are cached process-wide. Without this, a test
    that sets a key leaks a configured gateway into every test after it — the
    exact class of bug that makes a suite pass locally and lie in CI."""
    from app import config, db
    from app.llm import gateway as gateway_mod

    def reset():
        config.get_settings.cache_clear()
        gateway_mod._gateway = None
        db._engine = None
        db._Session = None

    reset()
    yield
    reset()
