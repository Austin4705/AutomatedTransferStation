import cv2
import os
import random
import matplotlib.pyplot as plt
import json
import threading
import numpy as np
import matplotlib.cm as cm
from pathlib import Path
from scipy.interpolate import interp1d
from skimage import color, segmentation, measure, morphology, filters
from sklearn.cluster import KMeans
import pandas as pd
import os

class FlinderDetector:
    """Flinder-style flake detection with KBGR channel masking."""

    def __init__(self, config=None, debug=False):
        self.debug = debug
        self.config = config
        self._background = None
        if config is not None:
            for key, value in config.items():
                if isinstance(value, dict) and key in self.config and isinstance(self.config[key], dict):
                    self.config[key].update(value)
                else:
                    self.config[key] = value

    # ── Vignetting / flat-field correction ───────────────────────────────

    @staticmethod
    def compute_background(image_paths, n_sample=100, target_value=127.5):
        """Build a per-pixel background model from the median of sampled images.

        Most pixels in a wafer scan are bare substrate, so the pixel-wise
        median across many images captures the illumination profile
        (including vignetting, uneven lighting, etc.).

        Args:
            image_paths: list of Path or str to images in a collection.
            n_sample: how many images to sample (more = more accurate, slower).
            target_value: the neutral gray value to normalize to.

        Returns:
            background (np.float32 H x W x 3): per-pixel background model.
        """
        paths = list(image_paths)
        if len(paths) == 0:
            raise ValueError("No image paths provided for background computation")
        sample = random.sample(paths, min(n_sample, len(paths)))

        first = cv2.imread(str(sample[0]), cv2.IMREAD_COLOR)
        if first is None:
            raise ValueError(f"Could not read image: {sample[0]}")
        h, w = first.shape[:2]

        stack = np.zeros((len(sample), h, w, 3), dtype=np.uint8)
        valid = 0
        for i, p in enumerate(sample):
            img = cv2.imread(str(p), cv2.IMREAD_COLOR)
            if img is not None and img.shape[:2] == (h, w):
                stack[valid] = img
                valid += 1
        stack = stack[:valid]

        background = np.median(stack, axis=0).astype(np.float32)
        return background

    @staticmethod
    def correct_vignetting(image, background, target_value=127.5):
        """Correct vignetting by dividing by the per-pixel background.

        For each channel at each pixel: corrected = (pixel / background) * target.
        Then re-center so the histogram peak sits at target_value.

        Args:
            image: BGR uint8 image.
            background: float32 H x W x 3 background from compute_background().
            target_value: neutral gray level to normalize to.

        Returns:
            corrected BGR uint8 image.
        """
        img_f = image.astype(np.float32)
        safe_bg = np.maximum(background, 1.0)
        corrected = img_f / safe_bg * target_value

        for ch in range(3):
            channel = corrected[:, :, ch]
            vals = channel[(channel > 10) & (channel < 245)]
            if len(vals) > 0:
                bins = np.arange(50, 200, 0.5)
                hist, _ = np.histogram(vals, bins=bins)
                peak = bins[np.argmax(hist)]
                if peak > 10:
                    channel[:] = channel / peak * target_value
            corrected[:, :, ch] = channel

        return np.clip(corrected, 0, 255).astype(np.uint8)

    def set_background(self, background):
        """Store a precomputed background for use in detect/detect_flakes."""
        self._background = background

    def clear_background(self):
        """Clear the stored background model."""
        self._background = None

    def preprocess_image(self, image):
        """Apply vignetting correction if a background model is set."""
        if self._background is not None:
            return self.correct_vignetting(image, self._background)
        return image

    # ── Channel extraction ──────────────────────────────────────────────

    @staticmethod
    def extract_kbgr(image):
        """Extract K (gray), B, G, R channels from BGR image."""
        b, g, r = cv2.split(image)
        k = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return k.astype("uint8"), b.astype("uint8"), g.astype("uint8"), r.astype("uint8")

    # ── Calibration → mask values (Flinder interp pipeline) ─────────────

    @staticmethod
    def _find_minmax_segment(thickness, cal, tmin, tmax, error):
        """Min-error / max+error over a thickness segment (interp1d).
        Single-point degrades to value +/- error."""
        thickness = np.array(thickness, dtype=float)
        cal = np.array(cal, dtype=float)
        error = np.array(error, dtype=float)
        if len(thickness) == 1:
            return int(np.round(cal[0] - error[0])), int(np.round(cal[0] + error[0]))
        t_temp = np.linspace(tmin, tmax, 10000)
        cal_i = interp1d(thickness, cal)(t_temp)
        err_i = interp1d(thickness, error)(t_temp)
        mask = (t_temp > tmin) & (t_temp < tmax)
        if mask.sum() == 0:
            mask = np.ones_like(t_temp, dtype=bool)
        cal_i, err_i = cal_i[mask], err_i[mask]
        cal_min = np.min(cal_i) - err_i[np.argmin(cal_i)]
        cal_max = np.max(cal_i) + err_i[np.argmax(cal_i)]
        return int(np.round(cal_min)), int(np.round(cal_max))

    @staticmethod
    def compute_mask_values(calibration):
        """Compute mask-value dicts from a calibration dict.

        calibration keys: 'thickness', 'k','b','g','r',
            'k_error','b_error','g_error','r_error', 'number_of_intervals'
        Returns: list of dicts  [{'k':{'min':..,'max':..}, ...}, ...]
        """
        thickness = np.array(calibration["thickness"], dtype=float)
        n = int(calibration.get("number_of_intervals", 1))
        segs = np.linspace(thickness.min(), thickness.max(), n + 1)
        out = []
        for i in range(n):
            iv = {}
            for ch in ["k", "b", "g", "r"]:
                lo, hi = FlinderDetector._find_minmax_segment(
                    thickness, calibration[ch], segs[i], segs[i + 1], calibration[f"{ch}_error"]
                )
                iv[ch] = {"min": lo, "max": hi}
            out.append(iv)
        return out

    # ── Single-channel mask (Flinder double-threshold) ──────────────────

    def create_mask(self, channel, lmin, lmax):
        sq = self.config.get("blur_size", 5)
        blurred = cv2.blur(channel, (sq, sq)).astype("uint8")
        _, b1 = cv2.threshold(blurred, lmin, 255, cv2.THRESH_BINARY_INV)
        _, b2 = cv2.threshold(blurred, lmax, 255, cv2.THRESH_BINARY_INV)
        return b1 - b2

    # ── Combined KBGR mask (Flinder make_selection) ─────────────────────

    def make_selection(self, k, b, g, r, mask_values):
        use = self.config["use_channels"]
        gray_mask = self.create_mask(k, mask_values["k"]["min"], mask_values["k"]["max"]) if use.get("k") else self.create_mask(k, 0, 255)
        for ch, img in [("b", b), ("g", g), ("r", r)]:
            if use.get(ch):
                m = self.create_mask(img, mask_values[ch]["min"], mask_values[ch]["max"])
                gray_mask[m < 0.5] = 0
        gray_mask = cv2.medianBlur(gray_mask, self.config.get("mask_median_blur_size", 5))
        return gray_mask

    def make_channel_masks(self, k, b, g, r, mask_values):
        """Return dict of individual channel masks for visualization."""
        use = self.config["use_channels"]
        ch_imgs = {"k": k, "b": b, "g": g, "r": r}
        return {ch: self.create_mask(ch_imgs[ch], mask_values[ch]["min"], mask_values[ch]["max"])
                for ch in ["k", "b", "g", "r"] if use.get(ch)}

    # ── Contour finding ─────────────────────────────────────────────────

    def find_contours_in_mask(self, mask, min_area=100):
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return [c for c in contours if cv2.contourArea(c) > min_area]

    # ── Contour statistics ──────────────────────────────────────────────

    def calculate_contour_statistics(self, contour, k, b, g, r):
        mask = np.zeros(k.shape, np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
        kv, bv, gv, rv = k[mask > 0.5], b[mask > 0.5], g[mask > 0.5], r[mask > 0.5]
        area = max(cv2.contourArea(contour), 1)
        perim = max(cv2.arcLength(contour, True), 1)
        box = cv2.boxPoints(cv2.minAreaRect(contour))
        d1, d2 = max(np.linalg.norm(box[0]-box[1]), 1), max(np.linalg.norm(box[1]-box[2]), 1)
        return {
            "k_median": float(np.median(kv)), "k_std": float(np.std(kv)),
            "b_median": float(np.median(bv)), "b_std": float(np.std(bv)),
            "g_median": float(np.median(gv)), "g_std": float(np.std(gv)),
            "r_median": float(np.median(rv)), "r_std": float(np.std(rv)),
            "area": float(area), "perimeter": float(perim),
            "area_perimeter_ratio": float(16 * area / perim**2),
            "aspect_ratio": float(max(d1, d2) / min(d1, d2)),
            "points_per_unit_length": float(len(contour) / perim),
        }

    # ── Validation ──────────────────────────────────────────────────────

    def check_criteria(self, stats):
        c = self.config["criteria"]
        return all([
            stats["k_std"] < c["k_std"]["max"], stats["b_std"] < c["b_std"]["max"],
            stats["g_std"] < c["g_std"]["max"], stats["r_std"] < c["r_std"]["max"],
            c["area_perimeter_ratio"]["min"] < stats["area_perimeter_ratio"] < c["area_perimeter_ratio"]["max"],
            c["aspect_ratio"]["min"] < stats["aspect_ratio"] < c["aspect_ratio"]["max"],
            c["points_per_unit_length"]["min"] < stats["points_per_unit_length"] < c["points_per_unit_length"]["max"],
        ])

    def check_color_in_range(self, stats, mask_values):
        use = self.config["use_channels"]
        return all(
            mask_values[ch]["min"] < stats[f"{ch}_median"] < mask_values[ch]["max"]
            for ch in ["k", "b", "g", "r"] if use.get(ch)
        )

    # ── Main detection pipeline ─────────────────────────────────────────

    def detect(self, image, mask_values_list, min_area=None):
        """Returns (flakes_list, k, b, g, r) processed channels."""
        if min_area is None:
            min_area = self.config["min_area"]
        corrected = self.preprocess_image(image)
        self._debug_image(corrected, "Vignetting-corrected")
        processed = cv2.medianBlur(corrected, self.config.get("median_blur_size", 7))
        self._debug_image(processed, "Preprocessed (median blur)")
        k, b, g, r = self.extract_kbgr(processed)
        flakes = []
        for idx, mv in enumerate(mask_values_list):
            sel = self.make_selection(k, b, g, r, mv)
            self._debug_image(sel, f"Combined mask - interval {idx}")
            for contour in self.find_contours_in_mask(sel, min_area):
                stats = self.calculate_contour_statistics(contour, k, b, g, r)
                if not self.check_criteria(stats):
                    continue
                if not self.check_color_in_range(stats, mv):
                    continue
                M = cv2.moments(contour)
                cx = int(M["m10"] / M["m00"]) if M["m00"] > 0 else 0
                cy = int(M["m01"] / M["m00"]) if M["m00"] > 0 else 0
                flakes.append({"contour": contour, "interval_idx": idx,
                               "center": (cx, cy), "stats": stats, "mask_values": mv})
        return flakes, k, b, g, r

    def detect_flakes(self, image, mask_values_list, min_area=None):
        """Convenience wrapper: returns just the flakes list."""
        flakes, *_ = self.detect(image, mask_values_list, min_area)
        return flakes

    # ── Visualization ───────────────────────────────────────────────────

    def visualize_flakes(self, image, flakes, show_stats=True):
        vis = image.copy()
        if not flakes:
            return vis
        max_iv = max(f["interval_idx"] for f in flakes)
        colors = (cm.rainbow(np.linspace(0, 1, max_iv + 1))[:, :3] * 255)
        for i, f in enumerate(flakes):
            c = colors[f["interval_idx"]].astype(int).tolist()
            cv2.drawContours(vis, [f["contour"]], -1, c, 2)
            cv2.circle(vis, f["center"], 5, c, -1)
            if show_stats:
                label = f"{i}: A={int(f['stats']['area'])}"
                pos = (f["center"][0] + 10, f["center"][1])
                cv2.putText(vis, label, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
                cv2.putText(vis, label, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)
        return vis

    def _debug_image(self, image, text=""):
        if self.debug:
            plt.figure(figsize=(7, 7))
            if len(image.shape) == 3:
                plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                plt.imshow(image, cmap="gray")
            if text:
                plt.title(text)
            plt.axis("off")
            plt.show()