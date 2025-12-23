import asyncio
import logging

try:
    from watchfiles import awatch
except ImportError as e:
    raise ImportError(
        "HotReloadMixin requires watchfiles. "
        "Install with: pip install pattern_agentic_settings[hotreload]"
    ) from e

logger = logging.getLogger(__name__)


class HotReloadMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reload_lock = asyncio.Lock()
        self._env_watch_task = None

    async def _watch_env_file(self):
        paths = [p for p in [self.dot_env, self.dot_env_secrets] if p]
        if not paths:
            return
        logger.info(f"Watching for changes in {paths}")

        async for changes in awatch(*paths):
            logger.info("------------------------------")
            logger.info(f"Detected env change: {changes}")
            async with self._reload_lock:
                try:
                    self.reload()
                except Exception as exc:
                    logging.error(
                        f"Failed to reload settings: {exc}",
                        exc_info=True
                    )

    def watch_env_file(self):
        if self.dot_env or self.dot_env_secrets:
            loop = asyncio.get_running_loop()
            self._env_watch_task = loop.create_task(self._watch_env_file())

    def stop_watching(self):
        if self._env_watch_task and not self._env_watch_task.done():
            self._env_watch_task.cancel()
            logger.info("Stopped watching env file")
