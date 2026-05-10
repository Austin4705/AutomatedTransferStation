"""Hot-swappable algorithm registry.

Each algorithm is a plain Python callable annotated with `@algorithm(category, name)`.
The registry stores them keyed by (category, name) and tracks which variant is
currently *active* per category. Call sites should always go through `get_active`
or `apply` so a hot-reload picks up the new variant immediately.

Categories used in this project (seeded in pipeline.py):
    whitebalance       (frame) -> frame
    color_correction   (frame) -> frame
    focus_metric       (frame) -> float
    substrate_detector (frame) -> (bool, dict)
    autofocus          (stage, frames, **opts) -> None
    trace_over         (**opts) -> None

Adding a new variant: drop a file in algorithms/<category>/<name>.py that calls
@algorithm("<category>", "<name>") on a top-level function. With the hot-reload
watcher running, saving the file makes the variant available immediately.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class _Entry:
    fn: Callable[..., Any]
    doc: str = ""
    module: str = ""


# (category, name) -> entry
_REGISTRY: Dict[tuple, _Entry] = {}
# category -> active variant name
_ACTIVE: Dict[str, str] = {}
# category -> default variant name (set on first registration unless already set)
_DEFAULTS: Dict[str, str] = {}
# category -> list of (callback, *args) invoked whenever the registry changes for
# that category. Used by pipeline / UI to refresh.
_LISTENERS: Dict[str, List[Callable[[], None]]] = {}

_LOCK = threading.RLock()


def algorithm(category: str, name: str) -> Callable:
    """Decorator: register `fn` as variant `name` of `category`.

    Re-registering an existing (category, name) overwrites — this is what makes
    hot-reload work: the module is reloaded, decorators run again, the new
    function replaces the old entry.
    """
    def decorator(fn: Callable) -> Callable:
        with _LOCK:
            _REGISTRY[(category, name)] = _Entry(
                fn=fn,
                doc=(fn.__doc__ or "").strip(),
                module=fn.__module__,
            )
            # First registered variant in a category becomes the default + active.
            if category not in _DEFAULTS:
                _DEFAULTS[category] = name
                _ACTIVE.setdefault(category, name)
            _notify(category)
        return fn
    return decorator


def get(category: str, name: str) -> Callable:
    with _LOCK:
        entry = _REGISTRY.get((category, name))
        if entry is None:
            raise KeyError(f"Algorithm not registered: {category}/{name}")
        return entry.fn


def get_active(category: str) -> Callable:
    """Return the currently-active variant for `category`. Raises if none registered."""
    with _LOCK:
        name = _ACTIVE.get(category)
        if name is None:
            raise KeyError(f"No active variant for category: {category}")
        return get(category, name)


def get_active_name(category: str) -> Optional[str]:
    with _LOCK:
        return _ACTIVE.get(category)


def set_active(category: str, name: str) -> None:
    with _LOCK:
        if (category, name) not in _REGISTRY:
            raise KeyError(f"Algorithm not registered: {category}/{name}")
        _ACTIVE[category] = name
        _notify(category)


def list_categories() -> List[str]:
    with _LOCK:
        return sorted({cat for cat, _ in _REGISTRY.keys()})


def list_variants(category: str) -> List[str]:
    with _LOCK:
        return sorted(name for cat, name in _REGISTRY.keys() if cat == category)


def describe() -> Dict[str, Any]:
    """Snapshot of the whole registry — useful for the LIST_ALGORITHMS packet."""
    with _LOCK:
        out: Dict[str, Any] = {"categories": {}}
        for cat in list_categories():
            out["categories"][cat] = {
                "active": _ACTIVE.get(cat),
                "default": _DEFAULTS.get(cat),
                "variants": [
                    {
                        "name": name,
                        "doc": _REGISTRY[(cat, name)].doc,
                        "module": _REGISTRY[(cat, name)].module,
                    }
                    for name in list_variants(cat)
                ],
            }
        return out


def on_change(category: str, callback: Callable[[], None]) -> Callable[[], None]:
    """Register a listener fired whenever `category` changes (new variant, swap)."""
    with _LOCK:
        _LISTENERS.setdefault(category, []).append(callback)

    def unsubscribe() -> None:
        with _LOCK:
            listeners = _LISTENERS.get(category, [])
            if callback in listeners:
                listeners.remove(callback)
    return unsubscribe


def _notify(category: str) -> None:
    # Caller holds _LOCK. Snapshot listeners then release before invoking.
    listeners = list(_LISTENERS.get(category, []))
    for cb in listeners:
        try:
            cb()
        except Exception:
            pass
