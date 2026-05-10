"""Color-feature ratio — fraction of pixels above a saturation threshold.

Used as a *scene quality* check: if there's almost no colorful content, the
frame is probably looking at bare metal or off-substrate, and texture-based
focus metrics will be meaningless.
"""
import cv2
import numpy as np

from ..registry import algorithm


@algorithm("focus_metric", "color_ratio")
def color_ratio(image, saturation_threshold: int = 40) -> float:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    colorful = int(np.count_nonzero(sat > saturation_threshold))
    total = image.shape[0] * image.shape[1]
    return colorful / max(total, 1)


def has_color_features(image, ratio_threshold: float = 0.05) -> bool:
    """Convenience wrapper used by autofocus to skip off-substrate frames."""
    return color_ratio(image) >= ratio_threshold
