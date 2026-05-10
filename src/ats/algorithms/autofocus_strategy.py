"""Coarse + fine autofocus strategy.

Sweeps z, measures edge count at each step, picks the z that maximizes
edges, refines via a Gaussian fit on the combined samples.

Pure procedure on top of `Stage` + `FrameSource` — no Logger, no
threading.Event. Cancellation and logging are passed in as plain callables
so the algorithm has no hidden dependencies and is trivially testable.
"""
from typing import Callable, List, Tuple

from .autofocus import Autofocus
from .gaussian_fit import fit_peak
from .protocols import FrameSource, Stage

_NOOP_LOG: Callable[[str], None] = lambda _msg: None
_ALWAYS_CONTINUE: Callable[[], bool] = lambda: True


def coarse_fine_autofocus(
    stage: Stage,
    frames: FrameSource,
    *,
    n_samples_coarse: int = 20,
    n_samples_fine: int = 20,
    z_range_coarse: float = 0.5,
    z_range_fine: float = 0.1,
    should_continue: Callable[[], bool] = _ALWAYS_CONTINUE,
    log: Callable[[str], None] = _NOOP_LOG,
) -> None:
    """Move the stage to the z that maximizes detected edges.

    Strategy:
      1. If the current frame has no color features, abort early (nothing
         to focus on — likely off the substrate).
      2. If the current edge count is zero, do a coarse scan and jump near
         the resulting peak. Otherwise skip the coarse pass.
      3. Do a fine scan around the (now-better) z.
      4. Fit a Gaussian to the *combined* coarse+fine samples and move to
         the fitted peak. If the fit fails or all samples are zero, leave
         z where the fine scan put it.

    Mutates the stage; returns None. The samples list is internal —
    diagnostic output is emitted through `log`.
    """
    log("Auto Focus")
    frame = frames.get_frame()

    if not Autofocus.exist_color_features(frame):
        log("No color features exist")
        return

    original_edge_count = Autofocus.get_edge_count(frame)
    samples: List[Tuple[float, float]] = []

    def _scan(z_range: float, n_samples: int) -> float:
        local: List[Tuple[float, float]] = []
        log(f"Scanning z range {z_range:.4f} ({n_samples} samples)")
        stage.moveZRel(-z_range / 2)
        stage.wait(1.25)
        z_step = z_range / n_samples
        for i in range(n_samples):
            if not should_continue():
                return 0.0
            stage.moveZRel(z_step)
            edge_count = Autofocus.get_edge_count(frames.get_frame())
            z_pos = -z_range / 2 + (i * z_step)
            local.append((edge_count, z_pos))
            samples.append((edge_count, z_pos))
        best = max(local, key=lambda pt: pt[0])
        log(f"Best in scan: edges={best[0]}, z={best[1]:.5f}")
        if best[0] == 0:
            return -z_range / 2
        return -z_range / 2 + best[1]

    if original_edge_count == 0:
        log("Original edge count is 0; running coarse scan")
        best_coarse = _scan(z_range_coarse, n_samples_coarse)
        stage.moveZRel(best_coarse)
    else:
        log(f"Original edge count = {original_edge_count}; skipping coarse scan")

    _scan(z_range_fine, n_samples_fine)

    best_fine = fit_peak(samples)
    if best_fine is None:
        log("Gaussian fit failed or all edge counts are 0; not adjusting z")
        best_fine = 0.0
    else:
        log(f"Gaussian peak at z={best_fine:.5f}")

    offset = -z_range_fine / 2 + z_range_fine / n_samples_fine
    stage.moveZRel(best_fine + offset)
    log(f"All edge samples: {samples}")
