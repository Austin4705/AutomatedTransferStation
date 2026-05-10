"""Algorithm registry + hot-swappable variants.

Importing this package eagerly imports every variant module under
`algorithms/<category>/` so their `@algorithm(...)` decorators run and the
registry is fully populated at startup.

To add a new variant:
    1. Drop a file at `algorithms/<category>/<variant>.py`
    2. Inside, register a top-level callable:
           @algorithm("<category>", "<variant>")
           def my_variant(...): ...
    3. (Optional) `set_active("<category>", "<variant>")` to make it default
       at startup. Otherwise the first registered variant wins.

With `ATS_ALGO_HOTRELOAD=1`, edits to variant files are picked up live.
"""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from . import pipeline, registry  # re-exports
from .registry import algorithm, get, get_active, get_active_name, set_active  # noqa: F401


_FRAMEWORK_MODULES = {"registry", "pipeline", "hotreload", "protocols"}


def _discover_variants() -> None:
    """Eagerly import every subpackage / submodule under `algorithms/`.

    Each variant lives in either:
        algorithms/<category>/<variant>.py    (preferred)
        algorithms/<category>/__init__.py     (with @algorithm decorators inline)
    """
    pkg_path = Path(__file__).parent
    # Top-level submodules (legacy: autofocus.py, cv_functions.py, etc. — left in
    # place but the framework only auto-imports subpackages, not flat files, to
    # avoid pulling in legacy modules that the new code shouldn't rely on).
    for entry in pkg_path.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("_") or entry.name in _FRAMEWORK_MODULES:
            continue
        category_pkg = f"ats.algorithms.{entry.name}"
        try:
            importlib.import_module(category_pkg)
        except Exception as e:
            from ..logger import Logger
            Logger.log_error(f"[algorithms] failed to import {category_pkg}: {e}")
            continue
        # Import each variant file inside the category package.
        for _, name, _ in pkgutil.iter_modules([str(entry)]):
            mod = f"{category_pkg}.{name}"
            try:
                importlib.import_module(mod)
            except Exception as e:
                from ..logger import Logger
                Logger.log_error(f"[algorithms] failed to import {mod}: {e}")


_discover_variants()


def configure_default_pipelines() -> None:
    """Apply the project's default pipeline assignments.

    Called from `__main__` after registry discovery so any user override via
    SET_ALGORITHM_PIPELINE remains in force across the rest of the run.
    """
    # Live view: identity by default. Flip to whitebalance/grayworld via WS.
    pipeline.set_pipeline("live_view", [("whitebalance", "identity")])
    pipeline.set_pipeline("snapshot", [("whitebalance", "identity")])
