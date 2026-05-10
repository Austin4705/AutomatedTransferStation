"""Raster scan over a sample, with adaptive autofocus.

Walks a serpentine grid of (x, y) points, captures a frame at each one, and
decides whether to re-run autofocus based on the substrate-background check
and focus score. Both the focus metric and the substrate detector are looked
up via the registry on every call, so swapping them takes effect mid-scan.

Pure procedure on top of `Stage` + `FrameSource` + caller-supplied callbacks.
Storage I/O, logging, and cancellation are injected.
"""
import time
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from ..path_planning import serpentine_grid
from ..protocols import FrameSource, Stage
from ..registry import algorithm, get_active

_NOOP_LOG: Callable[[str], None] = lambda _msg: None
_ALWAYS_CONTINUE: Callable[[], bool] = lambda: True
_NOOP_AUTOFOCUS: Callable[[], None] = lambda: None


@dataclass
class FrameSnapshot:
    """One captured frame, plus metadata computed for the autofocus decision."""
    image: np.ndarray
    x: float
    y: float
    sequence: int
    is_substrate_background: bool
    focus_score: float


def _should_autofocus(
    *,
    is_substrate_background: bool,
    focus_score: float,
    prev_was_not_substrate: bool,
    score_threshold: float = 10.0,
) -> bool:
    """Re-focus when on substrate AND (focus is poor OR we just re-entered substrate)."""
    if not is_substrate_background:
        return False
    return focus_score < score_threshold or prev_was_not_substrate


@algorithm("trace_over", "serpentine")
def trace_over_serpentine(
    *,
    start_x: float,
    end_x: float,
    start_y: float,
    end_y: float,
    start_z: float,
    step_x: float,
    step_y: float,
    initial_settle_time: float,
    point_settle_time: float,
    stage: Stage,
    frames: FrameSource,
    autofocus: Callable[[], None] = _NOOP_AUTOFOCUS,
    initial_autofocus: Optional[Callable[[], None]] = None,
    on_frame: Callable[[FrameSnapshot], None] = lambda _snap: None,
    should_continue: Callable[[], bool] = _ALWAYS_CONTINUE,
    log: Callable[[str], None] = _NOOP_LOG,
    score_threshold: float = 10.0,
) -> None:
    points = serpentine_grid(start_x, end_x, start_y, end_y, step_x, step_y)
    log(f"Trace over: {len(points)} points planned")

    # Resolve once per call — picks up the latest variant on every scan run.
    focus_metric = get_active("focus_metric")
    substrate_detect = get_active("substrate_detector")

    stage.moveXY(start_x, start_y)
    stage.moveZ(start_z)
    stage.wait(initial_settle_time)
    if initial_autofocus is not None:
        initial_autofocus()

    prev_was_not_substrate = False

    for sequence, (x, y) in enumerate(points, start=1):
        if not should_continue():
            log("Trace over cancelled during execution")
            return
        time.sleep(0.01)

        stage.moveXY(x, y)
        stage.wait(point_settle_time)
        image = frames.get_frame()
        is_background, _bg_stats = substrate_detect(image)
        focus_score = focus_metric(image)

        if _should_autofocus(
            is_substrate_background=is_background,
            focus_score=focus_score,
            prev_was_not_substrate=prev_was_not_substrate,
            score_threshold=score_threshold,
        ):
            log(f"Autofocusing - is_background={is_background}, focus_score={focus_score}, "
                f"prev_was_not_substrate={prev_was_not_substrate}")
            autofocus()
        elif not is_background:
            log("Skipping autofocus - not substrate background")
        prev_was_not_substrate = not is_background

        on_frame(FrameSnapshot(
            image=image,
            x=x,
            y=y,
            sequence=sequence,
            is_substrate_background=is_background,
            focus_score=focus_score,
        ))
