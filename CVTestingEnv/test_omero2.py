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
show_image_cv2(image)

project = image_container.create_project("test-project")
dataset = image_container.create_dataset("test-dataset", project_id=project)

image_id = image_container.upload_image(image, dataset_id=dataset)
image_downloaded = image_container.download_image(image_id)


cv2.imshow("image_downloaded", image_downloaded)
cv2.waitKey(0)
cv2.destroyAllWindows()