from .base import PABaseSettings

try:
    from .hotreload import HotReloadMixin
    __all__ = ['PABaseSettings', 'HotReloadMixin']
except ImportError:
    __all__ = ['PABaseSettings']
