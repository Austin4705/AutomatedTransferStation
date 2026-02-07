#!/usr/bin/env python3
"""
Graphene-focused testing suite that mirrors Flinder's SubHunter logic.

The suite loads the sample wafer frames (images/imageW*.png), runs the requested
detector (lab or flinder) and optionally displays each annotated overlay.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import cv2

from detect_flakes import (
    FlakeDetectionConfig,
    FlakeDetector,
    FlinderGrapheneConfig,
    FlinderGrapheneDetector,
    collect_image_paths,
    parse_manual_color_targets,
    render_overlays,
)

try:
    import matplotlib.pyplot as plt  # type: ignore
except ImportError:  # pragma: no cover - matplotlib not strictly required
    plt = None


DEFAULT_IMAGES = (Path(__file__).parent / "images", "imageW*.png")


@dataclass
class SuiteDetector:
    detector: object
    overlay_kwargs: Dict[str, Tuple[int, int, int] | float]


def create_suite_detector(
    detector_type: str,
    *,
    calibration_path: Path,
    scale_ratio: float,
    manual_targets,
) -> SuiteDetector:
    if detector_type == "lab":
        config = FlakeDetectionConfig()
        detector = FlakeDetector(config)
        overlay_kwargs = dict(
            overlay_alpha=config.overlay_alpha,
            fill_color=config.overlay_fill_color,
            border_color=config.overlay_border_color,
        )
        return SuiteDetector(detector=detector, overlay_kwargs=overlay_kwargs)

    config = FlinderGrapheneConfig(
        calibration_path=calibration_path,
        scale_ratio=scale_ratio,
        targeted_size_um2=80.0,
        min_contour_area_px=150.0,
        thickness_range=(0.0, 10.0),
        apply_high_contrast=None,
        reference_rgb=(160, 166, 166),
        manual_color_targets=manual_targets,
    )
    detector = FlinderGrapheneDetector(config)
    overlay_kwargs = dict(
        overlay_alpha=config.overlay_alpha,
        fill_color=config.overlay_fill_color,
        border_color=config.overlay_border_color,
    )
    return SuiteDetector(detector=detector, overlay_kwargs=overlay_kwargs)


def display_overlay(title: str, overlay: cv2.Mat, delay: float) -> None:
    if plt is None:
        print(f"[WARN] matplotlib not available, skipping display for {title}")
        return
    rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(8, 8))
    plt.imshow(rgb)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.show(block=False)
    plt.pause(delay)
    plt.close()


def run_suite(args: argparse.Namespace) -> None:
    images_dir, pattern = DEFAULT_IMAGES
    image_paths = collect_image_paths(str(images_dir), pattern, suite=True)
    if not image_paths:
        raise SystemExit(f"No wafer frames found under {images_dir}")

    try:
        manual_targets = parse_manual_color_targets(
            args.manual_color_target,
            args.manual_color_width,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    suite_detector = create_suite_detector(
        args.detector,
        calibration_path=Path(args.calibration_path),
        scale_ratio=args.scale_ratio,
        manual_targets=manual_targets,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in image_paths:
        print(f"[SUITE] Processing {path}")
        result = suite_detector.detector.detect(path)
        original = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if original is None:
            raise ValueError(f"Unable to read {path}")

        overlay = render_overlays(
            original.copy(),
            result.flakes,
            **suite_detector.overlay_kwargs,
        )
        save_path = output_dir / f"{path.stem}_{args.detector}.png"
        cv2.imwrite(str(save_path), overlay)
        print(f"         -> saved overlay to {save_path}")
        if args.show:
            display_overlay(f"{path.name} ({len(result.flakes)} flakes)", overlay, args.delay)
        time.sleep(0.05)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the graphene flake detection suite")
    parser.add_argument(
        "--detector",
        choices=["lab", "flinder"],
        default="flinder",
        help="Which backend to test",
    )
    parser.add_argument(
        "--calibration-path",
        type=str,
        default="Flinder/Flinder/Materials/Default/Graphene1234",
        help="Material folder copied from Flinder",
    )
    parser.add_argument(
        "--scale-ratio",
        type=float,
        default=0.3,
        help="Microns per pixel for the wafer frames",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="TestingEnv/CVTesting/FlakeDetection/output/suite",
        help="Directory where the overlays will be written",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Also render each overlay using matplotlib",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Seconds to keep each matplotlib window open",
    )
    parser.add_argument(
        "--manual-color-target",
        action="append",
        default=[],
        metavar="label:R,G,B[:layers]",
        help="Manual colour targets forwarded to Flinder detector",
    )
    parser.add_argument(
        "--manual-color-width",
        type=float,
        default=12.0,
        help="Half-width around each manual colour target (RGB/K units)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    run_suite(parse_args())

