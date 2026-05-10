"""Image-transform pipelines.

Some categories (whitebalance, color_correction) are *transforms* — same input
and output type — so it makes sense to chain several. A `Pipeline` is just an
ordered list of (category, variant) pairs. `apply_pipeline(slot, frame)` walks
the list and applies each in order.

For *single-pick* categories (autofocus, trace_over), don't use a pipeline —
just call `registry.get_active(category)`.

Slots used in this project:
    "live_view"   — applied to frames in the camera/WebRTC stream
    "snapshot"    — applied when saving a snapshot (currently same as live_view)

Each slot's contents survive a hot-reload, since they reference variants by name,
not by function.
"""
from __future__ import annotations

import threading
from typing import Dict, List, Tuple

from . import registry


_PIPELINES: Dict[str, List[Tuple[str, str]]] = {
    # slot -> [(category, variant), ...]
    "live_view": [],
    "snapshot": [],
}
_LOCK = threading.RLock()


def set_pipeline(slot: str, stages: List[Tuple[str, str]]) -> None:
    """Replace the pipeline for `slot`. Validates every stage is registered."""
    for cat, name in stages:
        registry.get(cat, name)  # raises if missing
    with _LOCK:
        _PIPELINES[slot] = list(stages)


def get_pipeline(slot: str) -> List[Tuple[str, str]]:
    with _LOCK:
        return list(_PIPELINES.get(slot, []))


def list_slots() -> List[str]:
    with _LOCK:
        return sorted(_PIPELINES.keys())


def apply_pipeline(slot: str, frame):
    """Apply each stage in the slot's pipeline to `frame`. Stages are looked up
    via the registry on every call, so hot-reload + variant swap take effect
    immediately.

    A bad stage (missing variant or raising) is logged and skipped — never let
    the live view die because of a broken research-mode algorithm.
    """
    from ..logger import Logger  # local import to avoid bootstrap cycle

    with _LOCK:
        stages = list(_PIPELINES.get(slot, []))

    for cat, name in stages:
        try:
            fn = registry.get(cat, name)
            frame = fn(frame)
        except Exception as e:
            Logger.log_error(f"[pipeline:{slot}] {cat}/{name} failed: {e}")
            # Continue with the un-modified frame so the stream stays up.
    return frame


def describe() -> Dict[str, List[Dict[str, str]]]:
    with _LOCK:
        return {
            slot: [{"category": cat, "variant": name} for cat, name in stages]
            for slot, stages in _PIPELINES.items()
        }
