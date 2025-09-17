"""Tests for API key enforcement logic in the FastAPI layer."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

import regradar.api


@pytest.fixture(autouse=True)
def reset_api_module(monkeypatch):
    """Ensure each test runs with a clean API module state."""

    # Ensure the environment variable is cleared before the module is (re)imported.
    monkeypatch.delenv("API_KEY", raising=False)
    importlib.reload(regradar.api)
    yield
    monkeypatch.delenv("API_KEY", raising=False)
    importlib.reload(regradar.api)


def test_require_api_key_is_noop_when_unset(monkeypatch):
    """When no API key is configured the guard should not block requests."""

    assert os.getenv("API_KEY") is None
    importlib.reload(regradar.api)

    # Should not raise when the environment variable is missing.
    regradar.api.require_api_key(api_key=None)


def test_require_api_key_blocks_invalid_values(monkeypatch):
    """When an API key is configured, only the matching value should be accepted."""

    monkeypatch.setenv("API_KEY", "secret")
    importlib.reload(regradar.api)

    with pytest.raises(regradar.api.HTTPException) as exc:
        regradar.api.require_api_key(api_key="wrong")
    assert exc.value.status_code == 401

    # Matching key should be accepted.
    regradar.api.require_api_key(api_key="secret")
