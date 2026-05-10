"""Laplacian variance — classic focus metric.

Variance of a Laplacian filter applied to a Gaussian-blurred frame. Higher
variance = more edge contrast = more in-focus.
"""
import cv2

from ..registry import algorithm


@algorithm("focus_metric", "laplacian_variance")
def laplacian_variance(image) -> float:
    blurred = cv2.GaussianBlur(image, (9, 9), 0)
    laplacian = cv2.Laplacian(blurred, cv2.CV_64F)
    return float(laplacian.var())
