import os
import asyncio
import tempfile
import pytest
from pydantic_settings import SettingsConfigDict
from pattern_agentic_settings.base import PABaseSettings

try:
    from pattern_agentic_settings.hotreload import HotReloadMixin
    HOTRELOAD_AVAILABLE = True
except ImportError:
    HOTRELOAD_AVAILABLE = False


@pytest.mark.skipif(not HOTRELOAD_AVAILABLE, reason="Requires watchfiles (install with [hotreload])")
class TestHotReload:
    class Settings(HotReloadMixin, PABaseSettings):
        model_config = SettingsConfigDict(
            env_prefix="TST_"
        )
        worker_count: int

    def test_mixin_initialization(self, monkeypatch):
        monkeypatch.setenv('TST_WORKER_COUNT', '10')
        settings = self.Settings.load('pattern_agentic_settings')

        assert hasattr(settings, '_reload_lock')
        assert hasattr(settings, '_env_watch_task')
        assert settings._env_watch_task is None

    def test_watch_env_file_without_dot_env(self, monkeypatch):
        monkeypatch.setenv('TST_WORKER_COUNT', '10')
        settings = self.Settings.load('pattern_agentic_settings')

        settings.watch_env_file()
        assert settings._env_watch_task is None

    @pytest.mark.asyncio
    async def test_watch_env_file_with_dot_env(self, monkeypatch, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TST_WORKER_COUNT=5\n")

        monkeypatch.setenv('TST_DOT_ENV', str(env_file))

        settings = self.Settings.load('pattern_agentic_settings')
        assert settings.worker_count == 5

        settings.watch_env_file()
        assert settings._env_watch_task is not None

        await asyncio.sleep(0.1)

        env_file.write_text("TST_WORKER_COUNT=15\n")

        await asyncio.sleep(0.5)

        assert settings.worker_count == 15

        settings.stop_watching()
        await asyncio.sleep(0.1)
        assert settings._env_watch_task.cancelled() or settings._env_watch_task.done()

    def test_stop_watching_without_task(self, monkeypatch):
        monkeypatch.setenv('TST_WORKER_COUNT', '10')
        settings = self.Settings.load('pattern_agentic_settings')

        settings.stop_watching()
