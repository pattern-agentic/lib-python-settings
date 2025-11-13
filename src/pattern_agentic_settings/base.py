from typing import Optional

from pydantic import ValidationError, Field
from pydantic_settings import BaseSettings
#from watchfiles import awatch

import os
import asyncio
import logging
import importlib

logger = logging.getLogger(__name__)


class PABaseSettings(BaseSettings):
    _reload_lock: asyncio.Lock = asyncio.Lock()
    _env_watch_task: asyncio.Task

    dot_env: Optional[str] = Field(default=None, description="The path to the .env file to load env variables from (optional)")
    app_name: str
    app_version: str

    @staticmethod
    def format_config_validation_error(error: ValidationError) -> str:
        """Format Pydantic validation errors into a more readable format."""
        missing_fields = []
        invalid_fields = []

        for err in error.errors():
            if err['type'] == 'missing':
                missing_fields.append(err['loc'][0] if err['loc'] else 'unknown')
            else:
                field_name = err['loc'][0] if err['loc'] else 'unknown'
                invalid_fields.append(f"{field_name}: {err['msg']}")

        error_message = "Configuration validation failed:\n"

        if missing_fields:
            error_message += "\nMissing required configuration fields:\n"
            for field in sorted(missing_fields):
                error_message += f"  - {field}\n"

        if invalid_fields:
            error_message += "\nInvalid configuration values:\n"
            for field in invalid_fields:
                error_message += f"  - {field}\n"

        error_message += "\nPlease check your environment variables or .env file."
        return error_message

    def reload(self):
        """Reload env files and update this instance in-place."""
        new_instance = self.__class__(
            app_version=self.app_version,
            _env_file=self.dot_env
        )
        new_values = new_instance.model_dump()
        for k, v in new_values.items():
            old = getattr(self, k)
            if v != old:
                logger.info(f"Reloading changed parameter {k}")
                setattr(self, k, v)
        logger.info("-------------------")

    async def _watch_env_file(self):
        logger.info(f"Watching for changes in {self.dot_env}")

        async for changes in awatch(self.dot_env):
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
        if self.dot_env:
            loop = asyncio.get_running_loop()
            self._env_watch_task = loop.create_task(self._watch_env_file())

    def safe_describe(self, indent="  "):
        sensitive_keys = [
            'password', 'secret', 'key', 'token', 'auth', 'service_account'
        ]
        safe_desc = {}
        for key, value in self.model_dump().items():
            if any(x in key for x in sensitive_keys):
                none_or_empty = (value is None or value == '')
                safe_desc[key] = '(empty)' if none_or_empty else '(redacted)'
            else:
                safe_desc[key] = value
        keys = sorted(safe_desc.keys())
        return "\n".join([f"{indent}{k}: {safe_desc[k]}" for k in keys])

    @staticmethod
    def _version_from_importlib(package_name: str, fallback: Optional[str]):
        try:
            return importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            return fallback or "0.0.0-dev"

    @classmethod
    def load(cls,
             package_name: str,
             app_name: Optional[str] = None,
             app_version: Optional[str] = None,
             fallback_version: Optional[str] = None,
             log_conf_on_startup: bool = True
             ):
        env_prefix = cls.model_config.get('env_prefix', '')
        dot_env_path = os.environ.get(f"{env_prefix}DOT_ENV", None)
        if dot_env_path and not os.path.isfile(dot_env_path):
            logger.warning(f"WARNING: dot env file '{dot_env_path}' does not exist\n")

        version = app_version
        if not version:
            version = PABaseSettings._version_from_importlib(package_name, fallback_version)

        pretty_app_name = app_name
        if not pretty_app_name:
            components = package_name.replace("-", "_").split("_")
            pretty_app_name = " ".join(word.capitalize() for word in components)

        try:
            settings = cls(app_version=version, app_name=pretty_app_name, _env_file=dot_env_path)
            logger.info(f"{app_name} v{version}")
            if log_conf_on_startup:
                logger.info(f"\nConfiguration:\n{settings.safe_describe()}\n--------------------\n")
            return settings
        except ValidationError as exc:
            error_msg = PABaseSettings.format_config_validation_error(exc)
            raise RuntimeError(error_msg) from exc
