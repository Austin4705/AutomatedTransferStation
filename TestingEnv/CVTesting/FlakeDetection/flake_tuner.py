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


def draw_flakes_on_image(image_rgb, flakes):
    """Draw detected flake contours and labels on an RGB image."""
    det = image_rgb.copy()
    for flake in flakes:
        cv2.drawContours(det, [flake["contour"]], -1, (0, 255, 0), 2)
        cx, cy = flake["center"]
        cv2.circle(det, (cx, cy), 6, (255, 0, 0), -1)
        label = f"A={int(flake['stats']['area'])}"
        cv2.putText(det, label, (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(det, label, (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    return det


def load_and_preprocess(path, apply_wb):
    """Load image, optionally white-balance. Returns (bgr, rgb) or (None, None)."""
    raw_bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if raw_bgr is None:
        return None, None
    raw_rgb = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)
    if apply_wb:
        wb_rgb = whitebalance(raw_rgb)
        wb_bgr = cv2.cvtColor(wb_rgb, cv2.COLOR_RGB2BGR)
    else:
        wb_rgb = raw_rgb.copy()
        wb_bgr = raw_bgr.copy()
    return wb_bgr, wb_rgb


# ─── Default Config ──────────────────────────────────────────────────────────
# Edit these to change the startup defaults for all sliders.

DEFAULT_CALIBRATION = {
    "thickness": [1],
    "k": [161],
    "b": [166],
    "g": [162],
    "r": [158],
    "k_error": [6],
    "b_error": [5],
    "g_error": [6],
    "r_error": [6],
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

    wb_bgr, wb_rgb = load_and_preprocess(image_path, apply_wb)
    if wb_bgr is None:
        st.error(f"Failed to load {image_path}")
        st.stop()

    h, w = wb_rgb.shape[:2]

    # ── Color sampler ────────────────────────────────────────────────────
    st.subheader("Color Sampler")
    sc1, sc2 = st.columns([3, 1])
    with sc1:
        sample_x = st.number_input("Sample X", 0, w - 1, w // 2, step=10)
        sample_y = st.number_input("Sample Y", 0, h - 1, h // 2, step=10)
    with sc2:
        px_bgr = wb_bgr[sample_y, sample_x]
        px_b, px_g, px_r = int(px_bgr[0]), int(px_bgr[1]), int(px_bgr[2])
        px_k = int(cv2.cvtColor(wb_bgr, cv2.COLOR_BGR2GRAY)[sample_y, sample_x])
        st.markdown(f"**Sampled:** K={px_k} B={px_b} G={px_g} R={px_r}")
        swatch = np.full((40, 100, 3), [px_r, px_g, px_b], dtype=np.uint8)
        st.image(swatch, caption=f"RGB({px_r},{px_g},{px_b})", width=100)
        st.caption("Copy these into the sidebar Target Color fields.")

    crosshair_img = draw_crosshair(wb_rgb, sample_x, sample_y)
    st.image(crosshair_img, caption="Original (click position shown)", width="stretch")

    # ── Run detection ────────────────────────────────────────────────────
    flakes, k_ch, b_ch, g_ch, r_ch = detector.detect(wb_bgr, [mask_values])
    channel_masks = detector.make_channel_masks(k_ch, b_ch, g_ch, r_ch, mask_values)
    combined_mask = detector.make_selection(k_ch, b_ch, g_ch, r_ch, mask_values)

    # ── Mask ranges ──────────────────────────────────────────────────────
    st.subheader("Mask Value Ranges")
    range_cols = st.columns(4)
    for i, ch in enumerate(["k", "b", "g", "r"]):
        enabled = config["use_channels"].get(ch, False)
        range_cols[i].metric(
            f"{ch.upper()} range",
            f"[{mask_values[ch]['min']}, {mask_values[ch]['max']}]" if enabled else "disabled",
        )

    # ── Channel masks ────────────────────────────────────────────────────
    st.subheader("Individual Channel Masks")
    ch_colors = {"k": (200, 200, 200), "b": (80, 80, 255), "g": (80, 255, 80), "r": (255, 80, 80)}
    mask_cols = st.columns(4)
    for i, ch in enumerate(["k", "b", "g", "r"]):
        with mask_cols[i]:
            if ch in channel_masks:
                vis = overlay_mask(wb_rgb, channel_masks[ch], ch_colors[ch], alpha=0.5)
                st.image(vis, caption=f"{ch.upper()} mask", width="stretch")
                st.caption(f"{int(np.count_nonzero(channel_masks[ch])):,} px")
            else:
                st.caption(f"{ch.upper()} disabled")

    # ── Combined + Detection ─────────────────────────────────────────────
    st.subheader("Combined Mask & Detection Result")
    res_cols = st.columns(2)
    with res_cols[0]:
        combined_vis = overlay_mask(wb_rgb, combined_mask, (0, 255, 255), alpha=0.5)
        st.image(combined_vis, caption="Combined mask", width="stretch")
        st.caption(f"{int(np.count_nonzero(combined_mask)):,} px in combined mask")
    with res_cols[1]:
        det_img = draw_flakes_on_image(wb_rgb, flakes)
        st.image(det_img, caption=f"Detected: {len(flakes)} flakes", width="stretch")

    # ── Flake details table ──────────────────────────────────────────────
    if flakes:
        st.subheader(f"Detected Flakes ({len(flakes)})")
        rows = []
        for i, f in enumerate(flakes):
            s = f["stats"]
            rows.append({
                "#": i,
                "Center": f"{f['center'][0]}, {f['center'][1]}",
                "Area (px)": f"{s['area']:.0f}",
                "K med": f"{s['k_median']:.0f}", "B med": f"{s['b_median']:.0f}",
                "G med": f"{s['g_median']:.0f}", "R med": f"{s['r_median']:.0f}",
                "K std": f"{s['k_std']:.1f}", "B std": f"{s['b_std']:.1f}",
                "G std": f"{s['g_std']:.1f}", "R std": f"{s['r_std']:.1f}",
                "A/P": f"{s['area_perimeter_ratio']:.3f}",
                "Aspect": f"{s['aspect_ratio']:.2f}",
            })
        st.dataframe(rows, width="stretch")
    else:
        st.info("No flakes detected. Try widening tolerances or lowering min area.")

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

    # Options
    opt_cols = st.columns(4)
    show_mode = opt_cols[0].radio("Show", ["Only with flakes", "All images"], index=0)
    max_display = opt_cols[1].number_input("Max images to display", 10, 500, 50, step=10)
    cols_per_row = opt_cols[2].number_input("Columns", 1, 6, 3)
    n_workers = opt_cols[3].number_input("Workers", 1, 16, min(8, total_available), step=1)

    # Sample size
    sample_cols = st.columns(2)
    max_compute = sample_cols[0].number_input(
        "Max images to process", 1, total_available, min(total_available, 100), step=10,
        help="Randomly samples this many images from the folder.",
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

        # Worker function — runs in a thread. cv2 releases the GIL so
        # multiple threads get true parallelism on the C++ side.
        def _detect_one(img_path):
            wb_bgr_w, wb_rgb_w = load_and_preprocess(img_path, apply_wb)
            if wb_bgr_w is None:
                return None
            flakes_w = detector.detect_flakes(wb_bgr_w, [mask_values])
            det_img_w = draw_flakes_on_image(wb_rgb_w, flakes_w)
            return (img_path, flakes_w, det_img_w)

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

        # ── Summary ──────────────────────────────────────────────────────
        total_processed = len(results)
        with_flakes = [(p, f, img) for p, f, img in results if len(f) > 0]
        total_flakes = sum(len(f) for _, f, _ in results)

        st.success(
            f"Done in **{elapsed_total:.1f}s** ({total_processed/elapsed_total:.1f} img/s). "
            f"Processed **{total_processed}** images. "
            f"**{len(with_flakes)}** have flakes ({total_flakes} total flakes found)."
        )

        # Save results to session state so they persist across reruns
        st.session_state["dataset_results"] = results
        st.session_state["dataset_with_flakes"] = with_flakes
        st.session_state["dataset_total_flakes"] = total_flakes

    # ── Display results (from session state) ─────────────────────────────
    if "dataset_results" in st.session_state:
        results = st.session_state["dataset_results"]
        with_flakes = st.session_state["dataset_with_flakes"]
        total_flakes = st.session_state["dataset_total_flakes"]

        # Summary metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Images processed", len(results))
        m2.metric("Images with flakes", len(with_flakes))
        m3.metric("Total flakes", total_flakes)

        # Pick which results to show
        display_list = with_flakes if show_mode == "Only with flakes" else results
        display_list = display_list[:max_display]

        if not display_list:
            st.info("No images to display with current filter.")
        else:
            st.subheader(f"Results ({len(display_list)} images shown)")

            # Render as a grid
            for row_start in range(0, len(display_list), cols_per_row):
                row_items = display_list[row_start : row_start + cols_per_row]
                cols = st.columns(cols_per_row)
                for col_idx, (img_path, flakes_item, det_img) in enumerate(row_items):
                    with cols[col_idx]:
                        n = len(flakes_item)
                        caption = f"{img_path.name} — {n} flake{'s' if n != 1 else ''}"
                        st.image(det_img, caption=caption, width="stretch")

            # ── Aggregate flake table ────────────────────────────────────
            if with_flakes:
                with st.expander("All detected flakes (table)"):
                    all_rows = []
                    for img_path, flakes_item, _ in with_flakes:
                        for i, f in enumerate(flakes_item):
                            s = f["stats"]
                            all_rows.append({
                                "Image": img_path.name,
                                "Flake #": i,
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
