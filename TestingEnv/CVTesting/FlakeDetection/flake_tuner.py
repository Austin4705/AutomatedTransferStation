"""
Flake Detection Tuner
Interactive Streamlit app for tuning Flinder-style flake detection parameters.

Usage:
    cd TestingEnv/CVTesting/FlakeDetection
    streamlit run flake_tuner.py
"""

import streamlit as st
import cv2
import numpy as np
from pathlib import Path
from scipy.interpolate import interp1d


# ─── White Balance ───────────────────────────────────────────────────────────

def whitebalance(image):
    """White-balance an RGB image by equalizing to the most common color."""
    result = image.astype(np.float32)
    quantized = (image // 8) * 8
    brightness = quantized.sum(axis=2)
    mask = brightness > 30
    filtered = quantized[mask]

    colors_as_int = (
        (filtered[:, 0].astype(np.int32) << 16)
        | (filtered[:, 1].astype(np.int32) << 8)
        | filtered[:, 2].astype(np.int32)
    )

    counts = np.bincount(colors_as_int)
    most_common_int = np.argmax(counts)

    color = np.array(
        [
            (most_common_int >> 16) & 0xFF,
            (most_common_int >> 8) & 0xFF,
            most_common_int & 0xFF,
        ],
        dtype=np.float32,
    )

    avg_gray = (color[0] + color[1] + color[2]) / 3.0
    scale_r = avg_gray / color[0] if color[0] > 0 else 1.0
    scale_g = avg_gray / color[1] if color[1] > 0 else 1.0
    scale_b = avg_gray / color[2] if color[2] > 0 else 1.0
    result[:, :, 0] *= scale_r
    result[:, :, 1] *= scale_g
    result[:, :, 2] *= scale_b

    result = np.clip(result, 0, 255)
    return result.astype(np.uint8)


# ─── FlinderDetector (self-contained) ────────────────────────────────────────

class FlinderDetector:
    """Flinder-style flake detection with KBGR channel masking."""

    def __init__(self, config=None):
        self.config = {
            "use_channels": {"k": True, "b": True, "g": True, "r": True},
            "blur_size": 5,
            "median_blur_size": 7,
            "mask_median_blur_size": 5,
            "min_area": 100,
            "criteria": {
                "k_std": {"max": 15},
                "b_std": {"max": 15},
                "g_std": {"max": 15},
                "r_std": {"max": 15},
                "area_perimeter_ratio": {"min": 0.05, "max": 100000},
                "aspect_ratio": {"min": 1, "max": 6},
            },
        }
        if config is not None:
            for key, value in config.items():
                if (
                    isinstance(value, dict)
                    and key in self.config
                    and isinstance(self.config[key], dict)
                ):
                    self.config[key].update(value)
                else:
                    self.config[key] = value

    @staticmethod
    def extract_kbgr(image):
        b, g, r = cv2.split(image)
        k = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return (
            k.astype("uint8"),
            b.astype("uint8"),
            g.astype("uint8"),
            r.astype("uint8"),
        )

    def create_mask(self, channel, lmin, lmax):
        square = self.config.get("blur_size", 5)
        blurred = cv2.blur(channel, (square, square)).astype("uint8")
        _, binary = cv2.threshold(blurred, lmin, 255, cv2.THRESH_BINARY_INV)
        _, binary2 = cv2.threshold(blurred, lmax, 255, cv2.THRESH_BINARY_INV)
        return binary - binary2

    def make_selection(self, k, b, g, r, mask_values):
        use = self.config["use_channels"]

        if use.get("k", False):
            gray_mask = self.create_mask(
                k, mask_values["k"]["min"], mask_values["k"]["max"]
            )
        else:
            gray_mask = self.create_mask(k, 0, 255)

        if use.get("b", False):
            blue_mask = self.create_mask(
                b, mask_values["b"]["min"], mask_values["b"]["max"]
            )
            gray_mask[blue_mask < 0.5] = 0

        if use.get("g", False):
            green_mask = self.create_mask(
                g, mask_values["g"]["min"], mask_values["g"]["max"]
            )
            gray_mask[green_mask < 0.5] = 0

        if use.get("r", False):
            red_mask = self.create_mask(
                r, mask_values["r"]["min"], mask_values["r"]["max"]
            )
            gray_mask[red_mask < 0.5] = 0

        ms = self.config.get("mask_median_blur_size", 5)
        gray_mask = cv2.medianBlur(gray_mask, ms)
        return gray_mask

    def make_channel_masks(self, k, b, g, r, mask_values):
        """Return individual channel masks for visualization."""
        use = self.config["use_channels"]
        masks = {}
        if use.get("k", False):
            masks["k"] = self.create_mask(
                k, mask_values["k"]["min"], mask_values["k"]["max"]
            )
        if use.get("b", False):
            masks["b"] = self.create_mask(
                b, mask_values["b"]["min"], mask_values["b"]["max"]
            )
        if use.get("g", False):
            masks["g"] = self.create_mask(
                g, mask_values["g"]["min"], mask_values["g"]["max"]
            )
        if use.get("r", False):
            masks["r"] = self.create_mask(
                r, mask_values["r"]["min"], mask_values["r"]["max"]
            )
        return masks

    def find_contours_in_mask(self, mask, min_area=100):
        contours, _ = cv2.findContours(
            mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        return [c for c in contours if cv2.contourArea(c) > min_area]

    def calculate_contour_statistics(self, contour, k, b, g, r):
        mask = np.zeros(k.shape, np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)

        k_v = k[mask > 0.5]
        b_v = b[mask > 0.5]
        g_v = g[mask > 0.5]
        r_v = r[mask > 0.5]

        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        if area == 0:
            area = 1
        if perimeter == 0:
            perimeter = 1
        apr = 16 * area / (perimeter**2)

        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        d1 = np.linalg.norm(box[0] - box[1])
        d2 = np.linalg.norm(box[1] - box[2])
        if d1 == 0:
            d1 = 1
        if d2 == 0:
            d2 = 1
        ar = max(d1, d2) / min(d1, d2)

        return {
            "k_median": float(np.median(k_v)),
            "k_std": float(np.std(k_v)),
            "b_median": float(np.median(b_v)),
            "b_std": float(np.std(b_v)),
            "g_median": float(np.median(g_v)),
            "g_std": float(np.std(g_v)),
            "r_median": float(np.median(r_v)),
            "r_std": float(np.std(r_v)),
            "area": float(area),
            "perimeter": float(perimeter),
            "area_perimeter_ratio": float(apr),
            "aspect_ratio": float(ar),
        }

    def check_criteria(self, stats):
        crit = self.config["criteria"]
        checks = [
            stats["k_std"] < crit["k_std"]["max"],
            stats["b_std"] < crit["b_std"]["max"],
            stats["g_std"] < crit["g_std"]["max"],
            stats["r_std"] < crit["r_std"]["max"],
            crit["area_perimeter_ratio"]["min"]
            < stats["area_perimeter_ratio"]
            < crit["area_perimeter_ratio"]["max"],
            crit["aspect_ratio"]["min"]
            < stats["aspect_ratio"]
            < crit["aspect_ratio"]["max"],
        ]
        return all(checks)

    def check_color_in_range(self, stats, mask_values):
        use = self.config["use_channels"]
        checks = []
        for ch in ["k", "b", "g", "r"]:
            if use.get(ch, False):
                checks.append(
                    mask_values[ch]["min"]
                    < stats[f"{ch}_median"]
                    < mask_values[ch]["max"]
                )
        return all(checks)

    def detect(self, image, mask_values_list, min_area=None):
        if min_area is None:
            min_area = self.config["min_area"]

        blur_sz = self.config.get("median_blur_size", 7)
        processed = cv2.medianBlur(image, blur_sz)
        k, b, g, r = self.extract_kbgr(processed)
        k_o, b_o, g_o, r_o = self.extract_kbgr(image)

        flakes = []
        for idx, mv in enumerate(mask_values_list):
            sel = self.make_selection(k, b, g, r, mv)
            for contour in self.find_contours_in_mask(sel, min_area):
                stats = self.calculate_contour_statistics(contour, k_o, b_o, g_o, r_o)
                if not self.check_criteria(stats):
                    continue
                if not self.check_color_in_range(stats, mv):
                    continue
                M = cv2.moments(contour)
                cx = int(M["m10"] / M["m00"]) if M["m00"] > 0 else 0
                cy = int(M["m01"] / M["m00"]) if M["m00"] > 0 else 0
                flakes.append(
                    {
                        "contour": contour,
                        "interval_idx": idx,
                        "center": (cx, cy),
                        "stats": stats,
                    }
                )
        return flakes, k, b, g, r


# ─── Helpers ─────────────────────────────────────────────────────────────────

def mask_to_rgb(mask, color=(0, 255, 0)):
    """Convert single-channel mask to a colored RGB image."""
    rgb = np.zeros((*mask.shape, 3), dtype=np.uint8)
    rgb[mask > 0] = color
    return rgb


def overlay_mask(image_rgb, mask, color=(0, 255, 0), alpha=0.4):
    """Overlay colored mask on image."""
    out = image_rgb.copy()
    colored = np.zeros_like(out)
    colored[mask > 0] = color
    out = cv2.addWeighted(out, 1.0, colored, alpha, 0)
    return out


def draw_crosshair(image_rgb, x, y, size=20, color=(255, 0, 0)):
    """Draw a crosshair on the image."""
    out = image_rgb.copy()
    h, w = out.shape[:2]
    x = int(np.clip(x, 0, w - 1))
    y = int(np.clip(y, 0, h - 1))
    cv2.line(out, (x - size, y), (x + size, y), color, 2)
    cv2.line(out, (x, y - size), (x, y + size), color, 2)
    cv2.circle(out, (x, y), 4, color, -1)
    return out


# ─── Streamlit App ───────────────────────────────────────────────────────────

st.set_page_config(layout="wide", page_title="Flake Detection Tuner")
st.title("Flake Detection Tuner")

# ─── Sidebar: Image ─────────────────────────────────────────────────────────

st.sidebar.header("Image")
image_dir = Path(__file__).parent / "images"
image_files = sorted(image_dir.glob("*.png")) + sorted(image_dir.glob("*.jpg"))
image_names = [f.name for f in image_files]

if not image_names:
    st.error("No images found in images/ directory")
    st.stop()

selected_name = st.sidebar.selectbox("Select image", image_names, index=3)
image_path = image_dir / selected_name

apply_wb = st.sidebar.checkbox("Apply white balance", value=True)

# Load image
raw_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
if raw_bgr is None:
    st.error(f"Failed to load {image_path}")
    st.stop()

raw_rgb = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)

if apply_wb:
    wb_rgb = whitebalance(raw_rgb)
    wb_bgr = cv2.cvtColor(wb_rgb, cv2.COLOR_RGB2BGR)
else:
    wb_rgb = raw_rgb.copy()
    wb_bgr = raw_bgr.copy()

h, w = wb_rgb.shape[:2]

# ─── Sidebar: Color Picker ──────────────────────────────────────────────────

st.sidebar.header("Color Sampler")
st.sidebar.caption("Set X/Y to sample a pixel from the image as target color.")

sample_x = st.sidebar.number_input("Sample X", 0, w - 1, w // 2, step=10)
sample_y = st.sidebar.number_input("Sample Y", 0, h - 1, h // 2, step=10)

# Read pixel at sample point (from the processed BGR image)
px_bgr = wb_bgr[sample_y, sample_x]
px_b, px_g, px_r = int(px_bgr[0]), int(px_bgr[1]), int(px_bgr[2])
px_k = int(cv2.cvtColor(wb_bgr, cv2.COLOR_BGR2GRAY)[sample_y, sample_x])

st.sidebar.markdown(f"**Sampled KBGR:** K={px_k}, B={px_b}, G={px_g}, R={px_r}")
# Show color swatch
swatch = np.full((30, 120, 3), [px_r, px_g, px_b], dtype=np.uint8)
st.sidebar.image(swatch, caption=f"RGB({px_r}, {px_g}, {px_b})", width=120)

# Manual override
st.sidebar.caption("Or set target values manually:")
col_k, col_b = st.sidebar.columns(2)
target_k = col_k.number_input("Target K", 0, 255, px_k)
target_b = col_b.number_input("Target B", 0, 255, px_b)
col_g, col_r = st.sidebar.columns(2)
target_g = col_g.number_input("Target G", 0, 255, px_g)
target_r = col_r.number_input("Target R", 0, 255, px_r)

# ─── Sidebar: Tolerances ────────────────────────────────────────────────────

st.sidebar.header("Channel Tolerances")
tol_k = st.sidebar.slider("K tolerance (+-)", 1, 80, 15)
tol_b = st.sidebar.slider("B tolerance (+-)", 1, 80, 15)
tol_g = st.sidebar.slider("G tolerance (+-)", 1, 80, 15)
tol_r = st.sidebar.slider("R tolerance (+-)", 1, 80, 15)

# Channel toggles
st.sidebar.header("Channels")
ck, cb = st.sidebar.columns(2)
use_k = ck.checkbox("Use K", value=True)
use_b = cb.checkbox("Use B", value=True)
cg, cr = st.sidebar.columns(2)
use_g = cg.checkbox("Use G", value=True)
use_r = cr.checkbox("Use R", value=True)

# ─── Sidebar: Detection ─────────────────────────────────────────────────────

st.sidebar.header("Detection")
min_area = st.sidebar.slider("Min contour area (px)", 10, 10000, 200, step=10)
blur_size = st.sidebar.slider("Local averaging kernel", 1, 21, 5, step=2)
median_blur = st.sidebar.slider("Preprocessing median blur", 1, 21, 7, step=2)
mask_median = st.sidebar.slider("Post-mask median blur", 1, 21, 5, step=2)

# ─── Sidebar: Criteria ──────────────────────────────────────────────────────

st.sidebar.header("Criteria")
max_std = st.sidebar.slider("Max channel std (all)", 1, 80, 15)
apr_min = st.sidebar.slider("Area/perimeter ratio min", 0.0, 1.0, 0.05, step=0.01)
apr_max = st.sidebar.slider("Area/perimeter ratio max", 1.0, 10.0, 1.0, step=0.1)
ar_min = st.sidebar.slider("Aspect ratio min", 1.0, 3.0, 1.0, step=0.1)
ar_max = st.sidebar.slider("Aspect ratio max", 1.0, 30.0, 6.0, step=0.5)

# ─── Build Config & Mask Values ─────────────────────────────────────────────

mask_values = {
    "k": {"min": max(0, target_k - tol_k), "max": min(255, target_k + tol_k)},
    "b": {"min": max(0, target_b - tol_b), "max": min(255, target_b + tol_b)},
    "g": {"min": max(0, target_g - tol_g), "max": min(255, target_g + tol_g)},
    "r": {"min": max(0, target_r - tol_r), "max": min(255, target_r + tol_r)},
}

config = {
    "use_channels": {"k": use_k, "b": use_b, "g": use_g, "r": use_r},
    "blur_size": blur_size,
    "median_blur_size": median_blur,
    "mask_median_blur_size": mask_median,
    "min_area": min_area,
    "criteria": {
        "k_std": {"max": max_std},
        "b_std": {"max": max_std},
        "g_std": {"max": max_std},
        "r_std": {"max": max_std},
        "area_perimeter_ratio": {"min": apr_min, "max": apr_max},
        "aspect_ratio": {"min": ar_min, "max": ar_max},
    },
}

detector = FlinderDetector(config=config)

# ─── Run Detection ───────────────────────────────────────────────────────────

flakes, k_ch, b_ch, g_ch, r_ch = detector.detect(wb_bgr, [mask_values])
channel_masks = detector.make_channel_masks(k_ch, b_ch, g_ch, r_ch, mask_values)
combined_mask = detector.make_selection(k_ch, b_ch, g_ch, r_ch, mask_values)

# ─── Display: Original Image + Crosshair ────────────────────────────────────

st.subheader("Original Image (with sample point)")
crosshair_img = draw_crosshair(wb_rgb, sample_x, sample_y)
st.image(crosshair_img, width="stretch")

# ─── Display: Mask Ranges ───────────────────────────────────────────────────

st.subheader("Mask Value Ranges")
range_cols = st.columns(4)
for i, ch in enumerate(["k", "b", "g", "r"]):
    if config["use_channels"].get(ch, False):
        range_cols[i].metric(
            f"{ch.upper()} range",
            f"[{mask_values[ch]['min']}, {mask_values[ch]['max']}]",
        )
    else:
        range_cols[i].metric(f"{ch.upper()} range", "disabled")

# ─── Display: Channel Masks ─────────────────────────────────────────────────

st.subheader("Individual Channel Masks")
mask_cols = st.columns(4)
ch_colors = {
    "k": (200, 200, 200),
    "b": (80, 80, 255),
    "g": (80, 255, 80),
    "r": (255, 80, 80),
}
for i, ch in enumerate(["k", "b", "g", "r"]):
    with mask_cols[i]:
        if ch in channel_masks:
            m = channel_masks[ch]
            vis = overlay_mask(wb_rgb, m, ch_colors[ch], alpha=0.5)
            st.image(vis, caption=f"{ch.upper()} mask", width="stretch")
            px_count = int(np.count_nonzero(m))
            st.caption(f"{px_count:,} pixels selected")
        else:
            st.caption(f"{ch.upper()} disabled")

# ─── Display: Combined Mask + Detection ──────────────────────────────────────

st.subheader("Combined Mask & Detection Result")
res_cols = st.columns(2)

with res_cols[0]:
    combined_vis = overlay_mask(wb_rgb, combined_mask, (0, 255, 255), alpha=0.5)
    st.image(combined_vis, caption="Combined mask", width="stretch")
    total_px = int(np.count_nonzero(combined_mask))
    st.caption(f"{total_px:,} pixels in combined mask")

with res_cols[1]:
    # Draw detection results
    det_img = wb_rgb.copy()
    for flake in flakes:
        cv2.drawContours(det_img, [flake["contour"]], -1, (0, 255, 0), 2)
        cx, cy = flake["center"]
        cv2.circle(det_img, (cx, cy), 6, (255, 0, 0), -1)
        label = f"A={int(flake['stats']['area'])}"
        cv2.putText(
            det_img,
            label,
            (cx + 10, cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            3,
        )
        cv2.putText(
            det_img,
            label,
            (cx + 10, cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            1,
        )
    st.image(det_img, caption=f"Detected: {len(flakes)} flakes", width="stretch")

# ─── Display: Flake Details Table ────────────────────────────────────────────

if flakes:
    st.subheader(f"Detected Flakes ({len(flakes)})")
    rows = []
    for i, f in enumerate(flakes):
        s = f["stats"]
        rows.append(
            {
                "#": i,
                "Center": f"{f['center'][0]}, {f['center'][1]}",
                "Area (px)": f"{s['area']:.0f}",
                "K median": f"{s['k_median']:.0f}",
                "B median": f"{s['b_median']:.0f}",
                "G median": f"{s['g_median']:.0f}",
                "R median": f"{s['r_median']:.0f}",
                "K std": f"{s['k_std']:.1f}",
                "B std": f"{s['b_std']:.1f}",
                "G std": f"{s['g_std']:.1f}",
                "R std": f"{s['r_std']:.1f}",
                "A/P ratio": f"{s['area_perimeter_ratio']:.3f}",
                "Aspect": f"{s['aspect_ratio']:.2f}",
            }
        )
    st.dataframe(rows, width="stretch")
else:
    st.info("No flakes detected with current parameters. Try widening tolerances or lowering min area.")

# ─── Export Config ───────────────────────────────────────────────────────────

st.subheader("Export Config")
st.caption("Copy this dict into your notebook to use these tuned parameters.")
export_config = f"""calibration = {{
    'thickness': [1],
    'k':         [{target_k}],
    'b':         [{target_b}],
    'g':         [{target_g}],
    'r':         [{target_r}],
    'k_error':   [{tol_k}],
    'b_error':   [{tol_b}],
    'g_error':   [{tol_g}],
    'r_error':   [{tol_r}],
    'number_of_intervals': 1,
}}

config = {{
    'use_channels': {{'k': {use_k}, 'b': {use_b}, 'g': {use_g}, 'r': {use_r}}},
    'blur_size': {blur_size},
    'median_blur_size': {median_blur},
    'mask_median_blur_size': {mask_median},
    'min_area': {min_area},
    'criteria': {{
        'k_std': {{'max': {max_std}}},
        'b_std': {{'max': {max_std}}},
        'g_std': {{'max': {max_std}}},
        'r_std': {{'max': {max_std}}},
        'area_perimeter_ratio': {{'min': {apr_min}, 'max': {apr_max}}},
        'aspect_ratio': {{'min': {ar_min}, 'max': {ar_max}}},
    }}
}}"""
st.code(export_config, language="python")
