import cv2
from GMMDetector import MaterialDetector
import numpy as np
import matplotlib.cm as cm
import json

class CV_Functions:

    def __init__(self) -> None:
        pass
        # self.mockImage = np.zeros((512, 512, 3), dtype=np.uint8)
        # CV_Functions.matGMM2DTransform(self.mockImage)

    def whitebalance(image):
        # return image
        result = image.astype(np.float32)
        quantized = (image // 8) * 8
        brightness = quantized.sum(axis=2)
        mask = brightness > 30
        filtered = quantized[mask]
        
        colors_as_int = (filtered[:, 0].astype(np.int32) << 16) | (filtered[:, 1].astype(np.int32) << 8) | filtered[:, 2].astype(np.int32)
        
        counts = np.bincount(colors_as_int)
        most_common_int = np.argmax(counts)
        
        color = np.array([
            (most_common_int >> 16) & 0xFF,
            (most_common_int >> 8) & 0xFF,
            most_common_int & 0xFF
        ], dtype=np.float32)
        
        avg_gray = (color[0] + color[1] + color[2]) / 3.0
        scale_r = avg_gray / color[0] if color[0] > 0 else 1.0
        scale_g = avg_gray / color[1] if color[1] > 0 else 1.0
        scale_b = avg_gray / color[2] if color[2] > 0 else 1.0
        # print(f"Most common color: RGB({color[0]}, {color[1]}, {color[2]})")
        # print(f"Scale factors: R={scale_r:.3f}, G={scale_g:.3f}, B={scale_b:.3f}")
        result[:, :, 0] *= scale_r
        result[:, :, 1] *= scale_g
        result[:, :, 2] *= scale_b

        result = np.clip(result, 0, 255)
        return result.astype(np.uint8)


    def whitebalance_greyworld(image):
        # Grayworld method
        result = image.astype(np.float32)
        avg_r = np.mean(result[:, :, 0])
        avg_g = np.mean(result[:, :, 1])
        avg_b = np.mean(result[:, :, 2])
        avg_gray = (avg_r + avg_g + avg_b) / 3.0

        scale_r = avg_gray / avg_r if avg_r > 0 else 1.0
        scale_g = avg_gray / avg_g if avg_g > 0 else 1.0
        scale_b = avg_gray / avg_b if avg_b > 0 else 1.0

        result[:, :, 0] *= scale_r
        result[:, :, 1] *= scale_g
        result[:, :, 2] *= scale_b

        result = np.clip(result, 0, 255)
        return result.astype(np.uint8)
    

    def line_rgb_values(image: np.ndarray, start, end):
        """
        Given an image (H, W, 3) and start=(x0,y0), end=(x1,y1),
        return RGB values along the line connecting them.
        """
        x0, y0 = start
        x1, y1 = end
        num_points = int(np.hypot(x1 - x0, y1 - y0)) + 1
        x, y = np.linspace(x0, x1, num_points), np.linspace(y0, y1, num_points)
        x, y = np.round(x).astype(int), np.round(y).astype(int)
        # Clip to image bounds
        x = np.clip(x, 0, image.shape[1] - 1)
        y = np.clip(y, 0, image.shape[0] - 1)
        rgb = image[y, x]
        return rgb

    def generate_brightness_line(image: np.ndarray, start, end):
        rgb = line_rgb_values(image, start, end)
        # NTSC Coefficients for brightness
        brightness = 0.299 * rgb[:,0] + 0.587 * rgb[:,1] + 0.114 * rgb[:,2]
        return brightness

    def is_substrate_background(
        image,
        hue_range=(110, 170),
        min_saturation=30,
        min_purple_fraction=0.4,
        sample_fraction=0.5,
    ):
        """Check whether the image background is a purple SiO2 substrate.

        Returns True when the majority of the central region has purple hue
        with sufficient saturation (i.e. good for flake hunting).  Returns
        False for grey / brown bare-metal backgrounds.

        Args:
            image: BGR uint8 image (OpenCV format).
            hue_range: (lo, hi) acceptable hue in OpenCV 0-180 scale.
                        Default (110, 170) covers violet through magenta.
            min_saturation: pixels below this S value are considered grey.
            min_purple_fraction: fraction of sampled pixels that must be
                                    purple for the image to pass.
            sample_fraction: fraction of the image (centred) to sample,
                                avoids vignetting at edges.

        Returns:
            (bool, dict) – pass/fail and diagnostic stats.
        """
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
