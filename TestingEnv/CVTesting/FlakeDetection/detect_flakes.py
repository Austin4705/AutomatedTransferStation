#!/usr/bin/env python3
"""
Dual-mode flake detector that can run either the lightweight LAB-based heuristic
or the full Flinder SubHunter-style colour/criteria pipeline for graphene.

Usage examples:
    python detect_flakes.py --images images --pattern "imageW*.png"
    python detect_flakes.py --detector flinder --scale-ratio 0.32 --suite

All outputs are written under the directory passed via --output-dir
(defaults to TestingEnv/CVTesting/FlakeDetection/output).
"""

from __future__ import annotations

import argparse
import dataclasses
import glob
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import cv2
import numpy as np

from colorpicker import ColorPicker

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# -----------------------------------------------------------------------------
# Data containers and helpers
# -----------------------------------------------------------------------------


@dataclass
class FlakeDetectionConfig:
    """Configuration for the LAB-based detector."""

    target_rgb: Tuple[int, int, int] = (160, 166, 166)
    delta_e_threshold: float = 8.0
    min_area: float = 200.0
    max_area: float = 1_000_000.0
    max_area_ratio: float = 0.35
    max_std_lab: float = 8.0
    max_std_bgr: float = 20.0
    min_solidity: float = 0.8
    min_point_density: float = 0.35
    max_aspect_ratio: float = 15.0
    blur_kernel: int = 7
    morph_kernel: int = 9
    overlay_alpha: float = 0.4
    overlay_fill_color: Tuple[int, int, int] = (0, 0, 255)
    overlay_border_color: Tuple[int, int, int] = (0, 255, 0)


@dataclass
class Flake:
    """Statistics captured for each validated contour."""

    contour: np.ndarray
    bbox: Tuple[int, int, int, int]
    centroid: Tuple[float, float]
    area_px: float
    perimeter_px: float
    solidity: float
    aspect_ratio: float
    point_density: float
    mean_bgr: Tuple[float, float, float]
    std_bgr: Tuple[float, float, float]
    mean_lab: Tuple[float, float, float]
    std_lab: Tuple[float, float, float]
    delta_e: float
    layers: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionResult:
    """Full result for an image."""

    image_path: Path
    mask: np.ndarray
    flakes: List[Flake]


def _rgb_to_bgr(rgb: Sequence[int]) -> Tuple[int, int, int]:
    r, g, b = rgb
    return (b, g, r)


def _ensure_odd(value: int) -> int:
    """Median/Gaussian kernels must be odd."""
    return value if value % 2 == 1 else value + 1


def render_overlays(
    image_bgr: np.ndarray,
    flakes: Iterable[Flake],
    *,
    overlay_alpha: float,
    fill_color: Tuple[int, int, int],
    border_color: Tuple[int, int, int],
) -> np.ndarray:
    overlay = image_bgr.copy()
    for flake in flakes:
        cv2.drawContours(overlay, [flake.contour], -1, fill_color, thickness=-1)

    blended = cv2.addWeighted(
        overlay,
        overlay_alpha,
        image_bgr,
        1.0 - overlay_alpha,
        0,
    )

    for idx, flake in enumerate(flakes, start=1):
        x, y, w_box, h_box = flake.bbox
        cv2.rectangle(
            blended,
            (x, y),
            (x + w_box, y + h_box),
            border_color,
            thickness=2,
        )

        label_bits = [f"flake#{idx}", f"area={int(flake.area_px)}"]
        if flake.layers is not None:
            label_bits.append(f"L={int(round(flake.layers))}")
        target_label = flake.metadata.get("target_label")
        if target_label:
            label_bits.append(str(target_label))
        label = " ".join(label_bits)

        text_origin = (x, max(30, y - 10))
        cv2.putText(
            blended,
            label,
            text_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            border_color,
            thickness=2,
        )
    return blended


# -----------------------------------------------------------------------------
# LAB-based heuristic detector (legacy mode)
# -----------------------------------------------------------------------------


