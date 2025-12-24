from typing import Optional

from pydantic import ValidationError, Field
from pydantic_settings import BaseSettings

import os
import sys
import logging
import importlib


def _create_default_logger():
    lg = logging.getLogger(__name__)
    lg.setLevel(logging.INFO)
    if not lg.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        lg.addHandler(handler)
        lg.propagate = False
    return lg


class PABaseSettings(BaseSettings):
    dot_env: Optional[str] = Field(default=None, description="The path to the .env file to load env variables from (optional)")
    dot_env_secrets: Optional[str] = Field(default=None, description="The path to a secrets .env file (optional, overrides dot_env values)")
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
        env_files = [p for p in [self.dot_env, self.dot_env_secrets] if p]
        new_instance = self.__class__(
            app_version=self.app_version,
            app_name=self.app_name,
            dot_env=self.dot_env,
            dot_env_secrets=self.dot_env_secrets,
            _env_file=env_files if env_files else None
        )
        new_values = new_instance.model_dump()
        for k, v in new_values.items():
            old = getattr(self, k)
            if v != old:
                self._logger.info(f"Reloading changed parameter {k}")
                setattr(self, k, v)
        self._logger.info("-------------------")


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
             log_conf_on_startup: bool = True,
             logger: Optional[logging.Logger] = None
             ):
        if logger is None:
            logger = _create_default_logger()

        env_prefix = cls.model_config.get('env_prefix', '')
        dot_env_path = os.environ.get(f"{env_prefix}DOT_ENV", None)
        if dot_env_path and not os.path.isfile(dot_env_path):
            logger.warning(f"WARNING: dot env file '{dot_env_path}' does not exist\n")

        dot_env_secrets_path = os.environ.get(f"{env_prefix}DOT_ENV_SECRETS", None)
        if dot_env_secrets_path and not os.path.isfile(dot_env_secrets_path):
            logger.warning(f"WARNING: secrets file '{dot_env_secrets_path}' does not exist\n")

        env_files = [p for p in [dot_env_path, dot_env_secrets_path] if p]
        env_file_arg = env_files if env_files else None

        version = app_version
        if not version:
            version = PABaseSettings._version_from_importlib(package_name, fallback_version)

        pretty_app_name = app_name
        if not pretty_app_name:
            components = package_name.replace("-", "_").split("_")
            pretty_app_name = " ".join(word.capitalize() for word in components)

        try:
            settings = cls(
                app_version=version,
                app_name=pretty_app_name,
                dot_env=dot_env_path,
                dot_env_secrets=dot_env_secrets_path,
                _env_file=env_file_arg
            )
            settings._logger = logger
            logger.info(f"{pretty_app_name} v{version}")
            if log_conf_on_startup:
                logger.info(f"\nConfiguration:\n{settings.safe_describe()}\n--------------------\n")
            return settings
        except ValidationError as exc:
            error_msg = PABaseSettings.format_config_validation_error(exc)
            raise RuntimeError(error_msg) from exc
