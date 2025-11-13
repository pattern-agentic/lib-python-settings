
# Pattern Agentic Settings

A settings class based on pydantic-settings that facilitates:

  - printing all settings on startup (redacts senstive attrs)
  - easy loading of .env files via an env variable
  - optionally load app version from importlib (sourced from pyproject.toml)
  - optional hot reload using watchfiles


## Example

```python
class Settings(PABaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MYAPP_"
    )
    worker_count: int

# expects MYAPP_WORKER_COUNT 
# if MYAPP_DOT_ENV points to a file, will try to load vars from it
# throws an error if not defined
settings = Settings.load('my_app')
```

Exepcted output:

```
My App v1.0.0
Configuration:
  WORKER_COUNT: 3
```

And on failure:

```
RuntimeError: Configuration validation failed:

      Missing required configuration fields:
        - worker_count
```


## Tests

To run the tests the package must be installed in edit mode:

    uv pip install -e .
    
    # or to test hotreload
    uv pip install -e .[hotreload]

After that:

    # Base test
    uv run pytest tests/test_base.py

    # All tests
    uv run pytest


