"""
Wafer image stitcher and chip segmentation.

Given an OMERO dataset from a trace-over scan, this module:
1. Fetches all images and their metadata (x, y, sequence)
2. Builds a grid layout from physical stage coordinates
3. Classifies each tile as substrate-background or not
4. Segments individual chips via flood-fill on the background grid
5. Produces stitched overview images (full wafer or per-chip)
"""

import os
import sys
import pickle
import re
import cv2
import numpy as np
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))


class WaferStitcher:
    """Stitch microscope tile images from an OMERO dataset and segment chips."""

    def __init__(
        self,
        ic: Optional[Any] = None,
        connect_omero: bool = True,
    ):
        if connect_omero:
            if ic is None:
                from image_container import Image_Container
                self.ic = Image_Container()
            else:
                self.ic = ic
            self.conn = self.ic.conn
        else:
            self.ic = None
            self.conn = None

        self.tiles: List[Dict] = []
        self.dataset_meta: Dict = {}

        self.grid_rows = 0
        self.grid_cols = 0
        self.grid: Optional[np.ndarray] = None  # 2-D array of tile indices (-1 = empty)
        self.tile_h = 0
        self.tile_w = 0

    # ------------------------------------------------------------------
    # 1.  Load tiles from OMERO
    # ------------------------------------------------------------------

    def load_dataset(self, dataset_name: str, project_name: Optional[str] = None):
        """Fetch every image + metadata from an OMERO dataset.

        Populates ``self.tiles`` (list of dicts) and ``self.dataset_meta``.
        """
        if self.conn is None:
            raise RuntimeError(
                "No OMERO connection available. Initialize with connect_omero=True "
                "or use load_local_directory(...) for offline stitching."
            )

        dataset = self._find_dataset(dataset_name, project_name)
        if dataset is None:
            raise ValueError(
                f"Dataset '{dataset_name}' not found"
                + (f" in project '{project_name}'" if project_name else "")
            )

        self.dataset_meta = self._read_dataset_metadata(dataset)

        tiles = []
        for img_obj in dataset.listChildren():
            meta = self._read_image_metadata(img_obj)
            tiles.append(meta)

        tiles.sort(key=lambda t: t["sequence"])
        self.tiles = tiles
        print(f"Loaded {len(tiles)} tiles from dataset '{dataset_name}'")

    def load_local_directory(
        self,
        directory: str,
        grid_cols: Optional[int] = None,
        serpentine: bool = True,
        thumbnail_size: Optional[int] = None,
        recursive: bool = False,
    ):
        """Load tiles directly from a local folder saved by wafer_downloader.

        File names are expected to include a sequence index like ``image_1234``.
        Since local exports do not include OMERO x/y stage coordinates, this
        method synthesizes an initial lattice from sequence order.
        """
        root = Path(directory).expanduser()
        if not root.exists():
            raise FileNotFoundError(f"Directory not found: {root}")

        exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
        files = (
            [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts]
            if recursive
            else [p for p in root.glob("*") if p.is_file() and p.suffix.lower() in exts]
        )
        if not files:
            raise ValueError(f"No image files found in {root}")

        parsed = []
        for path in files:
            seq, ts = self._parse_sequence_timestamp_from_name(path.name)
            parsed.append((path, seq, ts))

        # Sort primarily by parsed sequence, then filename for stability.
        parsed.sort(
            key=lambda x: (
                float("inf") if x[1] is None else x[1],
                x[0].name.lower(),
            )
        )

        n = len(parsed)
        if grid_cols is None:
            grid_cols = max(1, int(round(np.sqrt(n))))
            print(
                f"grid_cols not provided; using auto-estimate {grid_cols}. "
                "Set GRID_COLS in the notebook for better placement."
            )
        if grid_cols <= 0:
            raise ValueError("grid_cols must be >= 1")

        tiles: List[Dict] = []
        loaded = 0
        for idx, (path, seq, ts) in enumerate(parsed):
            img = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if img is None:
                continue
            if thumbnail_size is not None:
                h, w = img.shape[:2]
                scale = thumbnail_size / max(h, w)
                img = cv2.resize(
                    img,
                    (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA,
                )

            row = loaded // grid_cols
            col_in_row = loaded % grid_cols
            col = grid_cols - 1 - col_in_row if (serpentine and row % 2 == 1) else col_in_row

            tiles.append(
                {
                    "image_id": None,
                    "name": path.name,
                    "local_path": str(path),
                    "x": float(col),
                    "y": float(row),
                    "sequence": int(seq) if seq is not None else loaded,
                    "magnification": None,
                    "timestamp": ts,
                    "image": img,
                }
            )
            loaded += 1
            if loaded % 200 == 0 or loaded == n:
                print(f"  Loaded {loaded}/{n} images")

        if not tiles:
            raise ValueError(f"Could not load any readable images from {root}")

        tiles.sort(key=lambda t: t["sequence"])
        self.tiles = tiles
        self.dataset_meta = {
            "id": None,
            "name": root.name,
            "source": "local_directory",
            "path": str(root),
            "key_value_pairs": {},
        }
        first = self.tiles[0]["image"]
        self.tile_h, self.tile_w = first.shape[:2]

        print(
            f"Loaded {len(self.tiles)} local tiles from '{root}' "
            f"(tile size: {self.tile_w}x{self.tile_h}, grid_cols={grid_cols}, "
            f"serpentine={serpentine})"
        )

    def download_tile_images(self, thumbnail_size: Optional[int] = None,
                             number_of_tiles: Optional[int] = None,
                             workers: int = 1):
        """Download pixel data for every tile. Optionally resize to thumbnail.

        Args:
            thumbnail_size: If set, resize images so the longest edge is this
                many pixels.  *None* keeps full resolution.
            number_of_tiles: Limit how many tiles to download (default: all).
            workers: Number of parallel OMERO connections to use.  Values > 1
                create additional ``BlitzGateway`` sessions and download
                images concurrently, which is significantly faster over a
                network link.
        """
        if self.ic is None:
            raise RuntimeError(
                "download_tile_images requires an OMERO connection. "
                "Use load_local_directory(...) for offline workflows."
            )

        if workers > 1:
            self._download_parallel(thumbnail_size, number_of_tiles, workers)
            return

        n = number_of_tiles if number_of_tiles is not None else len(self.tiles)
        for i, tile in enumerate(self.tiles[:n]):
            if "image" in tile and tile["image"] is not None:
                continue
            img = self.ic.download_image(tile["image_id"])
            if thumbnail_size is not None:
                h, w = img.shape[:2]
                scale = thumbnail_size / max(h, w)
                img = cv2.resize(
                    img,
                    (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA,
                )
            tile["image"] = img
            if (i + 1) % 50 == 0 or i == n - 1:
                print(f"  Downloaded {i + 1}/{n} images")

        first = next(t["image"] for t in self.tiles if t.get("image") is not None)
        self.tile_h, self.tile_w = first.shape[:2]

    def _download_parallel(self, thumbnail_size: Optional[int],
                           number_of_tiles: Optional[int],
                           workers: int):
        """Download tile images using multiple OMERO connections.

        Each worker gets its own ``BlitzGateway`` and processes a chunk of
        tiles sequentially.  This avoids the OMERO server-side contention
        that occurs when many concurrent pixel-store requests share
        server resources.
        """
        import logging
        import threading
        from omero.gateway import BlitzGateway

        logging.getLogger("omero").setLevel(logging.ERROR)

        host = os.environ.get("OMERO_HOST")
        port = int(os.environ.get("OMERO_PORT", "4064"))
        user = os.environ.get("OMERO_USERNAME")
        passwd = os.environ.get("OMERO_PASSWORD")

        n = number_of_tiles if number_of_tiles is not None else len(self.tiles)
        pending = [
            (i, self.tiles[i]) for i in range(min(n, len(self.tiles)))
            if self.tiles[i].get("image") is None
        ]
        if not pending:
            print("All tiles already downloaded")
            return

        total = len(pending)
        counter_lock = threading.Lock()
        done = [0]

        # Split pending list into roughly equal chunks, one per worker
        chunks: List[List[Tuple[int, Dict]]] = [[] for _ in range(workers)]
        for job_i, item in enumerate(pending):
            chunks[job_i % workers].append(item)

        def _worker(chunk: List[Tuple[int, Dict]], worker_id: int):
            conn = BlitzGateway(user, passwd, host=host, port=port,
                                secure=True)
            if not conn.connect():
                print(f"  Worker {worker_id}: failed to connect")
                return
            try:
                for idx, tile in chunk:
                    try:
                        image_id = tile["image_id"]
                        img_obj = conn.getObject("Image", image_id)
                        if img_obj is None:
                            continue
                        pixels = img_obj.getPrimaryPixels()
                        sizeC = img_obj.getSizeC()
                        sizeY = img_obj.getSizeY()
                        sizeX = img_obj.getSizeX()
                        data = np.zeros((sizeY, sizeX, sizeC), dtype=np.uint8)
                        for c in range(sizeC):
                            data[:, :, c] = pixels.getPlane(0, c, 0)
                        img = cv2.cvtColor(
                            np.ascontiguousarray(data), cv2.COLOR_RGB2BGR
                        )
                        if thumbnail_size is not None:
                            h, w = img.shape[:2]
                            scale = thumbnail_size / max(h, w)
                            img = cv2.resize(
                                img, (int(w * scale), int(h * scale)),
                                interpolation=cv2.INTER_AREA,
                            )
                        self.tiles[idx]["image"] = img
                    except Exception as e:
                        print(f"  Worker {worker_id}: error on tile {idx}: {e}")
                    with counter_lock:
                        done[0] += 1
                        if done[0] % 50 == 0 or done[0] == total:
                            print(f"  Downloaded {done[0]}/{total} images")
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        print(f"Downloading {total} images with {workers} workers...")
        threads = []
        for wid, chunk in enumerate(chunks):
            if not chunk:
                continue
            t = threading.Thread(target=_worker, args=(chunk, wid),
                                 daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        first = next(
            (t["image"] for t in self.tiles if t.get("image") is not None),
            None,
        )
        if first is not None:
            self.tile_h, self.tile_w = first.shape[:2]

    # ------------------------------------------------------------------
    # 1b. Save / load tile cache
    # ------------------------------------------------------------------

    def save_cache(self, path: str):
        """Persist tiles, metadata, and grid info to disk (pickle).

        Saves everything needed to resume without re-downloading images.
        The OMERO connection is excluded — only data is stored.
        """
        state = {
            "tiles": self.tiles,
            "dataset_meta": self.dataset_meta,
            "grid_rows": self.grid_rows,
            "grid_cols": self.grid_cols,
            "grid": self.grid,
            "tile_h": self.tile_h,
            "tile_w": self.tile_w,
        }
        if hasattr(self, "chips"):
            state["chips"] = self.chips

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)

        n_images = sum(1 for t in self.tiles if t.get("image") is not None)
        size_mb = path.stat().st_size / 1024 / 1024
        print(f"Saved cache to {path} ({size_mb:.1f} MB, "
              f"{len(self.tiles)} tiles, {n_images} with images)")

    @classmethod
    def from_cache(cls, path: str) -> "WaferStitcher":
        """Load a previously saved cache and return a new WaferStitcher.

        The OMERO connection is *not* restored — this is for offline use
        (stitching, classification, segmentation, etc.).
        """
        with open(path, "rb") as f:
            state = pickle.load(f)

        obj = cls.__new__(cls)
        obj.ic = None
        obj.conn = None
        obj.tiles = state["tiles"]
        obj.dataset_meta = state["dataset_meta"]
        obj.grid_rows = state["grid_rows"]
        obj.grid_cols = state["grid_cols"]
        obj.grid = state["grid"]
        obj.tile_h = state["tile_h"]
        obj.tile_w = state["tile_w"]
        if "chips" in state:
            obj.chips = state["chips"]

        n_images = sum(1 for t in obj.tiles if t.get("image") is not None)
        print(f"Loaded cache from {path} ({len(obj.tiles)} tiles, {n_images} with images)")
        return obj

    def rotate_tiles(self, angle: int = 180, image_keys: Optional[List[str]] = None):
        """Rotate every tile image in-place.

        Args:
            angle: 90, 180, or 270 (clockwise).
            image_keys: tile dict keys to rotate. If *None*, rotates every
                numpy image field present in each tile (e.g. ``image``,
                ``image_corrected``), ensuring all variants stay aligned.
        """
        rot_map = {
            90: cv2.ROTATE_90_CLOCKWISE,
            180: cv2.ROTATE_180,
            270: cv2.ROTATE_90_COUNTERCLOCKWISE,
        }
        if angle not in rot_map:
            raise ValueError(f"angle must be 90, 180, or 270 (got {angle})")
        code = rot_map[angle]
        per_key_counts: Dict[str, int] = {}
        for tile in self.tiles:
            if image_keys is None:
                keys = [
                    k for k, v in tile.items()
                    if isinstance(v, np.ndarray) and v.ndim >= 2
                ]
            else:
                keys = image_keys
            for key in keys:
                img = tile.get(key)
                if isinstance(img, np.ndarray) and img.ndim >= 2:
                    tile[key] = cv2.rotate(img, code)
                    per_key_counts[key] = per_key_counts.get(key, 0) + 1

        first = next((t.get("image") for t in self.tiles if t.get("image") is not None), None)
        if first is not None:
            self.tile_h, self.tile_w = first.shape[:2]
        count_msg = ", ".join(f"{k}: {v}" for k, v in sorted(per_key_counts.items()))
        print(
            f"Rotated tiles by {angle}° "
            f"({count_msg}; tile size now {self.tile_h}x{self.tile_w})"
        )

    def invert_x(self, image_keys: Optional[List[str]] = None):
        """Invert tile images along X direction (left-right mirror)."""
        per_key_counts: Dict[str, int] = {}
        for tile in self.tiles:
            if image_keys is None:
                keys = [
                    k for k, v in tile.items()
                    if isinstance(v, np.ndarray) and v.ndim >= 2
                ]
            else:
                keys = image_keys
            for key in keys:
                img = tile.get(key)
                if isinstance(img, np.ndarray) and img.ndim >= 2:
                    tile[key] = cv2.flip(img, 1)
                    per_key_counts[key] = per_key_counts.get(key, 0) + 1

        first = next((t.get("image") for t in self.tiles if t.get("image") is not None), None)
        if first is not None:
            self.tile_h, self.tile_w = first.shape[:2]
        count_msg = ", ".join(f"{k}: {v}" for k, v in sorted(per_key_counts.items()))
        print(
            f"Inverted X (left-right) "
            f"({count_msg}; tile size now {self.tile_h}x{self.tile_w})"
        )

    def invert_y(self, image_keys: Optional[List[str]] = None):
        """Invert tile images along Y direction (up-down mirror)."""
        per_key_counts: Dict[str, int] = {}
        for tile in self.tiles:
            if image_keys is None:
                keys = [
                    k for k, v in tile.items()
                    if isinstance(v, np.ndarray) and v.ndim >= 2
                ]
            else:
                keys = image_keys
            for key in keys:
                img = tile.get(key)
                if isinstance(img, np.ndarray) and img.ndim >= 2:
                    tile[key] = cv2.flip(img, 0)
                    per_key_counts[key] = per_key_counts.get(key, 0) + 1

        first = next((t.get("image") for t in self.tiles if t.get("image") is not None), None)
        if first is not None:
            self.tile_h, self.tile_w = first.shape[:2]
        count_msg = ", ".join(f"{k}: {v}" for k, v in sorted(per_key_counts.items()))
        print(
            f"Inverted Y (up-down) "
            f"({count_msg}; tile size now {self.tile_h}x{self.tile_w})"
        )

    # ------------------------------------------------------------------
    # 2.  Build the grid layout
    # ------------------------------------------------------------------

    def build_grid(self):
        """Map physical (x, y) coordinates to a row/col grid.

        Uses the stage coordinates stored per-tile. Tiles are snapped to
        the nearest grid position derived from the unique sorted x/y values.
        """
        xs = np.array([t["x"] for t in self.tiles])
        ys = np.array([t["y"] for t in self.tiles])

        unique_x = np.sort(np.unique(np.round(xs, 3)))
        unique_y = np.sort(np.unique(np.round(ys, 3)))

        self.grid_cols = len(unique_x)
        self.grid_rows = len(unique_y)

        x_to_col = {v: i for i, v in enumerate(unique_x)}
        y_to_row = {v: i for i, v in enumerate(unique_y)}

        self.grid = np.full((self.grid_rows, self.grid_cols), -1, dtype=int)

        for idx, tile in enumerate(self.tiles):
            col = x_to_col[np.round(tile["x"], 3)]
            row = y_to_row[np.round(tile["y"], 3)]
            tile["row"] = row
            tile["col"] = col
            self.grid[row, col] = idx

        print(f"Grid: {self.grid_rows} rows x {self.grid_cols} cols "
              f"({np.count_nonzero(self.grid >= 0)} populated)")

    # ------------------------------------------------------------------
    # 3.  Background classification
    # ------------------------------------------------------------------

    @staticmethod
    def is_substrate_background(
        image: np.ndarray,
        hue_range: Tuple[int, int] = (110, 170),
        min_saturation: int = 30,
        min_purple_fraction: float = 0.4,
        sample_fraction: float = 0.5,
    ) -> Tuple[bool, dict]:
        """Return (is_background, stats) — True when purple SiO₂ substrate."""
        h, w = image.shape[:2]
        my = int(h * (1 - sample_fraction) / 2)
        mx = int(w * (1 - sample_fraction) / 2)
        roi = image[my : h - my, mx : w - mx]

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hue = hsv[:, :, 0].ravel().astype(np.float32)
        sat = hsv[:, :, 1].ravel().astype(np.float32)

        purple_mask = (sat >= min_saturation) & (hue >= hue_range[0]) & (hue <= hue_range[1])
        purple_frac = purple_mask.sum() / max(len(hue), 1)

        stats = {
            "median_hue": float(np.median(hue)),
            "median_saturation": float(np.median(sat)),
            "purple_fraction": round(float(purple_frac), 4),
            "passed": purple_frac >= min_purple_fraction,
        }
        return stats["passed"], stats

    def classify_backgrounds(self):
        """Label every tile with ``is_substrate_background``."""
        for tile in self.tiles:
            if tile.get("image") is None:
                tile["is_substrate_background"] = None
                continue
            passed, stats = self.is_substrate_background(tile["image"])
            tile["is_substrate_background"] = passed
            tile["bg_stats"] = stats

        n_bg = sum(1 for t in self.tiles if t.get("is_substrate_background"))
        print(f"Background classification: {n_bg}/{len(self.tiles)} tiles are substrate")

    # ------------------------------------------------------------------
    # 4.  Chip segmentation via flood-fill
    # ------------------------------------------------------------------

    def segment_chips(self) -> Dict[int, List[int]]:
        """Flood-fill connected regions of *substrate* tiles → chip map.

        Non-substrate tiles act as boundaries between chips.  Each
        connected component of substrate tiles is assigned a unique chip id.

        Returns:
            dict mapping chip_id → list of tile indices
        """
        if self.grid is None:
            raise RuntimeError("Call build_grid() first")

        visited = np.zeros((self.grid_rows, self.grid_cols), dtype=bool)
        chips: Dict[int, List[int]] = {}
        chip_id = 0

        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                tile_idx = self.grid[r, c]
                if tile_idx < 0 or visited[r, c]:
                    continue
                tile = self.tiles[tile_idx]
                if not tile.get("is_substrate_background"):
                    visited[r, c] = True
                    continue

                component = self._flood_fill(r, c, visited)
                if component:
                    chips[chip_id] = component
                    for idx in component:
                        self.tiles[idx]["chip_id"] = chip_id
                    chip_id += 1

        # Tiles that are non-substrate get chip_id = -1
        for tile in self.tiles:
            tile.setdefault("chip_id", -1)

        print(f"Segmented {len(chips)} chip(s): "
              + ", ".join(f"chip {k}: {len(v)} tiles" for k, v in chips.items()))
        self.chips = chips
        return chips

    def _flood_fill(self, start_r: int, start_c: int, visited: np.ndarray) -> List[int]:
        """BFS flood-fill returning tile indices for one connected component."""
        queue = deque([(start_r, start_c)])
        visited[start_r, start_c] = True
        component: List[int] = []

        while queue:
            r, c = queue.popleft()
            tile_idx = self.grid[r, c]
            if tile_idx < 0:
                continue
            component.append(tile_idx)

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.grid_rows and 0 <= nc < self.grid_cols and not visited[nr, nc]:
                    nidx = self.grid[nr, nc]
                    if nidx >= 0 and self.tiles[nidx].get("is_substrate_background"):
                        visited[nr, nc] = True
                        queue.append((nr, nc))

        return component

    # ------------------------------------------------------------------
    # 4b. Tile placement solving
    # ------------------------------------------------------------------

    def solve_tile_positions(self, min_confidence: float = 0.3,
                             max_pairs_per_edge: int = 50) -> Dict:
        """Estimate per-tile pixel positions from pairwise image matching.

        Instead of assuming a rigid lattice, this measures the actual (dx, dy)
        offset between every pair of adjacent tiles (horizontal and vertical)
        via template matching, then solves for globally consistent positions
        using least-squares.

        Results are stored as ``tile["px_x"]`` and ``tile["px_y"]`` on each
        tile dict, and also in ``self.tile_positions``.

        Returns:
            dict with diagnostics: matched/rejected edge counts, residual.
        """
        if self.grid is None:
            raise RuntimeError("Call build_grid() first")

        tile_by_rc: Dict[Tuple[int, int], int] = {}
        for idx, t in enumerate(self.tiles):
            if t.get("image") is not None and "row" in t:
                tile_by_rc[(t["row"], t["col"])] = idx

        edges: List[Tuple[int, int, float, float, float]] = []
        tested = 0
        for (r, c), idx_a in tile_by_rc.items():
            for dr, dc in [(0, 1), (1, 0)]:
                nr, nc = r + dr, c + dc
                idx_b = tile_by_rc.get((nr, nc))
                if idx_b is None:
                    continue
                tested += 1
                direction = "horizontal" if dc == 1 else "vertical"
                dx, dy, conf = self._match_tile_offset(
                    self.tiles[idx_a]["image"],
                    self.tiles[idx_b]["image"],
                    direction,
                )
                if conf >= min_confidence:
                    edges.append((idx_a, idx_b, dx, dy, conf))
                if len(edges) >= max_pairs_per_edge * 2:
                    break

        n_matched = len(edges)
        n_rejected = tested - n_matched
        print(f"Placement solver: {n_matched} matched edges, "
              f"{n_rejected} rejected (conf < {min_confidence}), "
              f"{tested} tested")

        if n_matched == 0:
            print("  WARNING: no edges matched — falling back to lattice")
            self.tile_positions = None
            return {"matched": 0, "rejected": tested, "residual": float("inf")}

        # Least-squares solve: minimise sum |pos_b - pos_a - (dx, dy)|^2
        # with anchor: tile 0 at (0, 0)
        all_indices = sorted(set(
            idx for e in edges for idx in (e[0], e[1])
        ))
        idx_to_var = {idx: i for i, idx in enumerate(all_indices)}
        n_vars = len(all_indices)

        A_rows_x = []
        A_rows_y = []
        b_x = []
        b_y = []

        for idx_a, idx_b, dx, dy, conf in edges:
            w = conf
            row_x = np.zeros(n_vars, dtype=np.float64)
            row_y = np.zeros(n_vars, dtype=np.float64)
            va, vb = idx_to_var[idx_a], idx_to_var[idx_b]
            row_x[vb] = w
            row_x[va] = -w
            row_y[vb] = w
            row_y[va] = -w
            A_rows_x.append(row_x)
            A_rows_y.append(row_y)
            b_x.append(dx * w)
            b_y.append(dy * w)

        # Anchor the first tile
        anchor = np.zeros(n_vars, dtype=np.float64)
        anchor_idx = all_indices[0]
        anchor[idx_to_var[anchor_idx]] = 1000.0
        A_rows_x.append(anchor)
        A_rows_y.append(anchor)
        b_x.append(0.0)
        b_y.append(0.0)

        A_x = np.array(A_rows_x)
        A_y = np.array(A_rows_y)
        b_x_arr = np.array(b_x)
        b_y_arr = np.array(b_y)

        pos_x, res_x, _, _ = np.linalg.lstsq(A_x, b_x_arr, rcond=None)
        pos_y, res_y, _, _ = np.linalg.lstsq(A_y, b_y_arr, rcond=None)

        residual = 0.0
        if len(res_x) > 0 and len(res_y) > 0:
            residual = float(np.sqrt(res_x[0] + res_y[0]) / max(n_matched, 1))

        # Shift so minimum is 0
        pos_x -= pos_x.min()
        pos_y -= pos_y.min()

        positions: Dict[int, Tuple[float, float]] = {}
        for idx, var_i in idx_to_var.items():
            positions[idx] = (float(pos_x[var_i]), float(pos_y[var_i]))
            self.tiles[idx]["px_x"] = float(pos_x[var_i])
            self.tiles[idx]["px_y"] = float(pos_y[var_i])

        self.tile_positions = positions

        print(f"  Solved {n_vars} tile positions "
              f"(residual={residual:.2f}px per edge)")
        return {
            "matched": n_matched,
            "rejected": n_rejected,
            "residual": residual,
            "n_tiles_solved": n_vars,
        }

    def _match_tile_offset(
        self, img1: np.ndarray, img2: np.ndarray, direction: str
    ) -> Tuple[float, float, float]:
        """Measure the (dx, dy) pixel offset from img1 to img2.

        Uses template matching (same proven approach as ``_match_tile_overlap``
        but with a smaller template that allows detection of both axes).

        Returns ``(dx, dy, confidence)`` where ``(dx, dy)`` is the canvas
        translation from img1's origin to img2's origin.
        """
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        h, w = gray1.shape

        # Use a center crop from the overlap edge of img1 as template.
        # Smaller than full height/width so matchTemplate has room to
        # find the best (x, y) position in both axes.
        margin = max(h // 6, 4)  # vertical margin for cross-axis search

        if direction == "horizontal":
            strip = max(int(w * 0.2), 8)
            # Template: center-right patch of img1
            template = gray1[margin:h - margin, w - strip:]
            # Search region: left portion of img2, with vertical slack
            search_w = min(int(w * 0.65), w)
            search = gray2[:, :search_w]
        else:
            strip = max(int(h * 0.2), 8)
            # Template: center-bottom patch of img1
            template = gray1[h - strip:, margin:w - margin]
            # Search region: top portion of img2, with horizontal slack
            search_h = min(int(h * 0.65), h)
            search = gray2[:search_h, :]

        if (search.shape[0] < template.shape[0]
                or search.shape[1] < template.shape[1]):
            return 0.0, 0.0, 0.0

        result = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        mx, my = max_loc  # (x, y) in search image where template top-left sits

        if direction == "horizontal":
            # Template top-left in img1 coords: (w - strip, margin)
            # Matched at (mx, my) in img2 coords
            # Canvas: img1(w-strip, margin) = img2(mx, my)
            # So: img1.x + w - strip = img2.x + mx  →  dx = w - strip - mx
            #     img1.y + margin     = img2.y + my  →  dy = margin - my
            dx = float(w - strip - mx)
            dy = float(margin - my)
        else:
            # Template top-left in img1 coords: (margin, h - strip)
            # Matched at (mx, my) in img2 coords
            # img1.x + margin  = img2.x + mx  →  dx = margin - mx
            # img1.y + h-strip = img2.y + my  →  dy = h - strip - my
            dx = float(margin - mx)
            dy = float(h - strip - my)

        return dx, dy, float(max_val)

    # ------------------------------------------------------------------
    # 5.  Stitching
    # ------------------------------------------------------------------

    def _get_tile_image(self, tile: Dict, image_key: str = "image",
                        fallback_to_raw: bool = True) -> Optional[np.ndarray]:
        """Return the tile image for the given key, falling back to 'image'."""
        img = tile.get(image_key)
        if img is None and fallback_to_raw and image_key != "image":
            img = tile.get("image")
        return img

    def _tile_canvas_xy(self, tile: Dict, scale: float,
                        placement_mode: str,
                        lattice_step_x: int = 0,
                        lattice_step_y: int = 0,
                        origin_x: float = 0.0,
                        origin_y: float = 0.0) -> Tuple[int, int]:
        """Return (x0, y0) canvas position for a tile."""
        if placement_mode == "solved" and "px_x" in tile and "px_y" in tile:
            x0 = int(round(tile["px_x"] * scale + origin_x))
            y0 = int(round(tile["px_y"] * scale + origin_y))
        else:
            r, c = tile["row"], tile["col"]
            th = max(int(self.tile_h * scale), 1)
            tw = max(int(self.tile_w * scale), 1)
            sx = lattice_step_x if lattice_step_x else tw
            sy = lattice_step_y if lattice_step_y else th
            x0 = int(round(c * sx + origin_x))
            y0 = int(round(r * sy + origin_y))
        return x0, y0

    def _solved_canvas_size(self, scale: float) -> Tuple[int, int]:
        """Compute canvas size from solved positions."""
        th = max(int(self.tile_h * scale), 1)
        tw = max(int(self.tile_w * scale), 1)
        max_x = max_y = 0
        for t in self.tiles:
            if "px_x" in t and t.get("image") is not None:
                x = int(round(t["px_x"] * scale)) + tw
                y = int(round(t["px_y"] * scale)) + th
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        return max_x, max_y

    def stitch_full(self, scale: float = 1.0,
                    image_key: str = "image",
                    fallback_to_raw: bool = True,
                    placement_mode: str = "lattice") -> np.ndarray:
        """Stitch every tile into one large image.

        Args:
            scale: down-scale factor (0–1] applied to each tile before placing.
            image_key: which tile field to read pixels from.
            placement_mode: ``"lattice"`` (regular grid) or ``"solved"``
                (use per-tile positions from ``solve_tile_positions``).
        """
        th = max(int(self.tile_h * scale), 1)
        tw = max(int(self.tile_w * scale), 1)

        if placement_mode == "solved" and getattr(self, "tile_positions", None):
            canvas_w, canvas_h = self._solved_canvas_size(scale)
        else:
            canvas_h = self.grid_rows * th
            canvas_w = self.grid_cols * tw

        canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

        for tile in self.tiles:
            img = self._get_tile_image(tile, image_key, fallback_to_raw=fallback_to_raw)
            if img is None:
                continue
            patch = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA) if scale != 1.0 else img
            x0, y0 = self._tile_canvas_xy(tile, scale, placement_mode)
            y1 = min(y0 + th, canvas_h)
            x1 = min(x0 + tw, canvas_w)
            if y1 <= y0 or x1 <= x0:
                continue
            canvas[y0:y1, x0:x1] = patch[:y1 - y0, :x1 - x0]

        return canvas

    def stitch_chip(self, chip_id: int, scale: float = 1.0,
                    image_key: str = "image",
                    fallback_to_raw: bool = True,
                    placement_mode: str = "lattice") -> np.ndarray:
        """Stitch tiles belonging to a single chip.

        The output is cropped to the bounding box of the chip.
        """
        if chip_id not in self.chips:
            raise ValueError(f"Unknown chip_id {chip_id}")

        th = max(int(self.tile_h * scale), 1)
        tw = max(int(self.tile_w * scale), 1)
        indices = self.chips[chip_id]

        if placement_mode == "solved" and getattr(self, "tile_positions", None):
            xs = [int(round(self.tiles[i]["px_x"] * scale)) for i in indices
                  if "px_x" in self.tiles[i]]
            ys = [int(round(self.tiles[i]["px_y"] * scale)) for i in indices
                  if "px_y" in self.tiles[i]]
            if not xs:
                placement_mode = "lattice"
            else:
                min_x, min_y = min(xs), min(ys)
                max_x, max_y = max(xs) + tw, max(ys) + th
                w, h = max_x - min_x, max_y - min_y
                canvas = np.zeros((h, w, 3), dtype=np.uint8)
                for idx in indices:
                    tile = self.tiles[idx]
                    img = self._get_tile_image(tile, image_key, fallback_to_raw=fallback_to_raw)
                    if img is None or "px_x" not in tile:
                        continue
                    patch = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA) if scale != 1.0 else img
                    x0 = int(round(tile["px_x"] * scale)) - min_x
                    y0 = int(round(tile["px_y"] * scale)) - min_y
                    y1 = min(y0 + th, h)
                    x1 = min(x0 + tw, w)
                    if y1 <= y0 or x1 <= x0:
                        continue
                    canvas[y0:y1, x0:x1] = patch[:y1 - y0, :x1 - x0]
                return canvas

        # Lattice fallback
        rows = [self.tiles[i]["row"] for i in indices]
        cols = [self.tiles[i]["col"] for i in indices]
        min_r, max_r = min(rows), max(rows)
        min_c, max_c = min(cols), max(cols)

        h = (max_r - min_r + 1) * th
        w = (max_c - min_c + 1) * tw
        canvas = np.zeros((h, w, 3), dtype=np.uint8)

        for idx in indices:
            tile = self.tiles[idx]
            img = self._get_tile_image(tile, image_key, fallback_to_raw=fallback_to_raw)
            if img is None:
                continue
            r = tile["row"] - min_r
            c = tile["col"] - min_c
            patch = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA) if scale != 1.0 else img
            y0, x0 = r * th, c * tw
            canvas[y0 : y0 + th, x0 : x0 + tw] = patch

        return canvas

    def stitch_blended(
        self,
        overlap_x: Optional[int] = None,
        overlap_y: Optional[int] = None,
        feather: int = 15,
        scale: float = 1.0,
        blend_mode: str = "center",
        image_key: str = "image",
        fallback_to_raw: bool = True,
        placement_mode: str = "lattice",
        odd_row_x_shift: int = 0,
        odd_col_y_shift: int = 0,
    ) -> np.ndarray:
        """Stitch tiles with overlap alignment and blending.

        Args:
            overlap_x: Horizontal overlap in pixels (auto-detected if *None*).
                Ignored when *placement_mode* is ``"solved"``.
            overlap_y: Vertical overlap in pixels (auto-detected if *None*).
                Ignored when *placement_mode* is ``"solved"``.
            feather: Width of the weight ramp at each tile edge.
            scale: Output downscale factor in (0, 1].
            blend_mode: ``"center"`` or ``"linear"``.
            image_key: tile field to read pixels from.
            placement_mode: ``"lattice"`` (regular grid + overlap) or
                ``"solved"`` (per-tile positions from ``solve_tile_positions``).
            odd_row_x_shift: extra X shift for odd rows (lattice mode only).
            odd_col_y_shift: extra Y shift for odd columns (lattice mode only).

        Returns:
            Stitched BGR image (uint8).
        """
        if self.grid is None:
            raise RuntimeError("Call build_grid() first")

        use_solved = (
            placement_mode == "solved"
            and getattr(self, "tile_positions", None) is not None
        )

        th, tw = self.tile_h, self.tile_w
        if scale != 1.0:
            th = max(1, int(self.tile_h * scale))
            tw = max(1, int(self.tile_w * scale))

        feat = min(feather, tw // 4, th // 4)
        weight_mask = self._make_feather_mask(th, tw, feat)

        # Always compute lattice variables (needed as fallback for tiles
        # missing solved positions even when use_solved is True).
        if overlap_x is None:
            overlap_x = self._estimate_overlap("horizontal")
        if overlap_y is None:
            overlap_y = self._estimate_overlap("vertical")

        step_x = self.tile_w - overlap_x
        step_y = self.tile_h - overlap_y
        if scale != 1.0:
            step_x = max(1, int(step_x * scale))
            step_y = max(1, int(step_y * scale))

        origin_x = -min(0, odd_row_x_shift)
        origin_y = -min(0, odd_col_y_shift)

        if use_solved:
            canvas_w, canvas_h = self._solved_canvas_size(scale)
        else:
            canvas_h = ((self.grid_rows - 1) * step_y + th
                        + max(0, odd_row_x_shift) - min(0, odd_row_x_shift)
                        + max(0, odd_col_y_shift) - min(0, odd_col_y_shift))
            canvas_w = ((self.grid_cols - 1) * step_x + tw
                        + max(0, odd_row_x_shift) - min(0, odd_row_x_shift))

        if blend_mode == "center":
            canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
            best_weight = np.zeros((canvas_h, canvas_w), dtype=np.float32)
        else:
            canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
            weight_acc = np.zeros((canvas_h, canvas_w), dtype=np.float32)

        n = len(self.tiles)
        missing_key = 0
        placed = 0
        for i, tile in enumerate(self.tiles):
            if image_key != "image" and tile.get(image_key) is None:
                missing_key += 1
            img = self._get_tile_image(tile, image_key, fallback_to_raw=fallback_to_raw)
            if img is None or "row" not in tile:
                continue

            if scale != 1.0:
                img = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)

            if use_solved and "px_x" in tile:
                x0 = int(round(tile["px_x"] * scale))
                y0 = int(round(tile["px_y"] * scale))
            else:
                r, c = tile["row"], tile["col"]
                row_x_shift = odd_row_x_shift if (r % 2 == 1) else 0
                col_y_shift = odd_col_y_shift if (c % 2 == 1) else 0
                y0 = origin_y + r * step_y + col_y_shift
                x0 = origin_x + c * step_x + row_x_shift

            if x0 < 0 or y0 < 0:
                continue
            y1 = min(y0 + th, canvas_h)
            x1 = min(x0 + tw, canvas_w)
            if y1 <= y0 or x1 <= x0:
                continue

            placed += 1
            ph, pw = y1 - y0, x1 - x0
            wm = weight_mask[:ph, :pw]

            if blend_mode == "center":
                update = wm > best_weight[y0:y1, x0:x1]
                canvas[y0:y1, x0:x1][update] = img[:ph, :pw][update]
                best_weight[y0:y1, x0:x1] = np.maximum(
                    best_weight[y0:y1, x0:x1], wm
                )
            else:
                canvas[y0:y1, x0:x1] += (
                    img[:ph, :pw].astype(np.float32) * wm[:, :, np.newaxis]
                )
                weight_acc[y0:y1, x0:x1] += wm

            if (i + 1) % 100 == 0 or i == n - 1:
                print(f"  Iteration {i + 1}/{n} (placed {placed})")

        if blend_mode != "center":
            mask = weight_acc > 0
            for ch in range(3):
                canvas[:, :, ch][mask] /= weight_acc[mask]
            canvas = canvas.astype(np.uint8)

        mode_str = "solved" if use_solved else "lattice"
        print(f"Stitched: {canvas_w}x{canvas_h}px (placement={mode_str}, "
              f"placed {placed}/{n} tiles)")
        if image_key != "image":
            print(f"  Image key '{image_key}': missing {missing_key}/{n} tiles "
                  f"(fallback_to_raw={fallback_to_raw})")
        return canvas

    # ------------------------------------------------------------------
    # 6.  Visualisation helpers
    # ------------------------------------------------------------------

    def make_background_map(self) -> np.ndarray:
        """Return an RGB image showing the background classification grid.

        Green = substrate, red = non-substrate, black = empty.
        """
        cell = 20
        img = np.zeros((self.grid_rows * cell, self.grid_cols * cell, 3), dtype=np.uint8)
        for tile in self.tiles:
            r, c = tile["row"], tile["col"]
            color = (0, 180, 0) if tile.get("is_substrate_background") else (0, 0, 200)
            y0, x0 = r * cell, c * cell
            cv2.rectangle(img, (x0 + 1, y0 + 1), (x0 + cell - 1, y0 + cell - 1), color, -1)
        return img

    def make_chip_map(self) -> np.ndarray:
        """Return an RGB image color-coding each chip differently."""
        cell = 20
        img = np.zeros((self.grid_rows * cell, self.grid_cols * cell, 3), dtype=np.uint8)

        n_chips = len(self.chips) if hasattr(self, "chips") else 0
        palette = self._make_palette(max(n_chips, 1))

        for tile in self.tiles:
            r, c = tile["row"], tile["col"]
            cid = tile.get("chip_id", -1)
            if cid < 0:
                color = (60, 60, 60)
            else:
                color = palette[cid % len(palette)]
            y0, x0 = r * cell, c * cell
            cv2.rectangle(img, (x0 + 1, y0 + 1), (x0 + cell - 1, y0 + cell - 1), color, -1)

        return img

    def make_overview_with_chip_borders(self, scale: float = 0.1,
                                        image_key: str = "image",
                                        fallback_to_raw: bool = True,
                                        placement_mode: str = "lattice") -> np.ndarray:
        """Stitch the full wafer and overlay chip borders in color."""
        canvas = self.stitch_full(
            scale=scale, image_key=image_key, fallback_to_raw=fallback_to_raw,
            placement_mode=placement_mode,
        )
        th = max(int(self.tile_h * scale), 1)
        tw = max(int(self.tile_w * scale), 1)

        if not hasattr(self, "chips"):
            return canvas

        palette = self._make_palette(max(len(self.chips), 1))

        for chip_id, indices in self.chips.items():
            color = palette[chip_id % len(palette)]
            rows = [self.tiles[i]["row"] for i in indices]
            cols = [self.tiles[i]["col"] for i in indices]
            y0, y1 = min(rows) * th, (max(rows) + 1) * th
            x0, x1 = min(cols) * tw, (max(cols) + 1) * tw
            cv2.rectangle(canvas, (x0, y0), (x1, y1), color, 2)
            cv2.putText(
                canvas, f"Chip {chip_id}", (x0 + 4, y0 + 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2,
            )
            cv2.putText(
                canvas, f"Chip {chip_id}", (x0 + 4, y0 + 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1,
            )

        return canvas

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_dataset(self, dataset_name: str, project_name: Optional[str] = None):
        """Locate an OMERO dataset by name, optionally within a project."""
        if project_name:
            for proj in self.conn.getObjects("Project"):
                if proj.getName() == project_name:
                    for ds in proj.listChildren():
                        if ds.getName() == dataset_name:
                            return ds
        for ds in self.conn.getObjects("Dataset"):
            if ds.getName() == dataset_name:
                return ds
        return None

    def _read_dataset_metadata(self, dataset) -> dict:
        import omero.gateway
        meta: dict = {
            "id": dataset.getId(),
            "name": dataset.getName(),
            "key_value_pairs": {},
        }
        for ann in dataset.listAnnotations():
            if isinstance(ann, omero.gateway.MapAnnotationWrapper):
                for k, v in ann.getValue():
                    meta["key_value_pairs"][k] = v
        return meta

    def _read_image_metadata(self, img_obj) -> dict:
        import omero.gateway
        kv: dict = {}
        for ann in img_obj.listAnnotations():
            if isinstance(ann, omero.gateway.MapAnnotationWrapper):
                for k, v in ann.getValue():
                    kv[k] = v

        return {
            "image_id": img_obj.getId(),
            "name": img_obj.getName(),
            "x": float(kv.get("x", 0)),
            "y": float(kv.get("y", 0)),
            "sequence": int(kv.get("sequence", 0)),
            "magnification": kv.get("magnification"),
            "timestamp": kv.get("timestamp"),
            "image": None,
        }

    @staticmethod
    def _parse_sequence_timestamp_from_name(name: str) -> Tuple[Optional[int], Optional[str]]:
        """Best-effort parser for names like image_1234_2026-03-02_12-34-56.png."""
        stem = Path(name).stem
        m = re.search(r"(?:^|_)image_(\d+)(?:_(\d{4}-\d{2}-\d{2}_[0-9-]+))?$", stem, re.IGNORECASE)
        if m:
            seq = int(m.group(1))
            ts = m.group(2) if m.group(2) else None
            return seq, ts

        m2 = re.search(r"(\d+)", stem)
        if m2:
            return int(m2.group(1)), None
        return None, None

    def _estimate_overlap(self, direction: str = "horizontal", max_pairs: int = 20) -> int:
        """Estimate pixel overlap between adjacent tiles via template matching.

        Returns estimated overlap in pixels (0 if none detected).
        """
        tile_by_rc: Dict[Tuple[int, int], Dict] = {}
        for t in self.tiles:
            if t.get("image") is not None and "row" in t:
                tile_by_rc[(t["row"], t["col"])] = t

        overlaps: List[float] = []
        for (r, c), tile in tile_by_rc.items():
            nr, nc = (r, c + 1) if direction == "horizontal" else (r + 1, c)
            neighbor = tile_by_rc.get((nr, nc))
            if neighbor is None:
                continue

            ov, conf = self._match_tile_overlap(
                tile["image"], neighbor["image"], direction
            )
            if ov is not None and conf > 0.3:
                overlaps.append(ov)

            if len(overlaps) >= max_pairs:
                break

        if not overlaps:
            return 0

        result = int(round(float(np.median(overlaps))))
        dim = self.tile_w if direction == "horizontal" else self.tile_h
        print(f"  {direction} overlap: {result}px / {dim}px ({result / dim:.1%})")
        return result

    def _match_tile_overlap(
        self, img1: np.ndarray, img2: np.ndarray, direction: str = "horizontal"
    ) -> Tuple[Optional[int], float]:
        """Measure overlap between two adjacent tiles via template matching.

        For *horizontal*: img1 is left, img2 is right.
        For *vertical*: img1 is top, img2 is bottom.

        Returns ``(overlap_pixels, confidence)`` or ``(None, 0)``.
        """
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        if direction == "horizontal":
            h, w = gray1.shape
            strip = max(int(w * 0.25), 8)
            template = gray1[:, w - strip:]
            search = gray2[:, : min(int(w * 0.7), w)]
        else:
            h, w = gray1.shape
            strip = max(int(h * 0.25), 8)
            template = gray1[h - strip:, :]
            search = gray2[: min(int(h * 0.7), h), :]

        if search.shape[0] < template.shape[0] or search.shape[1] < template.shape[1]:
            return None, 0.0

        result = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if direction == "horizontal":
            overlap = max_loc[0] + strip
            dim = self.tile_w
        else:
            overlap = max_loc[1] + strip
            dim = self.tile_h

        if overlap <= 0 or overlap >= dim:
            return None, float(max_val)

        return overlap, float(max_val)

    @staticmethod
    def _make_feather_mask(h: int, w: int, feather: int) -> np.ndarray:
        """2-D linear feather mask: ramps from edge inward over *feather* pixels."""
        if feather <= 0:
            return np.ones((h, w), dtype=np.float32)
        dist_y = np.minimum(
            np.arange(1, h + 1), np.arange(h, 0, -1)
        ).astype(np.float32)
        dist_x = np.minimum(
            np.arange(1, w + 1), np.arange(w, 0, -1)
        ).astype(np.float32)
        ramp_y = np.clip(dist_y / (feather + 1), 0.0, 1.0)
        ramp_x = np.clip(dist_x / (feather + 1), 0.0, 1.0)
        return ramp_y[:, np.newaxis] * ramp_x[np.newaxis, :]


    @staticmethod
    def _make_palette(n: int) -> List[Tuple[int, int, int]]:
        """Generate *n* visually distinct BGR colours."""
        colors = []
        for i in range(n):
            hue = int(180 * i / n)
            hsv = np.uint8([[[hue, 220, 220]]])
            bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
            colors.append(tuple(int(c) for c in bgr))
        return colors

    # ------------------------------------------------------------------
    # Convenience: run the full pipeline
    # ------------------------------------------------------------------

    def run(
        self,
        dataset_name: str,
        project_name: Optional[str] = None,
        thumbnail_size: Optional[int] = None,
        stitch_scale: float = 1.0,
    ) -> dict:
        """Execute the full pipeline and return results dict.

        Returns dict with keys:
            tiles, dataset_meta, chips, stitched_full,
            background_map, chip_map, overview
        """
        self.load_dataset(dataset_name, project_name)
        self.download_tile_images(thumbnail_size=thumbnail_size)
        self.build_grid()
        self.classify_backgrounds()
        chips = self.segment_chips()

        results = {
            "tiles": self.tiles,
            "dataset_meta": self.dataset_meta,
            "chips": chips,
            "stitched_full": self.stitch_full(scale=stitch_scale),
            "background_map": self.make_background_map(),
            "chip_map": self.make_chip_map(),
            "overview": self.make_overview_with_chip_borders(scale=stitch_scale),
        }
        return results