class FlakeDetector:
    """Deterministic colour/geometry driven flake detector."""

    def __init__(self, config: FlakeDetectionConfig):
        self.config = config
        self.target_bgr = np.array(_rgb_to_bgr(config.target_rgb), dtype=np.uint8)
        self.target_lab = cv2.cvtColor(
            self.target_bgr.reshape(1, 1, 3), cv2.COLOR_BGR2LAB
        )[0, 0].astype(np.float32)

    def detect(self, image_path: Path) -> DetectionResult:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Failed to read image {image_path}")

        filtered = cv2.medianBlur(image, ksize=_ensure_odd(self.config.blur_kernel))
        lab = cv2.cvtColor(filtered, cv2.COLOR_BGR2LAB)

        mask = self._build_mask(lab)
        contours = self._find_contours(mask)

        flakes: List[Flake] = []
        for contour in contours:
            flake = self._evaluate_contour(contour, image, lab)
            if flake:
                flakes.append(flake)

        return DetectionResult(image_path=image_path, mask=mask, flakes=flakes)

    def _build_mask(self, lab_image: np.ndarray) -> np.ndarray:
        diff = lab_image.astype(np.float32) - self.target_lab
        delta = np.linalg.norm(diff, axis=2)
        mask = (delta <= self.config.delta_e_threshold).astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.config.morph_kernel, self.config.morph_kernel),
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)
        return mask

    @staticmethod
    def _find_contours(mask: np.ndarray) -> List[np.ndarray]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        return contours

    def _evaluate_contour(
        self,
        contour: np.ndarray,
        image_bgr: np.ndarray,
        image_lab: np.ndarray,
    ) -> Flake | None:
        area = cv2.contourArea(contour)
        if area < self.config.min_area or area > self.config.max_area:
            return None

        h, w = image_bgr.shape[:2]
        if area > self.config.max_area_ratio * (h * w):
            return None

        perimeter = cv2.arcLength(contour, closed=True)
        if perimeter < 1e-3:
            return None

        mask = np.zeros(image_bgr.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], contourIdx=-1, color=255, thickness=-1)

        bgr_mean, bgr_std = cv2.meanStdDev(image_bgr, mask=mask)
        lab_mean, lab_std = cv2.meanStdDev(image_lab, mask=mask)

        bgr_mean = tuple(float(x) for x in bgr_mean.flatten())
        bgr_std = tuple(float(x) for x in bgr_std.flatten())
        lab_mean = tuple(float(x) for x in lab_mean.flatten())
        lab_std = tuple(float(x) for x in lab_std.flatten())

        delta_e = float(np.linalg.norm(np.array(lab_mean) - self.target_lab))
        if delta_e > self.config.delta_e_threshold * 1.35:
            return None
        if max(lab_std) > self.config.max_std_lab:
            return None
        if max(bgr_std) > self.config.max_std_bgr:
            return None

        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull) + 1e-6
        solidity = area / hull_area
        if solidity < self.config.min_solidity:
            return None

        point_density = len(contour) / (perimeter + 1e-6)
        if point_density < self.config.min_point_density:
            return None

        x, y, bw, bh = cv2.boundingRect(contour)
        aspect_ratio = max(bw, bh) / max(1, min(bw, bh))
        if aspect_ratio > self.config.max_aspect_ratio:
            return None

        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            return None
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]

        return Flake(
            contour=contour,
            bbox=(int(x), int(y), int(bw), int(bh)),
            centroid=(float(cx), float(cy)),
            area_px=float(area),
            perimeter_px=float(perimeter),
            solidity=float(solidity),
            aspect_ratio=float(aspect_ratio),
            point_density=float(point_density),
            mean_bgr=bgr_mean,
            std_bgr=bgr_std,
            mean_lab=lab_mean,
            std_lab=lab_std,
            delta_e=delta_e,
        )


# -----------------------------------------------------------------------------
# Flinder-inspired graphene detector
# -----------------------------------------------------------------------------


@dataclass
class FlinderCriterion:
    name: str
    use: bool
    min_value: float
    max_value: float


@dataclass
class ManualColorTarget:
    label: str
    rgb: Tuple[int, int, int]
    mask_values: Tuple[float, float, float, float, float, float, float, float]
    layer_hint: float | None
    target_lab: np.ndarray


