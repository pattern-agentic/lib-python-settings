
# 2.0.0

Improvements:

  - add support for injecting dot evn files via `__PA_SETTINGS_DOT_ENVS`
  - automatically load watchfiles if dependency available
  
Breaking changes:

  - The HotReloadMixin is deprecated. This fucntionality has been
    moved into the base class itself, and is auto-loaded if the
    `watchfiles` module is available
  
# 1.2.0

Improvements:

  - add support for multiple dot env files: `$PREFIX_DOT_ENV`, `$PREFIX_DOT_ENV_SECRETS`

# 1.1.0

Fixes:
  - print settings to stdout when `log_conf_on_startup` is `True`

Improvements:
  - added an optional `logger` to `PABaseSettings.load()`
  
# 1.0.1
	
Fixes:
  - set settings logger level to INFO
