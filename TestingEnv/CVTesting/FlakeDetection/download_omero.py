"""
Download all images from the GR01 project in OMERO to Dataset/GR01/.
Preserves dataset sub-folder structure: Dataset/GR01/<dataset_name>/<image_name>.png
"""

import os
import sys
import numpy as np
import cv2

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

os.environ["OMERO_HOST"] = "100.125.247.59"
os.environ["OMERO_PORT"] = "4064"
os.environ["OMERO_USERNAME"] = "root"
os.environ["OMERO_PASSWORD"] = "omero"

from image_container import Image_Container

PROJECT_NAME = "GR01"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "Dataset", "GR01")


def sanitize(name: str) -> str:
    """Replace characters that are problematic in file paths."""
    return name.replace("/", "_").replace("\\", "_").replace(":", "_")


def main():
    print(f"Connecting to OMERO at {os.environ['OMERO_HOST']}...")
    ic = Image_Container()
    conn = ic.conn
    print("Connected.\n")

    # --- Find the GR01 project ---
    project = None
    for p in conn.getObjects("Project"):
        if p.getName() == PROJECT_NAME:
            project = p
            break

    if project is None:
        # Maybe GR01 is a dataset, not a project
        print(f"Project '{PROJECT_NAME}' not found. Searching datasets...")
        dataset = None
        for d in conn.getObjects("Dataset"):
            if d.getName() == PROJECT_NAME:
                dataset = d
                break
        if dataset is None:
            print(f"No project or dataset named '{PROJECT_NAME}' found.")
            print("\nAvailable projects:")
            for p in conn.getObjects("Project"):
                print(f"  - {p.getName()} (id={p.getId()})")
            print("\nAvailable datasets:")
            for d in conn.getObjects("Dataset"):
                print(f"  - {d.getName()} (id={d.getId()})")
            ic.disconnect_from_omero()
            return

        # Download images from the single dataset
        download_dataset_images(ic, dataset, OUTPUT_DIR)
        ic.disconnect_from_omero()
        return

    # --- Download all datasets in the project ---
    print(f"Found project '{PROJECT_NAME}' (id={project.getId()})")
    datasets = list(project.listChildren())
    print(f"  Contains {len(datasets)} dataset(s)\n")

    total_images = 0
    for dataset in datasets:
        ds_name = sanitize(dataset.getName())
        ds_dir = os.path.join(OUTPUT_DIR, ds_name)
        count = download_dataset_images(ic, dataset, ds_dir)
        total_images += count

    print(f"\nDone. Downloaded {total_images} image(s) total to {OUTPUT_DIR}")
    ic.disconnect_from_omero()


def download_dataset_images(ic, dataset, dest_dir: str) -> int:
    """Download all images from a dataset into dest_dir. Returns count."""
    os.makedirs(dest_dir, exist_ok=True)
    ds_name = dataset.getName()
    images = list(dataset.listChildren())
    print(f"  Dataset '{ds_name}' (id={dataset.getId()}) — {len(images)} image(s)")

    for i, img in enumerate(images):
        img_name = sanitize(img.getName())
        # Ensure .png extension
        if not img_name.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
            img_name += ".png"
        out_path = os.path.join(dest_dir, img_name)

        if os.path.exists(out_path):
            print(f"    [{i+1}/{len(images)}] Skipping (exists): {img_name}")
            continue

        print(f"    [{i+1}/{len(images)}] Downloading: {img_name} (id={img.getId()})...", end="", flush=True)
        try:
            arr = ic.download_image(img.getId())
            cv2.imwrite(out_path, arr)
            print(" OK")
        except Exception as e:
            print(f" ERROR: {e}")

    return len(images)


if __name__ == "__main__":
    main()
