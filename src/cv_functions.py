import cv2
# from GMMDetector import MaterialDetector
import numpy as np
import matplotlib.cm as cm
import json

class CV_Functions:

    # contrast_dict = json.load(open("../contrastDictDir/Graphene_GMM.json", "r"))

    def __init__(self) -> None:
        pass
        # self.mockImage = np.zeros((512, 512, 3), dtype=np.uint8)
        # CV_Functions.matGMM2DTransform(self.mockImage)

    def whitebalance_greyworld2(image):
        """
        White balance using gray world assumption.
        """
        # return image
        pixels = image.reshape(-1, 3)
        brightness = pixels.sum(axis=1)
        mask = brightness > 30  # Exclude pixels with sum < 30 (very dark)
        pixels = pixels[mask]
        
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        most_common_idx = np.argmax(counts)
        color = unique_colors[most_common_idx].astype(np.float32)
        
        avg= (color[0] + color[1] + color[2]) / 3.0
        scale_r = avg / color[0] if color[0] > 0 else 1.0
        scale_g = avg / color[1] if color[1] > 0 else 1.0
        scale_b = avg / color[2] if color[2] > 0 else 1.0

        result[:, :, 0] *= scale_r
        result[:, :, 1] *= scale_g
        result[:, :, 2] *= scale_b

        result = np.clip(result, 0, 255)
        print(f"Scale factors: R={scale_r:.3f}, G={scale_g:.3f}, B={scale_b:.3f}")
        return result.astype(np.uint8)

    def whitebalance(image):
        # return image
        result = image.astype(np.float32)
        quantized = (image // 8) * 8
        brightness = quantized.sum(axis=2)
        mask = brightness > 30
        filtered = quantized[mask]
        
        colors_as_int = (filtered[:, 0].astype(np.int32) << 16) | (filtered[:, 1].astype(np.int32) << 8) | filtered[:, 2].astype(np.int32)
        
        counts = np.bincount(colors_as_int)
        most_common_int = np.argmax(counts)
        
        color = np.array([
            (most_common_int >> 16) & 0xFF,
            (most_common_int >> 8) & 0xFF,
            most_common_int & 0xFF
        ], dtype=np.float32)
        
        avg_gray = (color[0] + color[1] + color[2]) / 3.0
        scale_r = avg_gray / color[0] if color[0] > 0 else 1.0
        scale_g = avg_gray / color[1] if color[1] > 0 else 1.0
        scale_b = avg_gray / color[2] if color[2] > 0 else 1.0
        # print(f"Most common color: RGB({color[0]}, {color[1]}, {color[2]})")
        # print(f"Scale factors: R={scale_r:.3f}, G={scale_g:.3f}, B={scale_b:.3f}")
        result[:, :, 0] *= scale_r
        result[:, :, 1] *= scale_g
        result[:, :, 2] *= scale_b

        result = np.clip(result, 0, 255)
        return result.astype(np.uint8)


    def whitebalance_greyworld(image):
        # Grayworld method
        result = image.astype(np.float32)
        avg_r = np.mean(result[:, :, 0])
        avg_g = np.mean(result[:, :, 1])
        avg_b = np.mean(result[:, :, 2])
        avg_gray = (avg_r + avg_g + avg_b) / 3.0

        scale_r = avg_gray / avg_r if avg_r > 0 else 1.0
        scale_g = avg_gray / avg_g if avg_g > 0 else 1.0
        scale_b = avg_gray / avg_b if avg_b > 0 else 1.0

        result[:, :, 0] *= scale_r
        result[:, :, 1] *= scale_g
        result[:, :, 2] *= scale_b

        result = np.clip(result, 0, 255)
        return result.astype(np.uint8)
    

    # def run_searching(img):
    #     model = MaterialDetector(
    #         contrast_dict=CV_Functions.contrast_dict,
    #         size_threshold=500,
    #         standard_deviation_threshold=5,
    #         used_channels="BGR",
    #     )

    #     flakes = model.detect_flakes(img)
    #     return flakes

    # def matGMM2DTransform(img):
    #     flakes = CV_Functions.run_searching(img)

    #     CONFIDENCE_THRESHOLD = 0.5
    #     image = CV_Functions.visualise_flakes(
    #         flakes,
    #         img,
    #         confidence_threshold=CONFIDENCE_THRESHOLD,
    #     )
    #     return image

    # def generate_image_output(self):
    #     pass
    #     # for image_metadata in self.metadata.get("searched"):
    #     #     image = self.load_image(image_metadata["name"], image_metadata["wafer_id"])
    #     #     flakes = [
    #     #         Flake(
    #     #             thickness=flake.get("thickness"),
    #     #             size=flake.get("size"), 
    #     #             false_positive_probability=flake.get("false_positive_probability"),
    #     #             center=flake.get("center"),
    #     #             mask=cv2.imread(os.path.join(self.directory_flake_masks, flake.get("mask")), cv2.IMREAD_GRAYSCALE),
    #     #             max_sidelength=flake.get("max_sidelength"),  # Default values for required parameters
    #     #             min_sidelength=flake.get("min_sidelength"),  # Default values for required parameters
    #     #             mean_contrast=flake.get("mean_contrast")  #
    #     #         )
    #     #         for flake in image_metadata.get("flakes", [])
    #     #     ]
    #     #     # image_data = CV_Functions.visualise_flakes(flakes, image, 0.5)
    #     #     image_data = image
    #     #     # Add wafer and position text
    #     #     cv2.putText(
    #     #         image_data,
    #     #         f"Wafer: {image_metadata['wafer_id']}", 
    #     #         (image_data.shape[1] - 300, 30),
    #     #         cv2.FONT_HERSHEY_SIMPLEX,
    #     #         1,
    #     #         (255, 255, 255),
    #     #         2
    #     #     )
    #     #     cv2.putText(
    #     #         image_data,
    #     #         f"Image Number: {image_metadata['image_id']}", 
    #     #         (image_data.shape[1] - 300, 60),
    #     #         cv2.FONT_HERSHEY_SIMPLEX,
    #     #         1,
    #     #         (255, 255, 255),
    #     #         2
    #     #     )
    #     #     cv2.putText(
    #     #         image_data,
    #     #         f"x: {image_metadata['x']} y: {image_metadata['y']}", 
    #     #         (image_data.shape[1] - 300, 90),
    #     #         cv2.FONT_HERSHEY_SIMPLEX,
    #     #         1,
    #     #         (255, 255, 255),
    #     #         2
    #     #     )
    #     #     cv2.imwrite(os.path.join(self.directory_searched, image_metadata["name"]), image_data)

        

    # def cvImageBoarderOp(img):
    #     # Convert to YCrCb Channel and extract cb channel
    #     imgYCrCb = cv2.cvtColor(img, cv2.COLOR_BGR2YCR_CB)
    #     channel = imgYCrCb[:, :, 2]

    #     ret, threshold = cv2.threshold(channel, 160, 255, cv2.THRESH_BINARY)

    #     result = img.copy()
    #     contours, hierarchy = cv2.findContours(
    #         threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    #     )
    #     # contours = contours[0] if len(contours) == 2 else contours[1]
    #     cv2.drawContours(result, contours, -1, (0, 255, 0), 3)

    #     for cont in contours:
    #         maxX = cont[0][0]
    #         maxY = cont[0][0]
    #         minX = cont[0][0]
    #         minY = cont[0][0]
    #         for point in cont:
    #             pt = point[0]
    #             if pt[0] > maxX[0]:
    #                 maxX = pt
    #             elif pt[0] == maxX[0]:
    #                 maxX = [pt[0], max(pt[1], maxX[1])]

    #             if pt[0] < minX[0]:
    #                 minX = pt
    #             elif pt[0] == minX[0]:
    #                 minX = [pt[0], min(pt[1], minX[1])]

    #             if pt[1] > maxY[1]:
    #                 maxY = pt
    #             elif pt[1] == maxY[1]:
    #                 maxY = [max(pt[0], maxY[0]), pt[1]]

    #             if pt[1] < minY[1]:
    #                 minY = pt
    #             elif pt[1] == minY[1]:
    #                 minY = [min(pt[0], maxY[0]), pt[1]]
    #         cv2.line(result, minX, minY, [0, 255, 0], 10)
    #         cv2.line(result, minY, maxX, [0, 255, 0], 10)
    #         cv2.line(result, maxX, maxY, [0, 255, 0], 10)
    #         cv2.line(result, maxY, minX, [0, 255, 0], 10)
    #         # print(f"{minX}, {minY}, {maxX}, {maxY}")
    #         return minX, minY, maxX, maxY
            
    # def visualise_flakes(flakes, image: np.ndarray, confidence_threshold: float = 0.5,) -> np.ndarray:
    #     """Visualise the flakes on the image.

    #     Args:
    #         flakes (List[Flake]): List of flakes to visualise.
    #         image (np.ndarray): Image to visualise the flakes on.
    #         confidence_threshold (float, optional): The confidence threshold to use, flakes with less confidence are not drawn. Defaults to 0.5.

    #     Returns:
    #         np.ndarray: Image with the flakes visualised.
    #     """

    #     confident_flakes = [
    #         flake
    #         for flake in flakes
    #         if (1 - flake.false_positive_probability) > confidence_threshold
    #     ]

    #     # get a colors for each flake
    #     colors = cm.rainbow(np.linspace(0, 1, len(confident_flakes)))[:, :3] * 255

    #     image = image.copy()
    #     for idx, flake in enumerate(confident_flakes):
    #         flake_contour = cv2.morphologyEx(
    #             flake.mask, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)
    #         )
    #         image[flake_contour > 0] = colors[idx]

    #         # put the text on the top right corner of the image
    #         cv2.putText(
    #             image,
    #             f"{(idx + 1):2}. {flake.thickness:1}L {int(flake.size * 0.3844**2):4}um2 {1- flake.false_positive_probability:.0%}",
    #             (10, 30 * (idx + 1)),
    #             cv2.QT_FONT_NORMAL,
    #             1,
    #             (255, 255, 255),
    #             2,
    #         )

    #         # draw a line from the text to the center of the flake
    #         cv2.line(
    #             image,
    #             (370, 30 * (idx + 1) - 15),
    #             (int(flake.center[0]), int(flake.center[1])),
    #             colors[idx],
    #             2,
    #         )

    #     return image

    # def line_rgb_values(image: np.ndarray, start, end):
    #     """
    #     Given an image (H, W, 3) and start=(x0,y0), end=(x1,y1),
    #     return RGB values along the line connecting them.
    #     """
    #     x0, y0 = start
    #     x1, y1 = end
    #     num_points = int(np.hypot(x1 - x0, y1 - y0)) + 1
    #     x, y = np.linspace(x0, x1, num_points), np.linspace(y0, y1, num_points)
    #     x, y = np.round(x).astype(int), np.round(y).astype(int)
    #     # Clip to image bounds
    #     x = np.clip(x, 0, image.shape[1] - 1)
    #     y = np.clip(y, 0, image.shape[0] - 1)
    #     rgb = image[y, x]
    #     return rgb

    # def generate_brightness_line(image: np.ndarray, start, end):
    #     rgb = line_rgb_values(image, start, end)
    #     # NTSC Coefficients for brightness
    #     brightness = 0.299 * rgb[:,0] + 0.587 * rgb[:,1] + 0.114 * rgb[:,2]
    #     return brightness