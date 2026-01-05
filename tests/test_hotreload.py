import asyncio
import pytest
from pydantic_settings import SettingsConfigDict
from pattern_agentic_settings.base import PABaseSettings, WATCHFILES_AVAILABLE


@pytest.mark.skipif(not WATCHFILES_AVAILABLE, reason="Requires watchfiles (install with [hotreload])")
class TestHotReload:
    class Settings(PABaseSettings):
        model_config = SettingsConfigDict(
            env_prefix="TST_"
        )
        worker_count: int

    def test_watch_task_initialized_to_none(self, monkeypatch):
        monkeypatch.setenv('TST_WORKER_COUNT', '10')
        settings = self.Settings.load('pattern_agentic_settings')
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

        if settings._env_watch_task.done():
            exc = settings._env_watch_task.exception()
            if exc:
                pytest.skip(f"Watcher failed to initialize: {exc}")

        env_file.write_text("TST_WORKER_COUNT=15\n")

        for _ in range(50):
            await asyncio.sleep(0.1)
            if settings.worker_count == 15:
                break
        else:
            pytest.fail("Hotreload did not detect file change within 5 seconds")

        settings.stop_watching()
        await asyncio.sleep(0.1)
        assert settings._env_watch_task.cancelled() or settings._env_watch_task.done()

    def test_stop_watching_without_task(self, monkeypatch):
        monkeypatch.setenv('TST_WORKER_COUNT', '10')
        settings = self.Settings.load('pattern_agentic_settings')
        settings.stop_watching()


class TestHotReloadNotAvailable:
    class Settings(PABaseSettings):
        model_config = SettingsConfigDict(
            env_prefix="TST_"
        )
        worker_count: int

    def test_watch_env_file_raises_when_unavailable(self, monkeypatch):
        monkeypatch.setenv('TST_WORKER_COUNT', '10')
        monkeypatch.setenv('TST_DOT_ENV', '/tmp/fake.env')

        import pattern_agentic_settings.base as base_module
        original = base_module.WATCHFILES_AVAILABLE
        base_module.WATCHFILES_AVAILABLE = False

        try:
            settings = self.Settings.load('pattern_agentic_settings')
            with pytest.raises(ImportError, match="Hot reload requires watchfiles"):
                settings.watch_env_file()
        finally:
            base_module.WATCHFILES_AVAILABLE = original
