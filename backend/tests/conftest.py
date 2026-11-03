import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Tests never touch a real database or a real model provider, and they never read the
# developer's .env for the settings they assert on. Plain assignment, not setdefault:
# a local .env saying LLM_FALLBACK= (empty) silently reduced the provider chain to one
# entry and failed a test that is about the *default* chain — a suite that passes or
# fails depending on whose machine it runs on is worse than no suite.
os.environ["DATABASE_URL"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["ENV"] = "test"
os.environ["LLM_PROVIDER"] = "groq"
os.environ["LLM_FALLBACK"] = "gemini"

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
