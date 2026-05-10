"""Canny edge count — fast, robust focus metric on textured samples.

Returns the number of pixels with significant edge response after a Canny
filter. Higher = more in-focus on textured imagery.
"""
import cv2
import numpy as np

from ..registry import algorithm


@algorithm("focus_metric", "canny_edges")
def canny_edge_count(image) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return float(np.sum(edges > 30))
