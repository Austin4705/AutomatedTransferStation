"""CPBD (Cumulative Probability of Blur Detection) — perceptual blur metric.

Slower than Laplacian/Canny but less sensitive to scene content. Useful for
substrate-only frames where texture-based metrics give zero. Requires the
optional `cpbd` package (pip install cpbd).
"""
import cv2

from ..registry import algorithm


@algorithm("focus_metric", "cpbd")
def cpbd_metric(image) -> float:
    import cpbd  # optional dep — lazy import keeps prod install lean
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    return float(cpbd.compute(gray))
