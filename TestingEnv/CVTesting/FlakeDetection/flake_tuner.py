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
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random

from Flinder import FlinderDetector


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


# ─── Helpers ─────────────────────────────────────────────────────────────────

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


def draw_flakes_on_image(image_rgb, flakes, undersized=None):
    """Draw detected flake contours and labels on an RGB image.

    Undersized flakes (if provided) are drawn in red instead of green.
    """
    det = image_rgb.copy()
    for flake in flakes:
        cv2.drawContours(det, [flake["contour"]], -1, (0, 255, 0), 2)
        cx, cy = flake["center"]
        cv2.circle(det, (cx, cy), 6, (255, 0, 0), -1)
        label = f"A={int(flake['stats']['area'])}"
        cv2.putText(det, label, (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(det, label, (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    for flake in (undersized or []):
        cv2.drawContours(det, [flake["contour"]], -1, (255, 60, 60), 2)
        cx, cy = flake["center"]
        cv2.circle(det, (cx, cy), 6, (180, 0, 0), -1)
        label = f"A={int(flake['stats']['area'])}"
        cv2.putText(det, label, (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(det, label, (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 60, 60), 1)
    return det


def load_and_preprocess(path, apply_wb, background=None):
    """Load image, optionally correct vignetting & white-balance.

    Returns (raw_bgr, wb_bgr, wb_rgb) or (None, None, None).
    raw_bgr: vignette-corrected but no white balance (for detection).
    wb_bgr/wb_rgb: with white balance applied (for display).
    """
    raw_bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if raw_bgr is None:
        return None, None, None
    if background is not None and raw_bgr.shape[:2] == background.shape[:2]:
        raw_bgr = FlinderDetector.correct_vignetting(raw_bgr, background)
    raw_rgb = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)
    if apply_wb:
        wb_rgb = whitebalance(raw_rgb)
        wb_bgr = cv2.cvtColor(wb_rgb, cv2.COLOR_RGB2BGR)
    else:
        wb_rgb = raw_rgb.copy()
        wb_bgr = raw_bgr.copy()
    return raw_bgr, wb_bgr, wb_rgb


def _get_or_compute_background(collection_dir, n_sample):
    """Load cached background from disk, or compute and save it.

    The background .npy file is saved inside the collection directory so it
    persists across Streamlit sessions and app restarts.
    """
    collection_dir = Path(collection_dir)
    cache_path = collection_dir / f"_vignetting_bg_n{n_sample}.npy"

    mem_key = str(cache_path)
    if mem_key in st.session_state:
        return st.session_state[mem_key]

    if cache_path.exists():
        bg = np.load(str(cache_path))
        st.session_state[mem_key] = bg
        return bg

    all_paths = sorted(collection_dir.glob("*.png")) + sorted(collection_dir.glob("*.jpg"))
    if len(all_paths) < 5:
        return None
    bg = FlinderDetector.compute_background(all_paths, n_sample=n_sample)
    np.save(str(cache_path), bg)
    st.session_state[mem_key] = bg
    return bg


# ─── Default Config ──────────────────────────────────────────────────────────
# Edit these to change the startup defaults for all sliders.

DEFAULT_CALIBRATION = {
    "thickness": [1],
    "k": [120],
    "b": [126],
    "g": [119],
    "r": [118],
    "k_error": [6],
    "b_error": [6],
    "g_error": [6],
    "r_error": [4],
    "number_of_intervals": 1,
}

DEFAULT_CONFIG = {
    "use_channels": {"k": True, "b": True, "g": True, "r": True},
    "blur_size": 5,
    "median_blur_size": 7,
    "mask_median_blur_size": 5,
    "min_area": 200,
    "criteria": {
        "k_std": {"max": 15},
        "b_std": {"max": 15},
        "g_std": {"max": 15},
        "r_std": {"max": 15},
        "area_perimeter_ratio": {"min": 0.05, "max": 1.0},
        "aspect_ratio": {"min": 1.0, "max": 6.0},
        "points_per_unit_length": {"min": 0.0, "max": 10.0},
    },
}

# ─── Streamlit App ───────────────────────────────────────────────────────────

st.set_page_config(layout="wide", page_title="Flake Detection Tuner")
st.title("Flake Detection Tuner")

# ─── Sidebar: Shared Parameters ──────────────────────────────────────────────

_cal = DEFAULT_CALIBRATION
_cfg = DEFAULT_CONFIG
_crit = _cfg["criteria"]
_use = _cfg["use_channels"]

st.sidebar.header("Preprocessing")
apply_wb = st.sidebar.checkbox("Apply white balance", value=True)
apply_vignetting = st.sidebar.checkbox("Apply vignetting correction", value=True,
    help="Builds a per-pixel background from the collection and divides each image by it. "
         "Removes spatially-varying illumination (vignetting, uneven lighting).")

if apply_vignetting:
    n_bg_samples = st.sidebar.slider("Background sample count", 20, 500, 100, step=10,
        help="Number of images to sample for computing the per-pixel median background.")

# Color target (defaults from calibration)
st.sidebar.header("Target Color (KBGR)")
st.sidebar.caption("Set manually, or use the color sampler in the Tuner tab.")
col_k, col_b = st.sidebar.columns(2)
target_k = col_k.number_input("Target K", 0, 255, _cal["k"][0])
target_b = col_b.number_input("Target B", 0, 255, _cal["b"][0])
col_g, col_r = st.sidebar.columns(2)
target_g = col_g.number_input("Target G", 0, 255, _cal["g"][0])
target_r = col_r.number_input("Target R", 0, 255, _cal["r"][0])

# Tolerances (defaults from calibration errors)
st.sidebar.header("Channel Tolerances")
tol_k = st.sidebar.slider("K tolerance (+-)", 1, 80, _cal["k_error"][0])
tol_b = st.sidebar.slider("B tolerance (+-)", 1, 80, _cal["b_error"][0])
tol_g = st.sidebar.slider("G tolerance (+-)", 1, 80, _cal["g_error"][0])
tol_r = st.sidebar.slider("R tolerance (+-)", 1, 80, _cal["r_error"][0])

# Channel toggles
st.sidebar.header("Channels")
ck, cb = st.sidebar.columns(2)
use_k = ck.checkbox("Use K", value=_use["k"])
use_b = cb.checkbox("Use B", value=_use["b"])
cg, cr = st.sidebar.columns(2)
use_g = cg.checkbox("Use G", value=_use["g"])
use_r = cr.checkbox("Use R", value=_use["r"])

# Detection params
st.sidebar.header("Detection")
min_area = st.sidebar.slider("Min contour area (px)", 10, 10000, _cfg["min_area"], step=10)
blur_size = st.sidebar.slider("Local averaging kernel", 1, 21, _cfg["blur_size"], step=2)
median_blur = st.sidebar.slider("Preprocessing median blur", 1, 21, _cfg["median_blur_size"], step=2)
mask_median = st.sidebar.slider("Post-mask median blur", 1, 21, _cfg["mask_median_blur_size"], step=2)

# Criteria
st.sidebar.header("Criteria")
max_std = st.sidebar.slider("Max channel std (all)", 1, 80, _crit["k_std"]["max"])
apr_min = st.sidebar.slider("Area/perimeter ratio min", 0.0, 1.0, _crit["area_perimeter_ratio"]["min"], step=0.01)
apr_max = st.sidebar.slider("Area/perimeter ratio max", 1.0, 10.0, _crit["area_perimeter_ratio"]["max"], step=0.1)
ar_min = st.sidebar.slider("Aspect ratio min", 1.0, 3.0, _crit["aspect_ratio"]["min"], step=0.1)
ar_max = st.sidebar.slider("Aspect ratio max", 1.0, 30.0, _crit["aspect_ratio"]["max"], step=0.5)
ppul_min = st.sidebar.slider("Points/unit length min", 0.0, 5.0, _crit["points_per_unit_length"]["min"], step=0.1)
ppul_max = st.sidebar.slider("Points/unit length max", 0.5, 20.0, _crit["points_per_unit_length"]["max"], step=0.5)

# Size filter (post-detection)
st.sidebar.header("Size Filter")
filter_by_area = st.sidebar.checkbox("Enable area filter", value=False,
    help="Post-detection filter: separate flakes by contour area. "
         "Does not affect which contours are found (that's min contour area above).")
if filter_by_area:
    area_threshold = st.sidebar.slider("Area threshold (px)", 10, 50000, 500, step=10)
    area_filter_mode = st.sidebar.radio("Undersized flakes", ["Highlight in red", "Discard"])
else:
    area_threshold = 0
    area_filter_mode = "Discard"

# ─── Build shared config & mask values ───────────────────────────────────────

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
        "points_per_unit_length": {"min": ppul_min, "max": ppul_max},
    },
}

detector = FlinderDetector(config=config)

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab_tuner, tab_dataset = st.tabs(["Single Image Tuner", "Run on Dataset"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: Single Image Tuner
# ═══════════════════════════════════════════════════════════════════════════════

with tab_tuner:
    # Image selector
    image_dir = Path(__file__).parent / "images"
    if image_dir.exists():
        image_files = sorted(image_dir.glob("*.png")) + sorted(image_dir.glob("*.jpg"))
    else:
        image_files = []
    image_names = [f.name for f in image_files]

    if not image_names:
        st.warning(
            "No images found in `images/` directory. "
            "Create an `images/` folder next to `flake_tuner.py` and add some .png/.jpg files, "
            "or use the **Run on Dataset** tab instead."
        )
        st.stop()

    selected_name = st.selectbox("Select image", image_names,
                                 index=min(3, len(image_names) - 1))
    if selected_name is None:
        st.stop()
    image_path = image_dir / selected_name

    # Vignetting correction — build list of background sources
    tuner_bg = None
    if apply_vignetting:
        tuner_bg_sources = []
        tuner_bg_labels = []

        dataset_root_tuner = Path(__file__).parent / "Dataset"
        if dataset_root_tuner.exists():
            coll_dirs = set()
            for p in dataset_root_tuner.rglob("*.png"):
                coll_dirs.add(p.parent)
            for d in sorted(coll_dirs):
                tuner_bg_sources.append(d)
                tuner_bg_labels.append(f"Dataset/{d.relative_to(dataset_root_tuner)}")

        if len(image_files) >= 5:
            tuner_bg_sources.append(image_dir)
            tuner_bg_labels.append(f"images/ ({len(image_files)} images)")

        if tuner_bg_sources:
            tuner_bg_idx = st.selectbox("Background source collection", range(len(tuner_bg_labels)),
                                        format_func=lambda i: tuner_bg_labels[i],
                                        help="Pick the collection folder to compute the vignetting background from. "
                                             "Needs many images of mostly bare substrate.",
                                        key="tuner_bg_collection")
            bg_dir = tuner_bg_sources[tuner_bg_idx]
            bg_count = len(sorted(bg_dir.glob("*.png")) + sorted(bg_dir.glob("*.jpg")))
            with st.spinner(f"Loading vignetting background (sampling {min(n_bg_samples, bg_count)} of {bg_count} images)..."):
                tuner_bg = _get_or_compute_background(bg_dir, n_bg_samples)
            if tuner_bg is not None:
                st.caption(f"Background loaded from `{tuner_bg_labels[tuner_bg_idx]}` (cached to disk).")
        else:
            st.info("No image sources with 5+ images found. Vignetting correction disabled for tuner.")

    raw_bgr, wb_bgr, wb_rgb = load_and_preprocess(image_path, apply_wb, background=tuner_bg)
    if raw_bgr is None:
        st.error(f"Failed to load {image_path}")
        st.stop()

    h, w = wb_rgb.shape[:2]

    # ── Run detection ────────────────────────────────────────────────────
    all_flakes, k_ch, b_ch, g_ch, r_ch = detector.detect(raw_bgr, [mask_values])
    channel_masks = detector.make_channel_masks(k_ch, b_ch, g_ch, r_ch, mask_values)
    combined_mask = detector.make_selection(k_ch, b_ch, g_ch, r_ch, mask_values)

    # Apply size filter
    if filter_by_area:
        flakes = [f for f in all_flakes if f["stats"]["area"] >= area_threshold]
        undersized_flakes = [f for f in all_flakes if f["stats"]["area"] < area_threshold]
        undersized_display = undersized_flakes if area_filter_mode == "Highlight in red" else []
    else:
        flakes = all_flakes
        undersized_display = []

    # ── Combined + Detection ─────────────────────────────────────────────
    st.subheader("Combined Mask & Detection Result")
    ch_colors = {"k": (200, 200, 200), "b": (80, 80, 255), "g": (80, 255, 80), "r": (255, 80, 80)}
    res_cols = st.columns(2)
    with res_cols[0]:
        color_overlay = np.zeros(wb_rgb.shape, dtype=np.float32)
        overlap_count = np.zeros(wb_rgb.shape[:2], dtype=np.float32)
        for ch, ch_color in ch_colors.items():
            if ch in channel_masks:
                m = channel_masks[ch] > 0
                color_overlay[m] += np.array(ch_color, dtype=np.float32)
                overlap_count[m] += 1.0
        has_color = overlap_count > 0
        color_overlay[has_color] /= overlap_count[has_color, np.newaxis]
        color_overlay = np.clip(color_overlay, 0, 255).astype(np.uint8)
        combined_vis = wb_rgb.copy()
        combined_vis[has_color] = cv2.addWeighted(
            wb_rgb, 1.0, color_overlay, 0.5, 0
        )[has_color]
        st.image(combined_vis, caption="Combined mask (per-channel colors)", width="stretch")
        st.caption(f"{int(np.count_nonzero(combined_mask)):,} px in combined mask")
    with res_cols[1]:
        det_img = draw_flakes_on_image(wb_rgb, flakes, undersized_display)
        caption = f"Detected: {len(flakes)} flakes"
        if undersized_display:
            caption += f" ({len(undersized_display)} undersized in red)"
        st.image(det_img, caption=caption, width="stretch")

    # ── ANDed mask + contour interpretability ────────────────────────────
    st.subheader("ANDed Mask & Contour Analysis")
    and_cols = st.columns(3)

    with and_cols[0]:
        mask_binary = (combined_mask > 0).astype(np.uint8) * 255
        st.image(mask_binary, caption="ANDed binary mask", width="stretch")
        st.caption(f"{int(np.count_nonzero(combined_mask)):,} px")

    all_contours = detector.find_contours_in_mask(combined_mask, min_area)

    rejected_criteria = []
    rejected_color = []
    for contour in all_contours:
        if any(np.array_equal(contour, f["contour"]) for f in all_flakes):
            continue
        stats = detector.calculate_contour_statistics(contour, k_ch, b_ch, g_ch, r_ch)
        if not detector.check_criteria(stats):
            rejected_criteria.append((contour, stats))
        else:
            rejected_color.append((contour, stats))

    def _draw_contour_categories(base_img):
        out = base_img.copy()
        for f in flakes:
            cv2.drawContours(out, [f["contour"]], -1, (0, 255, 0), 2)
        for f in undersized_display:
            cv2.drawContours(out, [f["contour"]], -1, (255, 255, 0), 2)
        for contour, _ in rejected_criteria:
            cv2.drawContours(out, [contour], -1, (255, 60, 60), 2)
        for contour, _ in rejected_color:
            cv2.drawContours(out, [contour], -1, (255, 165, 0), 2)
        return out

    with and_cols[1]:
        mask_rgb = cv2.cvtColor(mask_binary, cv2.COLOR_GRAY2RGB)
        st.image(_draw_contour_categories(mask_rgb), caption="Contours on mask", width="stretch")
        legend = (
            f":green[Green] = accepted ({len(flakes)})  \n"
            f":red[Red] = rejected by shape/std ({len(rejected_criteria)})  \n"
            f":orange[Orange] = rejected by color ({len(rejected_color)})"
        )
        if undersized_display:
            legend = (
                f":green[Green] = accepted ({len(flakes)})  \n"
                f"Yellow = undersized ({len(undersized_display)})  \n"
                f":red[Red] = rejected by shape/std ({len(rejected_criteria)})  \n"
                f":orange[Orange] = rejected by color ({len(rejected_color)})"
            )
        st.caption(legend)

    with and_cols[2]:
        st.image(_draw_contour_categories(wb_rgb), caption="Contours on image", width="stretch")
        st.caption(f"{len(all_contours)} total contours above min area")

    # ── Mask ranges ──────────────────────────────────────────────────────
    st.subheader("Mask Value Ranges")
    range_cols = st.columns(4)
    for i, ch in enumerate(["k", "b", "g", "r"]):
        enabled = config["use_channels"].get(ch, False)
        range_cols[i].metric(
            f"{ch.upper()} range",
            f"[{mask_values[ch]['min']}, {mask_values[ch]['max']}]" if enabled else "disabled",
        )

    # ── Raw channels ────────────────────────────────────────────────────
    st.subheader("Extracted Channels")
    ch_images = {"k": k_ch, "b": b_ch, "g": g_ch, "r": r_ch}
    raw_cols = st.columns(4)
    for i, ch in enumerate(["k", "b", "g", "r"]):
        with raw_cols[i]:
            st.image(ch_images[ch], caption=f"{ch.upper()} channel", width="stretch", clamp=True)

    # ── Channel masks ────────────────────────────────────────────────────
    st.subheader("Individual Channel Masks")
    mask_cols = st.columns(4)
    for i, ch in enumerate(["k", "b", "g", "r"]):
        with mask_cols[i]:
            if ch in channel_masks:
                mask_vis = (channel_masks[ch] > 0).astype(np.uint8) * 255
                st.image(mask_vis, caption=f"{ch.upper()} mask", width="stretch")
                st.caption(f"{int(np.count_nonzero(channel_masks[ch])):,} px")
            else:
                st.caption(f"{ch.upper()} disabled")

    # ── Flake details table ──────────────────────────────────────────────
    table_flakes = flakes + undersized_display
    if table_flakes:
        header = f"Detected Flakes ({len(flakes)})"
        if undersized_display:
            header += f" + {len(undersized_display)} undersized"
        st.subheader(header)
        rows = []
        for i, f in enumerate(table_flakes):
            s = f["stats"]
            rows.append({
                "#": i,
                "Status": "accepted" if i < len(flakes) else "undersized",
                "Center": f"{f['center'][0]}, {f['center'][1]}",
                "Area (px)": f"{s['area']:.0f}",
                "K med": f"{s['k_median']:.0f}", "B med": f"{s['b_median']:.0f}",
                "G med": f"{s['g_median']:.0f}", "R med": f"{s['r_median']:.0f}",
                "K std": f"{s['k_std']:.1f}", "B std": f"{s['b_std']:.1f}",
                "G std": f"{s['g_std']:.1f}", "R std": f"{s['r_std']:.1f}",
                "A/P": f"{s['area_perimeter_ratio']:.3f}",
                "Aspect": f"{s['aspect_ratio']:.2f}",
                "Pts/len": f"{s['points_per_unit_length']:.2f}",
            })
        st.dataframe(rows, width="stretch")
    else:
        st.info("No flakes detected. Try widening tolerances or lowering min area."
                + (" (area filter is active)" if filter_by_area else ""))

    # ── Color sampler ────────────────────────────────────────────────────
    st.subheader("Color Sampler")
    sc1, sc2 = st.columns([3, 1])
    with sc1:
        sample_x = st.number_input("Sample X", 0, w - 1, w // 2, step=10)
        sample_y = st.number_input("Sample Y", 0, h - 1, h // 2, step=10)
    with sc2:
        px_k = int(k_ch[sample_y, sample_x])
        px_b = int(b_ch[sample_y, sample_x])
        px_g = int(g_ch[sample_y, sample_x])
        px_r = int(r_ch[sample_y, sample_x])
        st.markdown(f"**Sampled:** K={px_k} B={px_b} G={px_g} R={px_r}")
        swatch = np.full((40, 100, 3), [px_r, px_g, px_b], dtype=np.uint8)
        st.image(swatch, caption=f"RGB({px_r},{px_g},{px_b})", width=100)
        st.caption("Copy these into the sidebar Target Color fields.")

    crosshair_img = draw_crosshair(wb_rgb, sample_x, sample_y)
    st.image(crosshair_img, caption="Original (click position shown)", width="stretch")

    # ── Export config ────────────────────────────────────────────────────
    with st.expander("Export Config"):
        st.caption("Copy this into your notebook.")
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
        'points_per_unit_length': {{'min': {ppul_min}, 'max': {ppul_max}}},
    }}
}}"""
        st.code(export_config, language="python")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: Run on Dataset
# ═══════════════════════════════════════════════════════════════════════════════

with tab_dataset:
    st.subheader("Run Detection on Dataset Folder")
    st.caption("Uses the parameters configured in the sidebar.")

    # ── Folder selection ─────────────────────────────────────────────────
    dataset_root = Path(__file__).parent / "Dataset"
    if not dataset_root.exists():
        st.warning(f"No Dataset/ directory found at {dataset_root}")
        st.stop()

    # Walk dataset_root to find folders that directly contain .png files
    candidate_dirs = set()
    for p in dataset_root.rglob("*.png"):
        candidate_dirs.add(p.parent)
    candidate_dirs = sorted(candidate_dirs)

    if not candidate_dirs:
        st.warning("No image folders found in Dataset/")
        st.stop()

    dir_labels = [str(d.relative_to(dataset_root)) for d in candidate_dirs]
    selected_dir_idx = st.selectbox("Select dataset folder", range(len(dir_labels)),
                                     format_func=lambda i: dir_labels[i])
    selected_dir = candidate_dirs[selected_dir_idx]

    # Count images
    all_images = sorted(selected_dir.glob("*.png")) + sorted(selected_dir.glob("*.jpg"))
    total_available = len(all_images)
    st.write(f"**{total_available}** images in `{dir_labels[selected_dir_idx]}`")

    # Compute vignetting background for this collection
    dataset_bg = None
    if apply_vignetting and total_available >= 5:
        with st.spinner(f"Loading vignetting background (sampling {min(n_bg_samples, total_available)} of {total_available} images)..."):
            dataset_bg = _get_or_compute_background(selected_dir, n_bg_samples)
        if dataset_bg is not None:
            st.caption(f"Background loaded (cached to `_vignetting_bg_n{n_bg_samples}.npy` in collection folder).")
    elif apply_vignetting:
        st.warning("Need at least 5 images for vignetting correction.")

    # Options
    opt_cols = st.columns(4)
    show_mode = opt_cols[0].radio("Show", ["Only with flakes", "All images"], index=1)
    max_display = opt_cols[1].number_input("Max images to display", 10, 50, 50, step=10)
    cols_per_row = opt_cols[2].number_input("Columns", 1, 6, 3)
    n_workers = opt_cols[3].number_input("Workers", 1, 16, min(8, total_available), step=1)

    # Sample size
    sample_cols = st.columns(2)
    max_compute = sample_cols[0].number_input(
        "Max images to process", 1, total_available, min(total_available, 50), step=10,
        help="Number of images to process. Default: all images.",
    )
    if max_compute < total_available:
        sample_cols[1].caption(f"Will randomly sample **{max_compute}** of {total_available} images.")
        sampled_images = random.sample(all_images, max_compute)
    else:
        sampled_images = all_images

    # ── Run button ───────────────────────────────────────────────────────
    if st.button("Run Detection", type="primary", use_container_width=True):

        images_to_run = sampled_images
        progress = st.progress(0, text="Starting parallel detection...")
        status_text = st.empty()
        total = len(images_to_run)
        t_start = time.perf_counter()

        def _detect_one(img_path):
            raw_bgr_w, wb_bgr_w, wb_rgb_w = load_and_preprocess(img_path, apply_wb, background=dataset_bg)
            if raw_bgr_w is None:
                return None
            flakes_w = detector.detect_flakes(raw_bgr_w, [mask_values])
            return (img_path, flakes_w, wb_rgb_w)

        results = [None] * total
        done_count = 0

        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            future_to_idx = {
                executor.submit(_detect_one, p): i
                for i, p in enumerate(images_to_run)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                result = future.result()
                if result is not None:
                    results[idx] = result
                done_count += 1
                elapsed = time.perf_counter() - t_start
                rate = done_count / elapsed
                eta = (total - done_count) / rate if rate > 0 else 0
                progress.progress(
                    done_count / total,
                    text=f"{done_count}/{total} done — {rate:.1f} img/s — ETA {eta:.0f}s",
                )

        # Filter out Nones (failed loads)
        results = [r for r in results if r is not None]

        elapsed_total = time.perf_counter() - t_start
        progress.empty()

        total_processed = len(results)
        all_flake_count = sum(len(f) for _, f, _ in results)

        st.success(
            f"Done in **{elapsed_total:.1f}s** ({total_processed/elapsed_total:.1f} img/s). "
            f"Processed **{total_processed}** images. "
            f"**{all_flake_count}** total flakes found."
        )

        st.session_state["dataset_results"] = results

    # ── Display results (from session state) ─────────────────────────────
    if "dataset_results" in st.session_state:
        results = st.session_state["dataset_results"]

        # Apply size filter to cached results (re-draws on every rerun, no re-detection needed)
        filtered = []
        for (img_path, flakes_raw, wb_rgb_w) in results:
            if filter_by_area:
                passing = [f for f in flakes_raw if f["stats"]["area"] >= area_threshold]
                undersized = [f for f in flakes_raw if f["stats"]["area"] < area_threshold]
                undersized_show = undersized if area_filter_mode == "Highlight in red" else []
            else:
                passing = flakes_raw
                undersized_show = []
            det_img = draw_flakes_on_image(wb_rgb_w, passing, undersized_show)
            filtered.append((img_path, passing, undersized_show, det_img))

        with_flakes = [(p, f, u, img) for p, f, u, img in filtered if len(f) > 0]
        total_flakes = sum(len(f) for _, f, _, _ in filtered)
        total_undersized = sum(len(u) for _, _, u, _ in filtered)

        # Summary metrics
        mcols = st.columns(4 if filter_by_area else 3)
        mcols[0].metric("Images processed", len(results))
        mcols[1].metric("Images with flakes", len(with_flakes))
        mcols[2].metric("Total flakes", total_flakes)
        if filter_by_area:
            mcols[3].metric("Undersized", total_undersized)

        # Pick which results to show
        display_list = with_flakes if show_mode == "Only with flakes" else filtered
        display_list = display_list[:max_display]

        if not display_list:
            st.info("No images to display with current filter.")
        else:
            st.subheader(f"Results ({len(display_list)} images shown)")

            for row_start in range(0, len(display_list), cols_per_row):
                row_items = display_list[row_start : row_start + cols_per_row]
                cols = st.columns(cols_per_row)
                for col_idx, (img_path, flakes_item, undersized_item, det_img) in enumerate(row_items):
                    with cols[col_idx]:
                        n = len(flakes_item)
                        caption = f"{img_path.name} — {n} flake{'s' if n != 1 else ''}"
                        if undersized_item:
                            caption += f" ({len(undersized_item)} undersized)"
                        st.image(det_img, caption=caption, width="stretch")

            # ── Aggregate flake table ────────────────────────────────────
            if with_flakes:
                with st.expander("All detected flakes (table)"):
                    all_rows = []
                    for img_path, flakes_item, undersized_item, _ in with_flakes:
                        for status, flist in [("accepted", flakes_item), ("undersized", undersized_item)]:
                            for i, f in enumerate(flist):
                                s = f["stats"]
                                all_rows.append({
                                    "Image": img_path.name,
                                    "Status": status,
                                    "Center": f"{f['center'][0]},{f['center'][1]}",
                                    "Area": f"{s['area']:.0f}",
                                    "K": f"{s['k_median']:.0f}",
                                    "B": f"{s['b_median']:.0f}",
                                    "G": f"{s['g_median']:.0f}",
                                    "R": f"{s['r_median']:.0f}",
                                    "K std": f"{s['k_std']:.1f}",
                                    "Aspect": f"{s['aspect_ratio']:.2f}",
                                })
                    st.dataframe(all_rows, width="stretch")
