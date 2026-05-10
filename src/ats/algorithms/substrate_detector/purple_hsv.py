"""Purple-SiO2 substrate detector via HSV thresholding.

Returns (passed, stats). `passed` is True when a sufficient fraction of the
central image region falls in the violet/magenta hue band with enough
saturation. Used to gate autofocus during a raster scan — there's no point
running edge-based focus on bare-metal regions.
"""
import cv2
import numpy as np

from ..registry import algorithm


@algorithm("substrate_detector", "purple_hsv")
def is_substrate_background_purple_hsv(
    image,
    hue_range=(110, 170),
    min_saturation: int = 30,
    min_purple_fraction: float = 0.4,
    sample_fraction: float = 0.5,
):
    h, w = image.shape[:2]
    margin_y = int(h * (1 - sample_fraction) / 2)
    margin_x = int(w * (1 - sample_fraction) / 2)
    roi = image[margin_y:h - margin_y, margin_x:w - margin_x]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0].ravel().astype(np.float32)
    sat = hsv[:, :, 1].ravel().astype(np.float32)

    saturated = sat >= min_saturation
    in_hue = (hue >= hue_range[0]) & (hue <= hue_range[1])
    purple_mask = saturated & in_hue

    n_total = len(hue)
    n_purple = int(purple_mask.sum())
    purple_frac = n_purple / max(n_total, 1)

    stats = {
        "median_hue": float(np.median(hue)),
        "median_saturation": float(np.median(sat)),
        "purple_fraction": round(purple_frac, 4),
        "n_pixels_sampled": n_total,
        "passed": purple_frac >= min_purple_fraction,
    }
    return stats["passed"], stats
