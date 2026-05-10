"""Coarse + fine autofocus.

Sweeps z, samples a focus metric at each step, picks the best, then refines
via a Gaussian fit on the combined samples. The focus metric and the scene
filter (e.g. "is this on substrate?") are both looked up from the registry on
each call, so swapping either picks up live.

Pure procedure on top of `Stage` + `FrameSource` — no Logger, no
threading.Event. Cancellation and logging are passed in as plain callables.
"""
from typing import Callable, List, Tuple

from ..focus_metric.color_features import has_color_features
from ..gaussian_fit import fit_peak
from ..protocols import FrameSource, Stage
from ..registry import algorithm, get_active

_NOOP_LOG: Callable[[str], None] = lambda _msg: None
_ALWAYS_CONTINUE: Callable[[], bool] = lambda: True


@algorithm("autofocus", "coarse_fine")
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
    log("Auto Focus")
    frame = frames.get_frame()

    if not has_color_features(frame):
        log("No color features exist")
        return

    # Resolve once per call so a hot-swap of the metric mid-scan is safe.
    focus_metric = get_active("focus_metric")

    original_score = focus_metric(frame)
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
            score = focus_metric(frames.get_frame())
            z_pos = -z_range / 2 + (i * z_step)
            local.append((score, z_pos))
            samples.append((score, z_pos))
        best = max(local, key=lambda pt: pt[0])
        log(f"Best in scan: score={best[0]}, z={best[1]:.5f}")
        if best[0] == 0:
            return -z_range / 2
        return -z_range / 2 + best[1]

    if original_score == 0:
        log("Original focus score is 0; running coarse scan")
        best_coarse = _scan(z_range_coarse, n_samples_coarse)
        stage.moveZRel(best_coarse)
    else:
        log(f"Original focus score = {original_score}; skipping coarse scan")

    _scan(z_range_fine, n_samples_fine)

    best_fine = fit_peak(samples)
    if best_fine is None:
        log("Gaussian fit failed or all scores are 0; not adjusting z")
        best_fine = 0.0
    else:
        log(f"Gaussian peak at z={best_fine:.5f}")

    offset = -z_range_fine / 2 + z_range_fine / n_samples_fine
    stage.moveZRel(best_fine + offset)
    log(f"All samples: {samples}")
