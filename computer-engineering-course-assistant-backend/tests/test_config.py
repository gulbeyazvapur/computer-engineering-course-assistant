from __future__ import annotations

import importlib
from pathlib import Path


def test_foundry_model_cache_dir_defaults_to_foundry_cli_cache_root():
    """B. No FOUNDRY_MODEL_CACHE_DIR set -> defaults to the same cache root
    the Foundry CLI itself uses (~/.foundry/cache/models, per
    `foundry cache location`), not a project-specific directory."""
    from app.core.config import settings

    assert settings.foundry_model_cache_dir == Path.home() / ".foundry" / "cache" / "models"


def test_foundry_model_cache_dir_env_override(monkeypatch, tmp_path):
    """C. FOUNDRY_MODEL_CACHE_DIR, when set, overrides the default."""
    from app.core import config as config_module

    custom = str(tmp_path / "custom-foundry-cache")
    monkeypatch.setenv("FOUNDRY_MODEL_CACHE_DIR", custom)
    try:
        importlib.reload(config_module)
        assert str(config_module.settings.foundry_model_cache_dir) == custom
    finally:
        monkeypatch.delenv("FOUNDRY_MODEL_CACHE_DIR", raising=False)
        importlib.reload(config_module)