@dataclass
class FlinderCalibration:
    mask_values: List[Tuple[float, float, float, float, float, float, float, float]]
    criteria: List[FlinderCriterion]
    thickness: np.ndarray
    k: np.ndarray
    b: np.ndarray
    g: np.ndarray
    r: np.ndarray
    k_error: np.ndarray
    b_error: np.ndarray
    g_error: np.ndarray
    r_error: np.ndarray
    layer_or_thickness: int
    number_of_intervals: int
    use_k: bool
    use_b: bool
    use_g: bool
    use_r: bool
    high_contrast: bool

    @classmethod
    def from_folder(cls, folder: Path) -> "FlinderCalibration":
        folder = Path(folder)
        calibration_rows = _load_numeric_table(folder / "calibration.dat")
        if calibration_rows.shape[1] < 9:
            raise ValueError(f"Unexpected calibration file format in {folder}")

        details_row = _load_numeric_table(folder / "calibration_details.dat")[0]
        if details_row.shape[0] < 7:
            raise ValueError(f"Unexpected calibration_details format in {folder}")

        criteria = _load_criteria(folder / "criterium.dat")

        thickness = calibration_rows[:, 0].astype(np.float32)
        k = calibration_rows[:, 1].astype(np.float32)
        b = calibration_rows[:, 2].astype(np.float32)
        g = calibration_rows[:, 3].astype(np.float32)
        r = calibration_rows[:, 4].astype(np.float32)
        k_error = calibration_rows[:, 5].astype(np.float32)
        b_error = calibration_rows[:, 6].astype(np.float32)
        g_error = calibration_rows[:, 7].astype(np.float32)
        r_error = calibration_rows[:, 8].astype(np.float32)

        layer_or_thickness = int(details_row[0])
        number_of_intervals = int(details_row[1])
        use_k = bool(int(details_row[2]))
        use_b = bool(int(details_row[3]))
        use_g = bool(int(details_row[4]))
        use_r = bool(int(details_row[5]))
        high_contrast = bool(int(details_row[6])) if len(details_row) > 6 else False

        mask_values = _build_mask_values(
            thickness,
            k,
            b,
            g,
            r,
            k_error,
            b_error,
            g_error,
            r_error,
            number_of_intervals,
        )

        return cls(
            mask_values=mask_values,
            criteria=criteria,
            thickness=thickness,
            k=k,
            b=b,
            g=g,
            r=r,
            k_error=k_error,
            b_error=b_error,
            g_error=g_error,
            r_error=r_error,
            layer_or_thickness=layer_or_thickness,
            number_of_intervals=number_of_intervals,
            use_k=use_k,
            use_b=use_b,
            use_g=use_g,
            use_r=use_r,
            high_contrast=high_contrast,
        )

    def color_in_range(
        self,
        mask_values: Tuple[float, float, float, float, float, float, float, float],
        kbgr: Tuple[float, float, float, float],
    ) -> bool:
        k_val, b_val, g_val, r_val = kbgr
        kmin, kmax, bmin, bmax, gmin, gmax, rmin, rmax = mask_values

        checks = []
        if self.use_k:
            checks.append(kmin <= k_val <= kmax)
        if self.use_b:
            checks.append(bmin <= b_val <= bmax)
        if self.use_g:
            checks.append(gmin <= g_val <= gmax)
        if self.use_r:
            checks.append(rmin <= r_val <= rmax)

        return all(checks)

    def criteria_pass(self, metrics: Dict[str, float]) -> bool:
        for criterion in self.criteria:
            if not criterion.use:
                continue
            value = metrics.get(criterion.name)
            if value is None:
                continue
            if not (criterion.min_value <= value <= criterion.max_value):
                return False
        return True

    def estimate_layers(self, kbgr: Tuple[float, float, float, float]) -> float:
        target = np.array(kbgr, dtype=np.float32)
        colors = np.stack([self.k, self.b, self.g, self.r], axis=1)
        distances = np.linalg.norm(colors - target, axis=1)
        idx = int(np.argmin(distances))
        return float(self.thickness[idx])


@dataclass
class FlinderGrapheneConfig:
    calibration_path: Path
    scale_ratio: float = 0.3  # µm / px
    targeted_size_um2: float = 80.0
    min_contour_area_px: float = 150.0
    max_area_ratio: float = 0.35
    thickness_range: Tuple[float, float] = (0.0, 10.0)
    apply_high_contrast: bool | None = None
    blur_kernel: int = 7
    reference_rgb: Tuple[int, int, int] = (160, 166, 166)
    overlay_alpha: float = 0.45
    overlay_fill_color: Tuple[int, int, int] = (255, 0, 0)
    overlay_border_color: Tuple[int, int, int] = (255, 255, 0)
    color_normalize: bool = True
    delta_e_threshold: float = 50.0
    manual_color_targets: List[ManualColorTarget] = field(default_factory=list)

    def __post_init__(self) -> None:
        candidate = Path(self.calibration_path)
        if not candidate.is_absolute():
            candidate = (PROJECT_ROOT / candidate).resolve()
        self.calibration_path = candidate
        if not self.calibration_path.exists():
            raise FileNotFoundError(
                f"Could not locate calibration folder at {self.calibration_path}"
            )


