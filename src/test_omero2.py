from dotenv import load_dotenv
import logging
import cv2
import numpy as np
import matplotlib.pyplot as plt
from image_container import Image_Container

load_dotenv("defualt.env")
load_dotenv(".env", override=True)

image_container = Image_Container(None)

def show_image_cv2(image):
    print(f"In show_image_cv2 - Type: {type(image)}, Shape: {image.shape if hasattr(image, 'shape') else 'N/A'}")
    print(f"Is numpy array: {isinstance(image, np.ndarray)}")
    if isinstance(image, np.ndarray):
        print(f"Flags: C_CONTIGUOUS={image.flags['C_CONTIGUOUS']}, F_CONTIGUOUS={image.flags['F_CONTIGUOUS']}")
        print(f"Numpy version: {np.__version__}")
        print(f"CV2 version: {cv2.__version__}")
        # Create a fresh copy to ensure compatibility
        image = np.array(image, dtype=np.uint8, copy=True)
        print(f"After copy - Type: {type(image)}, C_CONTIGUOUS={image.flags['C_CONTIGUOUS']}")
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert to RGB for proper colors
    plt.imshow(img_rgb)
    plt.axis('off')  # Hide axes
    plt.show()

def print_telemetry(image):
    print("Type:", type(image_downloaded))
    print("Is numpy array:", isinstance(image_downloaded, np.ndarray))
    print("Dtype:", image_downloaded.dtype)
    print("Shape:", image_downloaded.shape)
    print("Flags:", image_downloaded.flags)
    print("Is C-contiguous:", image_downloaded.flags['C_CONTIGUOUS'])
    print("Is F-contiguous:", image_downloaded.flags['F_CONTIGUOUS'])

image = cv2.imread("image.png")
# show_image_cv2(image)

# project = image_container.create_project("test-project")
# dataset = image_container.create_dataset("test-dataset", project_id=project)
dataset = 63

image_id = image_container.upload_image(image, dataset_id=dataset)
image_downloaded = image_container.download_image(image_id)

print("Debug info:")
print("Type:", type(image_downloaded))
print("Value:", image_downloaded)
if isinstance(image_downloaded, np.ndarray):
    print("Shape:", image_downloaded.shape)
    print("Dtype:", image_downloaded.dtype)

# print(metadata_serialize(image_id))
# print(dataset_serialize(dataset))

show_image_cv2(image_downloaded)


