from .base import PABaseSettings, WATCHFILES_AVAILABLE

__all__ = ['PABaseSettings', 'WATCHFILES_AVAILABLE', 'HotReloadMixin']


def __getattr__(name):
    if name == 'HotReloadMixin':
        from .hotreload import HotReloadMixin
        return HotReloadMixin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