class FlinderGrapheneDetector:
    """Subset of Flinder's SubHunter logic tuned for offline graphene flakes."""

    def __init__(self, config: FlinderGrapheneConfig):
        self.config = config
        self.calibration = FlinderCalibration.from_folder(config.calibration_path)
        self.manual_targets = list(config.manual_color_targets)
        if config.apply_high_contrast is None:
            self.use_high_contrast = bool(self.calibration.high_contrast)
        else:
            self.use_high_contrast = config.apply_high_contrast
        self.target_lab = cv2.cvtColor(
            np.array(_rgb_to_bgr(config.reference_rgb), dtype=np.uint8).reshape(1, 1, 3),
            cv2.COLOR_BGR2LAB,
        )[0, 0].astype(np.float32)

        self._targeted_area_px = max(
            int(round(config.targeted_size_um2 / max(1e-6, config.scale_ratio**2))),
            int(round(config.min_contour_area_px)),
        )
        self._calibration_means = (
            float(np.mean(self.calibration.k)),
            float(np.mean(self.calibration.b)),
            float(np.mean(self.calibration.g)),
            float(np.mean(self.calibration.r)),
        )

    def detect(self, image_path: Path) -> DetectionResult:
        image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError(f"Failed to read image {image_path}")
        self._image_area = image_bgr.shape[0] * image_bgr.shape[1]

        processed = self._preprocess(image_bgr)
        k, b, g, r = self._extract_kbgr(processed)
        lab_image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        self._lab_normalized = cv2.cvtColor(self._normalized_bgr, cv2.COLOR_BGR2LAB)

        self._channel_maps = {"k": k, "b": b, "g": g, "r": r}
        mask_accumulator = np.zeros(k.shape, dtype=np.uint8)
        flakes: List[Flake] = []

        if self.manual_targets:
            mask_sources = [
                (target.mask_values, target) for target in self.manual_targets
            ]
        else:
            mask_sources = [
                (mask_values, None) for mask_values in self.calibration.mask_values
            ]

        for mask_values, manual_target in mask_sources:
            selection = self._make_selection(mask_values)
            if self.config.delta_e_threshold > 0:
                target_lab = (
                    manual_target.target_lab if manual_target else self.target_lab
                )
                delta_mask = _delta_e_mask(
                    self._lab_normalized,
                    target_lab,
                    self.config.delta_e_threshold,
                )
                selection = cv2.bitwise_and(selection, delta_mask)
            mask_accumulator = cv2.bitwise_or(mask_accumulator, selection)
            contours = self._find_contours(selection)
            for contour in contours:
                flake = self._evaluate_contour(
                    contour,
                    mask_values,
            image_bgr,
                    lab_image,
                    manual_target=manual_target,
                )
                if flake:
                    flakes.append(flake)

        return DetectionResult(image_path=image_path, mask=mask_accumulator, flakes=flakes)

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        if not self.use_high_contrast:
            return cv2.medianBlur(image, ksize=_ensure_odd(self.config.blur_kernel))
        contrasted = _high_contrast(image)
        return cv2.medianBlur(contrasted, ksize=_ensure_odd(self.config.blur_kernel))

    def _extract_kbgr(self, image: np.ndarray) -> Tuple[np.ndarray, ...]:
        b, g, r = cv2.split(image)
        if self.config.color_normalize:
            b, g, r = self._normalize_channels(b, g, r)
        corrected = cv2.merge((b, g, r))
        self._normalized_bgr = corrected
        k = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY)
        return k.astype(np.uint8), b.astype(np.uint8), g.astype(np.uint8), r.astype(np.uint8)

    def _normalize_channels(
        self,
        b: np.ndarray,
        g: np.ndarray,
        r: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        normalized = []
        current_means = (
            float(np.mean(b)),
            float(np.mean(g)),
            float(np.mean(r)),
        )
        target_means = self._calibration_means[1:]
        for channel, current_mean, target_mean in zip(
            (b, g, r), current_means, target_means
        ):
            shift = target_mean - current_mean
            shift = float(np.clip(shift, -80.0, 80.0))
            adjusted = np.clip(channel.astype(np.float32) + shift, 0, 255).astype(np.uint8)
            normalized.append(adjusted)
        return tuple(normalized)  # type: ignore[return-value]

    def _make_selection(
        self,
        mask_values: Tuple[float, float, float, float, float, float, float, float],
    ) -> np.ndarray:
        kmin, kmax, bmin, bmax, gmin, gmax, rmin, rmax = mask_values
        mask = np.full(self._channel_maps["k"].shape, 255, dtype=np.uint8)

        if self.calibration.use_k:
            mask = cv2.bitwise_and(mask, _range_mask(self._channel_maps["k"], kmin, kmax))
        if self.calibration.use_b:
            mask = cv2.bitwise_and(mask, _range_mask(self._channel_maps["b"], bmin, bmax))
        if self.calibration.use_g:
            mask = cv2.bitwise_and(mask, _range_mask(self._channel_maps["g"], gmin, gmax))
        if self.calibration.use_r:
            mask = cv2.bitwise_and(mask, _range_mask(self._channel_maps["r"], rmin, rmax))

        mask = cv2.medianBlur(mask, 5)
        return mask

    def _find_contours(self, mask: np.ndarray) -> List[np.ndarray]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filtered = [
            contour
            for contour in contours
            if cv2.contourArea(contour) >= self._targeted_area_px
        ]
        return filtered

    def _evaluate_contour(
        self,
        contour: np.ndarray,
        mask_values: Tuple[float, float, float, float, float, float, float, float],
        image_bgr: np.ndarray,
        image_lab: np.ndarray,
        manual_target: ManualColorTarget | None = None,
    ) -> Flake | None:
        area_px = float(cv2.contourArea(contour))
        perimeter_px = float(cv2.arcLength(contour, True))
        if perimeter_px <= 1e-3:
            return None
        if area_px > self.config.max_area_ratio * self._image_area:
            return None

        mask = np.zeros(image_bgr.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, thickness=-1)

        k_vals = self._channel_maps["k"][mask > 0]
        b_vals = self._channel_maps["b"][mask > 0]
        g_vals = self._channel_maps["g"][mask > 0]
        r_vals = self._channel_maps["r"][mask > 0]
        if not len(k_vals):
            return None

        kbgr_median = (
            float(np.median(k_vals)),
            float(np.median(b_vals)),
            float(np.median(g_vals)),
            float(np.median(r_vals)),
        )
        kbgr_std = (
            float(np.std(k_vals)),
            float(np.std(b_vals)),
            float(np.std(g_vals)),
            float(np.std(r_vals)),
        )

        if manual_target is None:
            if not self.calibration.color_in_range(mask_values, kbgr_median):
                return None

        scale = self.config.scale_ratio
        area_um2 = area_px * scale * scale
        perimeter_um = perimeter_px * scale

        rect = cv2.minAreaRect(contour)
        width_um = max(rect[1][0], 1e-3) * scale
        height_um = max(rect[1][1], 1e-3) * scale
        aspect_ratio = max(width_um, height_um) / max(1e-6, min(width_um, height_um))
        point_density = len(contour) / (perimeter_px + 1e-6)
        solidity = area_px / (cv2.contourArea(cv2.convexHull(contour)) + 1e-6)

        metrics = {
            "grey_variance": kbgr_std[0],
            "blue_variance": kbgr_std[1],
            "green_variance": kbgr_std[2],
            "red_variance": kbgr_std[3],
            "Area/Perimeter": (16 * area_um2) / max(1e-6, perimeter_um * perimeter_um),
            "aspect_ratio": aspect_ratio,
            "Npoints_contour": point_density,
        }

        if not self.calibration.criteria_pass(metrics):
            return None

        estimated_layers = self.calibration.estimate_layers(kbgr_median)
        if manual_target and manual_target.layer_hint is not None:
            estimated_layers = manual_target.layer_hint
        tmin, tmax = self.config.thickness_range
        if not (tmin <= estimated_layers <= tmax):
            return None

        bgr_mean, bgr_std = cv2.meanStdDev(image_bgr, mask=mask)
        lab_mean, lab_std = cv2.meanStdDev(image_lab, mask=mask)
        bgr_mean = tuple(float(x) for x in bgr_mean.flatten())
        bgr_std = tuple(float(x) for x in bgr_std.flatten())
        lab_mean = tuple(float(x) for x in lab_mean.flatten())
        lab_std = tuple(float(x) for x in lab_std.flatten())

        lab_target = manual_target.target_lab if manual_target else self.target_lab
        delta_e = float(np.linalg.norm(np.array(lab_mean) - lab_target))

        x, y, bw, bh = cv2.boundingRect(contour)
        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            return None
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]

        metadata: Dict[str, Any] = {
            "area_um2": area_um2,
            "perimeter_um": perimeter_um,
        }
        if manual_target:
            metadata["target_label"] = manual_target.label

        return Flake(
            contour=contour,
            bbox=(int(x), int(y), int(bw), int(bh)),
            centroid=(float(cx), float(cy)),
            area_px=area_px,
            perimeter_px=perimeter_px,
            solidity=float(solidity),
            aspect_ratio=float(aspect_ratio),
            point_density=float(point_density),
            mean_bgr=bgr_mean,
            std_bgr=bgr_std,
            mean_lab=lab_mean,
            std_lab=lab_std,
            delta_e=delta_e,
            layers=estimated_layers,
            metadata=metadata,
        )


