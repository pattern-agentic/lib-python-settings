import os
import pytest
import tempfile
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


def test_settings_load_with_secrets_file(monkeypatch):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('TST_WORKER_COUNT=99\n')
        secrets_path = f.name

    try:
        monkeypatch.setenv('TST_DOT_ENV_SECRETS', secrets_path)
        settings = Settings.load('pattern_agentic_settings')

        assert settings.worker_count == 99
        assert settings.dot_env_secrets == secrets_path
    finally:
        os.unlink(secrets_path)


def test_settings_secrets_override_dot_env(monkeypatch):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('TST_WORKER_COUNT=10\n')
        env_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.secrets', delete=False) as f:
        f.write('TST_WORKER_COUNT=50\n')
        secrets_path = f.name

    try:
        monkeypatch.setenv('TST_DOT_ENV', env_path)
        monkeypatch.setenv('TST_DOT_ENV_SECRETS', secrets_path)
        settings = Settings.load('pattern_agentic_settings')

        assert settings.worker_count == 50
        assert settings.dot_env == env_path
        assert settings.dot_env_secrets == secrets_path
    finally:
        os.unlink(env_path)
        os.unlink(secrets_path)


def test_settings_missing_secrets_file_warns(monkeypatch):
    import io
    import logging

    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger = logging.getLogger('test_secrets_warn')
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    monkeypatch.setenv('TST_WORKER_COUNT', '1')
    monkeypatch.setenv('TST_DOT_ENV_SECRETS', '/nonexistent/secrets.env')

    settings = Settings.load('pattern_agentic_settings', logger=logger)

    assert settings.worker_count == 1
    assert "secrets file '/nonexistent/secrets.env' does not exist" in log_stream.getvalue()

