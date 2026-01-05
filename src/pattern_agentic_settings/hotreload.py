import warnings

warnings.warn(
    "HotReloadMixin is deprecated. Hot reload is now built into PABaseSettings. "
    "Use Settings.load(..., watch_env_files=True) instead.",
    DeprecationWarning,
    stacklevel=2
)


class HotReloadMixin:
    """Deprecated. Hot reload is now built into PABaseSettings."""
    pass