# -----------------------------------------------------------------------------
# File I/O helpers shared by CLI + test suite
# -----------------------------------------------------------------------------


def _load_numeric_table(path: Path) -> np.ndarray:
    rows: List[List[float]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.replace("\t", " ")
            tokens = [token for token in line.split(" ") if token]
            rows.append([float(token) for token in tokens])

    if not rows:
        raise ValueError(f"No numeric rows found in {path}")
    return np.array(rows, dtype=np.float32)


def _load_criteria(path: Path) -> List[FlinderCriterion]:
    criteria: List[FlinderCriterion] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.replace("\t", " ")
            tokens = [token for token in line.split(" ") if token]
            if len(tokens) < 4:
                continue
            name = tokens[0]
            use = bool(int(float(tokens[1])))
            min_value = float(tokens[2])
            max_value = float(tokens[3])
            criteria.append(FlinderCriterion(name=name, use=use, min_value=min_value, max_value=max_value))
    return criteria


def _build_mask_values(
    thickness: np.ndarray,
    k: np.ndarray,
    b: np.ndarray,
    g: np.ndarray,
    r: np.ndarray,
    k_error: np.ndarray,
    b_error: np.ndarray,
    g_error: np.ndarray,
    r_error: np.ndarray,
    number_of_intervals: int,
) -> List[Tuple[float, float, float, float, float, float, float, float]]:
    segments = np.linspace(thickness.min(), thickness.max(), number_of_intervals + 1)
    mask_values: List[Tuple[float, float, float, float, float, float, float, float]] = []
    for idx in range(number_of_intervals):
        tmin, tmax = segments[idx], segments[idx + 1]
        kmin, kmax = _segment_bounds(thickness, k, k_error, tmin, tmax)
        bmin, bmax = _segment_bounds(thickness, b, b_error, tmin, tmax)
        gmin, gmax = _segment_bounds(thickness, g, g_error, tmin, tmax)
        rmin, rmax = _segment_bounds(thickness, r, r_error, tmin, tmax)
        mask_values.append((kmin, kmax, bmin, bmax, gmin, gmax, rmin, rmax))
    return mask_values


def _segment_bounds(
    thickness: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    tmin: float,
    tmax: float,
) -> Tuple[float, float]:
    mask = (thickness >= tmin) & (thickness <= tmax)
    if not np.any(mask):
        mask = np.ones_like(thickness, dtype=bool)
    vals = values[mask]
    errs = errors[mask]
    lower = float(np.min(vals - errs))
    upper = float(np.max(vals + errs))
    return lower, upper


def _high_contrast(image: np.ndarray) -> np.ndarray:
    b, g, r = cv2.split(image)
    b = _filtering_extreme_values(b)
    g = _filtering_extreme_values(g)
    r = _filtering_extreme_values(r)
    merged = cv2.merge((b, g, r))
    return cv2.medianBlur(merged, 11)


def _filtering_extreme_values(channel: np.ndarray) -> np.ndarray:
    v = channel.astype(np.float32)
    spread = 20
    mid = 255.0 / 2.0
    liminf = mid - spread
    limsup = mid + spread

    a = mid / (mid - liminf)
    b = -a * liminf
    cond = v < mid
    v[cond] = a * v[cond] + b

    a = (mid - 255.0) / (mid - limsup)
    b = 255.0 - a * limsup
    cond = v > mid
    v[cond] = a * v[cond] + b

    np.clip(v, 0, 255, out=v)
    return v.astype(np.uint8)


def _range_mask(channel: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    blurred = cv2.blur(channel, (5, 5))
    mask = np.zeros_like(channel, dtype=np.uint8)
    mask[(blurred >= vmin) & (blurred <= vmax)] = 255
    return mask


def _delta_e_mask(
    lab_image: np.ndarray,
    target_lab: np.ndarray,
    threshold: float,
) -> np.ndarray:
    diff = lab_image.astype(np.float32) - target_lab.reshape(1, 1, 3)
    delta = np.linalg.norm(diff, axis=2)
    mask = np.zeros(lab_image.shape[:2], dtype=np.uint8)
    mask[delta <= threshold] = 255
    return mask


def _rgb_to_k(rgb: Tuple[int, int, int]) -> int:
    r, g, b = rgb
    return int(round(0.2989 * r + 0.5870 * g + 0.1140 * b))


def _clamp_channel(value: float, width: float) -> Tuple[float, float]:
    return max(0.0, value - width), min(255.0, value + width)


def _build_manual_target(
    label: str,
    rgb: Tuple[int, int, int],
    layer_hint: float | None,
    width: float,
) -> ManualColorTarget:
    width = max(0.0, width)
    bgr = _rgb_to_bgr(rgb)
    k_value = _rgb_to_k(rgb)
    kmin, kmax = _clamp_channel(k_value, width)
    bmin, bmax = _clamp_channel(bgr[0], width)
    gmin, gmax = _clamp_channel(bgr[1], width)
    rmin, rmax = _clamp_channel(bgr[2], width)
    mask_values = (kmin, kmax, bmin, bmax, gmin, gmax, rmin, rmax)

    lab = cv2.cvtColor(
        np.array([[bgr]], dtype=np.uint8),
        cv2.COLOR_BGR2LAB,
    )[0, 0].astype(np.float32)

    return ManualColorTarget(
        label=label,
        rgb=rgb,
        mask_values=mask_values,
        layer_hint=layer_hint,
        target_lab=lab,
    )


def parse_manual_color_targets(
    specs: Sequence[str],
    width: float,
) -> List[ManualColorTarget]:
    targets: List[ManualColorTarget] = []
    for spec in specs:
        if not spec:
            continue
        parts = spec.split(":")
        if len(parts) < 2:
            raise ValueError(
                f"Manual color target '{spec}' must use format label:R,G,B[:layers]"
            )
        label = parts[0].strip() or f"target{len(targets)}"
        rgb_tokens = parts[1].split(",")
        if len(rgb_tokens) != 3:
            raise ValueError(
                f"Manual color target '{spec}' must provide three comma-separated RGB values"
            )
        try:
            r, g, b = [int(token) for token in rgb_tokens]
        except ValueError as exc:
            raise ValueError(f"Manual color target '{spec}' has invalid RGB values") from exc
        layer_hint = None
        if len(parts) > 2 and parts[2].strip():
            try:
                layer_hint = float(parts[2])
            except ValueError as exc:
                raise ValueError(
                    f"Manual color target '{spec}' has invalid layer value"
                ) from exc
        targets.append(_build_manual_target(label, (r, g, b), layer_hint, width))
    return targets


def collect_image_paths(images_arg: str, pattern: str, suite: bool) -> List[Path]:
    if suite:
        default_dir = Path(__file__).parent / "images"
        return sorted(default_dir.glob("imageW*.png"))

    candidate = Path(images_arg)
    if candidate.is_file():
        return [candidate]
    if candidate.is_dir():
        return sorted(candidate.glob(pattern))

    matches = [Path(p) for p in glob.glob(images_arg)]
    if matches:
        return sorted(matches)

    raise FileNotFoundError(f"No images found for {images_arg}")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministic + Flinder flake detector")
    parser.add_argument(
        "--detector",
        choices=["lab", "flinder"],
        default="lab",
        help="Which backend to use (lab = legacy heuristic, flinder = graphene)",
    )
    parser.add_argument(
        "--images",
        type=str,
        default="TestingEnv/CVTesting/FlakeDetection/images",
        help="Directory, glob, or single image to analyse",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.png",
        help="Glob pattern (used only when --images is a directory)",
    )
    parser.add_argument(
        "--suite",
        action="store_true",
        help="Ignore --images/--pattern and process the default imageW* wafer set",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="TestingEnv/CVTesting/FlakeDetection/output",
        help="Directory where overlays/metadata will be saved",
    )
    parser.add_argument(
        "--target-rgb",
        type=int,
        nargs=3,
        metavar=("R", "G", "B"),
        default=(160, 166, 166),
        help="Reference flake colour picked from the microscope images",
    )
    parser.add_argument("--delta-e", type=float, default=8.0)
    parser.add_argument("--min-area", type=float, default=200.0)
    parser.add_argument("--max-area", type=float, default=1_000_000.0)
    parser.add_argument("--max-area-ratio", type=float, default=0.35)
    parser.add_argument("--max-std-lab", type=float, default=8.0)
    parser.add_argument("--max-std-bgr", type=float, default=20.0)
    parser.add_argument("--min-solidity", type=float, default=0.8)
    parser.add_argument("--min-point-density", type=float, default=0.35)
    parser.add_argument("--max-aspect-ratio", type=float, default=15.0)
    parser.add_argument("--blur-kernel", type=int, default=7)
    parser.add_argument("--morph-kernel", type=int, default=9)
    parser.add_argument("--overlay-alpha", type=float, default=0.4)
    parser.add_argument("--save-mask", action="store_true")

    # Flinder-specific options
    parser.add_argument(
        "--calibration-path",
        type=str,
        default="Flinder/Flinder/Materials/Default/Graphene1234",
        help="Path to the Flinder material folder (used with --detector flinder)",
    )
    parser.add_argument(
        "--scale-ratio",
        type=float,
        default=0.3,
        help="Microns per pixel for the captured images (flinder mode)",
    )
    parser.add_argument(
        "--targeted-size-um2",
        type=float,
        default=80.0,
        help="Minimum flake area in µm^2 for the flinder detector",
    )
    parser.add_argument(
        "--min-contour-area",
        type=float,
        default=150.0,
        help="Absolute contour area floor (px) for the flinder detector",
    )
    parser.add_argument(
        "--thickness-range",
        type=float,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=(0.0, 10.0),
        help="Only keep flakes whose estimated layer count is within this interval",
    )
    parser.add_argument(
        "--no-high-contrast",
        action="store_true",
        help="Force high-contrast preprocessing off (flinder detector)",
    )
    parser.add_argument(
        "--force-high-contrast",
        action="store_true",
        help="Force high-contrast preprocessing on (flinder detector)",
    )
    parser.add_argument(
        "--no-color-normalize",
        action="store_true",
        help="Disable per-channel colour normalization (flinder detector)",
    )
    parser.add_argument(
        "--flinder-delta-e",
        type=float,
        default=50.0,
        help="Delta-E filter applied before Flinder masking (0 disables it)",
    )
    parser.add_argument(
        "--manual-color-target",
        action="append",
        default=[],
        metavar="label:R,G,B[:layers]",
        help="Manual colour target (repeat). Example mono:140,150,160:1",
    )
    parser.add_argument(
        "--manual-color-width",
        type=float,
        default=12.0,
        help="Half-width in RGB/K used around each manual colour target",
    )
    parser.add_argument(
        "--pick-color",
        type=str,
        metavar="IMAGE_PATH",
        help="Open the interactive color picker on the provided image and exit",
    )

    return parser.parse_args()


def build_detector(args: argparse.Namespace):
    if args.detector == "lab":
        config = FlakeDetectionConfig(
            target_rgb=tuple(args.target_rgb),
            delta_e_threshold=args.delta_e,
            min_area=args.min_area,
            max_area=args.max_area,
            max_area_ratio=args.max_area_ratio,
            max_std_lab=args.max_std_lab,
            max_std_bgr=args.max_std_bgr,
            min_solidity=args.min_solidity,
            min_point_density=args.min_point_density,
            max_aspect_ratio=args.max_aspect_ratio,
            blur_kernel=args.blur_kernel,
            morph_kernel=args.morph_kernel,
            overlay_alpha=args.overlay_alpha,
        )
        detector = FlakeDetector(config)
        overlay_kwargs = dict(
            overlay_alpha=config.overlay_alpha,
            fill_color=config.overlay_fill_color,
            border_color=config.overlay_border_color,
        )
        return detector, overlay_kwargs

    try:
        manual_targets = parse_manual_color_targets(
            args.manual_color_target,
            args.manual_color_width,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    apply_high_contrast = None
    if args.force_high_contrast:
        apply_high_contrast = True
    elif args.no_high_contrast:
        apply_high_contrast = False

    flinder_config = FlinderGrapheneConfig(
        calibration_path=Path(args.calibration_path),
        scale_ratio=args.scale_ratio,
        targeted_size_um2=args.targeted_size_um2,
        min_contour_area_px=args.min_contour_area,
        thickness_range=tuple(args.thickness_range),
        apply_high_contrast=apply_high_contrast,
        blur_kernel=args.blur_kernel,
        reference_rgb=tuple(args.target_rgb),
        overlay_alpha=args.overlay_alpha,
        overlay_fill_color=(255, 0, 0),
        overlay_border_color=(255, 255, 0),
        color_normalize=not args.no_color_normalize,
        delta_e_threshold=args.flinder_delta_e,
        max_area_ratio=args.max_area_ratio,
        manual_color_targets=manual_targets,
    )
    detector = FlinderGrapheneDetector(flinder_config)
    overlay_kwargs = dict(
        overlay_alpha=flinder_config.overlay_alpha,
        fill_color=flinder_config.overlay_fill_color,
        border_color=flinder_config.overlay_border_color,
    )
    return detector, overlay_kwargs


def run_cli() -> None:
    args = parse_args()
    if args.pick_color:
        picker = ColorPicker(args.pick_color)
        picker.run()
        return
    detector, overlay_kwargs = build_detector(args)

    image_paths = collect_image_paths(args.images, args.pattern, args.suite)
    if not image_paths:
        raise SystemExit("No images found to process.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary: List[Dict[str, object]] = []
    for image_path in image_paths:
        print(f"[INFO] Processing {image_path}")
        result = detector.detect(image_path)

        original = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if original is None:
            raise ValueError(f"Failed to re-open image {image_path}")

        overlay = render_overlays(
            original.copy(),
            result.flakes,
            **overlay_kwargs,
        )

        overlay_path = output_dir / f"{image_path.stem}_flakes.png"
        cv2.imwrite(str(overlay_path), overlay)

        if args.save_mask:
            mask_path = output_dir / f"{image_path.stem}_mask.png"
            cv2.imwrite(str(mask_path), result.mask)

        summary.append(
            {
                "image": str(image_path),
                "num_flakes": len(result.flakes),
                "overlay": str(overlay_path),
                "flakes": [
                    {
                        "bbox": {
                            "x": flake.bbox[0],
                            "y": flake.bbox[1],
                            "w": flake.bbox[2],
                            "h": flake.bbox[3],
                        },
                        "centroid": {"x": flake.centroid[0], "y": flake.centroid[1]},
                        "area_px": flake.area_px,
                        "perimeter_px": flake.perimeter_px,
                        "solidity": flake.solidity,
                        "aspect_ratio": flake.aspect_ratio,
                        "point_density": flake.point_density,
                        "mean_bgr": flake.mean_bgr,
                        "std_bgr": flake.std_bgr,
                        "mean_lab": flake.mean_lab,
                        "std_lab": flake.std_lab,
                        "delta_e": flake.delta_e,
                        "layers": flake.layers,
                        "metadata": flake.metadata,
                    }
                    for flake in result.flakes
                ],
            }
        )
        print(f"       -> found {len(result.flakes)} flake(s)")

    summary_path = output_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"[INFO] Summary written to {summary_path}")


if __name__ == "__main__":
    run_cli()
