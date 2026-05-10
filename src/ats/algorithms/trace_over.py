"""Raster scan over a sample, with adaptive autofocus.

Walks a serpentine grid of (x, y) points, captures a frame at each one,
and decides whether to re-run autofocus based on the substrate-background
check and edge count.

Pure procedure on top of `Stage` + `FrameSource` + caller-supplied
callbacks. Storage I/O, logging, and cancellation are injected — this
module only contains the scan logic.
"""
import time
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from .autofocus import Autofocus
from .autofocus_trigger import should_autofocus
from .cv_functions import CV_Functions
from .path_planning import serpentine_grid
from .protocols import FrameSource, Stage

_NOOP_LOG: Callable[[str], None] = lambda _msg: None
_ALWAYS_CONTINUE: Callable[[], bool] = lambda: True
_NOOP_AUTOFOCUS: Callable[[], None] = lambda: None


@dataclass
class FrameSnapshot:
    """One captured frame, plus the metadata computed for the autofocus decision."""

    image: np.ndarray
    x: float
    y: float
    sequence: int                # 1-based index in visit order
    is_substrate_background: bool
    edge_count: int


def trace_over(
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
    edge_threshold: int = 10,
) -> None:
    """Raster-scan from (start_x, start_y) to (end_x, end_y) at z = start_z.

    Per point: move XY, settle, capture, classify substrate, decide whether
    to autofocus, emit a `FrameSnapshot` to the caller's `on_frame`. The
    caller decides what to do with each snapshot (store it, render it,
    discard it).

    Cancellation is checked before each point — pass `should_continue` that
    returns False to abort. `initial_autofocus` runs once after the initial
    XYZ move and settle; `autofocus` runs on demand during the scan.
    """
    points = serpentine_grid(start_x, end_x, start_y, end_y, step_x, step_y)
    log(f"Trace over: {len(points)} points planned")

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
        # Brief yield between iterations.
        time.sleep(0.01)

        stage.moveXY(x, y)
        stage.wait(point_settle_time)
        image = frames.get_frame()
        is_background, _bg_stats = CV_Functions.is_substrate_background(image)
        edge_count = Autofocus.get_edge_count(image)

        if should_autofocus(
            is_substrate_background=is_background,
            edge_count=edge_count,
            prev_was_not_substrate=prev_was_not_substrate,
            edge_threshold=edge_threshold,
        ):
            log(f"Autofocusing - is_background={is_background}, edge_count={edge_count}, "
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
            edge_count=edge_count,
        ))
