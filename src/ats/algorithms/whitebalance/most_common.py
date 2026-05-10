"""Most-common-color whitebalance.

Quantize the image into 8-step color buckets, find the most common (above a
brightness threshold), and rescale R/G/B so that color becomes neutral grey.
Intended for microscope frames where the background dominates and represents
the substrate's actual color.
"""
import numpy as np

from ..registry import algorithm


@algorithm("whitebalance", "most_common")
def whitebalance_most_common(image):
    result = image.astype(np.float32)
    quantized = (image // 8) * 8
    brightness = quantized.sum(axis=2)
    mask = brightness > 30
    filtered = quantized[mask]

    if filtered.size == 0:
        return image

    colors_as_int = (
        (filtered[:, 0].astype(np.int32) << 16)
        | (filtered[:, 1].astype(np.int32) << 8)
        | filtered[:, 2].astype(np.int32)
    )
    counts = np.bincount(colors_as_int)
    most_common_int = np.argmax(counts)

    color = np.array([
        (most_common_int >> 16) & 0xFF,
        (most_common_int >> 8) & 0xFF,
        most_common_int & 0xFF,
    ], dtype=np.float32)

    avg_gray = (color[0] + color[1] + color[2]) / 3.0
    scale_r = avg_gray / color[0] if color[0] > 0 else 1.0
    scale_g = avg_gray / color[1] if color[1] > 0 else 1.0
    scale_b = avg_gray / color[2] if color[2] > 0 else 1.0

    result[:, :, 0] *= scale_r
    result[:, :, 1] *= scale_g
    result[:, :, 2] *= scale_b
    return np.clip(result, 0, 255).astype(np.uint8)
