import os
import pytest
from pydantic_settings import SettingsConfigDict
from pattern_agentic_settings.base import PABaseSettings


class Settings(PABaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TST_"
    )
    worker_count: int


def test_settings_load_with_custom_attr(monkeypatch):
    monkeypatch.setenv('TST_WORKER_COUNT', '42')
    settings = Settings.load(
        'pattern_agentic_settings',
    )

    assert settings.worker_count == 42
    assert settings.app_name == 'Pattern Agentic Settings'
    assert settings.app_version is not None

def test_settings_load_with_missing_attr(monkeypatch):
    with pytest.raises(RuntimeError):
        settings = Settings.load(
            'pattern_agentic_settings',
        )

