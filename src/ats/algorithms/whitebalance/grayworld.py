"""Grayworld whitebalance — assumes the average of the scene is neutral grey."""
import numpy as np

from ..registry import algorithm


@algorithm("whitebalance", "grayworld")
def whitebalance_grayworld(image):
    result = image.astype(np.float32)
    avg_r = float(np.mean(result[:, :, 0]))
    avg_g = float(np.mean(result[:, :, 1]))
    avg_b = float(np.mean(result[:, :, 2]))
    avg_gray = (avg_r + avg_g + avg_b) / 3.0

    scale_r = avg_gray / avg_r if avg_r > 0 else 1.0
    scale_g = avg_gray / avg_g if avg_g > 0 else 1.0
    scale_b = avg_gray / avg_b if avg_b > 0 else 1.0

    result[:, :, 0] *= scale_r
    result[:, :, 1] *= scale_g
    result[:, :, 2] *= scale_b
    return np.clip(result, 0, 255).astype(np.uint8)
