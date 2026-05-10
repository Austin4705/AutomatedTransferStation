"""Filesystem watcher that reloads algorithm modules in place.

Polling-based (no `watchdog` dependency). Walks `algorithms/` once a second
looking for `.py` files whose mtime changed since last poll, then calls
`importlib.reload()` on each.

Reload mechanics that make this work:
  - Each algorithm sits in its own module and registers itself with
    `@algorithm("category", "name")` at import time.
  - On reload, the decorator runs again and overwrites the registry entry.
  - Call sites must look up via `registry.get_active(...)` every call so they
    pick up the new function (no caching of bound references).

Limitations:
  - Module-level state (caches, loaded models) is dropped on reload.
  - Anything that did `from algorithms.foo import Foo` keeps the OLD reference.
  - Native/C extension state should not be hot-reloaded (cameras, SDKs).

Opt in by setting `ATS_ALGO_HOTRELOAD=1` in the env. Off by default so prod
doesn't pay the polling cost.
"""
from __future__ import annotations

import importlib
import os
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from ..logger import Logger


_ALGORITHMS_DIR = Path(__file__).parent
# Files we never want to reload — the framework itself.
_FRAMEWORK_FILES = {"registry.py", "pipeline.py", "hotreload.py", "__init__.py", "protocols.py"}


class _Watcher:
    def __init__(self, interval_seconds: float = 1.0) -> None:
        self.interval = interval_seconds
        self._mtimes: Dict[Path, float] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread is not None:
            return
        # Seed mtimes so we don't reload everything on startup.
        for path in self._iter_files():
            try:
                self._mtimes[path] = path.stat().st_mtime
            except FileNotFoundError:
                pass
        self._thread = threading.Thread(target=self._run, daemon=True, name="algo-hotreload")
        self._thread.start()
        Logger.log(f"[hotreload] watching {_ALGORITHMS_DIR} (interval={self.interval}s)")

    def stop(self) -> None:
        self._stop.set()

    def _iter_files(self):
        for path in _ALGORITHMS_DIR.rglob("*.py"):
            if path.name in _FRAMEWORK_FILES:
                continue
            if "__pycache__" in path.parts:
                continue
            yield path

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            for path in self._iter_files():
                try:
                    mtime = path.stat().st_mtime
                except FileNotFoundError:
                    self._mtimes.pop(path, None)
                    continue
                prev = self._mtimes.get(path)
                if prev is None or mtime > prev:
                    self._mtimes[path] = mtime
                    if prev is not None:
                        # Only reload — first sighting is just the seed.
                        self._reload(path)

    def _reload(self, path: Path) -> None:
        module_name = self._path_to_module(path)
        if module_name is None:
            return
        mod = sys.modules.get(module_name)
        try:
            if mod is None:
                importlib.import_module(module_name)
                Logger.log(f"[hotreload] imported {module_name}")
            else:
                importlib.reload(mod)
                Logger.log(f"[hotreload] reloaded {module_name}")
        except Exception as e:
            Logger.log_error(f"[hotreload] failed to reload {module_name}: {e}")

    @staticmethod
    def _path_to_module(path: Path) -> Optional[str]:
        try:
            rel = path.relative_to(_ALGORITHMS_DIR)
        except ValueError:
            return None
        parts = list(rel.with_suffix("").parts)
        return "ats.algorithms." + ".".join(parts) if parts else None


_singleton: Optional[_Watcher] = None


def start_if_enabled() -> None:
    """Start the watcher iff `ATS_ALGO_HOTRELOAD=1`."""
    global _singleton
    if os.getenv("ATS_ALGO_HOTRELOAD", "0") != "1":
        return
    if _singleton is None:
        _singleton = _Watcher(interval_seconds=float(os.getenv("ATS_ALGO_HOTRELOAD_INTERVAL", "1.0")))
        _singleton.start()


def stop() -> None:
    if _singleton is not None:
        _singleton.stop()
