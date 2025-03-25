import cv2
from GMMDetector import MaterialDetector
import numpy as np
import matplotlib.cm as cm
import json

class CVFunctions:

    contrast_dict = json.load(open("../contrastDictDir/Graphene_GMM.json", "r"))

    def __init__(self) -> None:
        self.mockImage = np.zeros((512, 512, 3), dtype=np.uint8)
        CVFunctions.matGMM2DTransform(self.mockImage)

    def run_searching(img):
        model = MaterialDetector(
            contrast_dict=CVFunctions.contrast_dict,
            size_threshold=500,
            standard_deviation_threshold=5,
            used_channels="BGR",
        )

        flakes = model.detect_flakes(img)
        return flakes

    def matGMM2DTransform(img):
        flakes = CVFunctions.run_searching(img)

        CONFIDENCE_THRESHOLD = 0.5
        image = CVFunctions.visualise_flakes(
            flakes,
            img,
            confidence_threshold=CONFIDENCE_THRESHOLD,
        )
        return image

    def cvImageBoarderOp(img):
        # Convert to YCrCb Channel and extract cb channel
        imgYCrCb = cv2.cvtColor(img, cv2.COLOR_BGR2YCR_CB)
        channel = imgYCrCb[:, :, 2]

        ret, threshold = cv2.threshold(channel, 160, 255, cv2.THRESH_BINARY)

        result = img.copy()
        contours, hierarchy = cv2.findContours(
            threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        # contours = contours[0] if len(contours) == 2 else contours[1]
        cv2.drawContours(result, contours, -1, (0, 255, 0), 3)

        for cont in contours:
            maxX = cont[0][0]
            maxY = cont[0][0]
            minX = cont[0][0]
            minY = cont[0][0]
            for point in cont:
                pt = point[0]
                if pt[0] > maxX[0]:
                    maxX = pt
                elif pt[0] == maxX[0]:
                    maxX = [pt[0], max(pt[1], maxX[1])]

                if pt[0] < minX[0]:
                    minX = pt
                elif pt[0] == minX[0]:
                    minX = [pt[0], min(pt[1], minX[1])]

                if pt[1] > maxY[1]:
                    maxY = pt
                elif pt[1] == maxY[1]:
                    maxY = [max(pt[0], maxY[0]), pt[1]]

                if pt[1] < minY[1]:
                    minY = pt
                elif pt[1] == minY[1]:
                    minY = [min(pt[0], maxY[0]), pt[1]]
            cv2.line(result, minX, minY, [0, 255, 0], 10)
            cv2.line(result, minY, maxX, [0, 255, 0], 10)
            cv2.line(result, maxX, maxY, [0, 255, 0], 10)
            cv2.line(result, maxY, minX, [0, 255, 0], 10)
            # print(f"{minX}, {minY}, {maxX}, {maxY}")
            return minX, minY, maxX, maxY
            
    def visualise_flakes(flakes, image: np.ndarray, confidence_threshold: float = 0.5,) -> np.ndarray:
        """Visualise the flakes on the image.

        Args:
            flakes (List[Flake]): List of flakes to visualise.
            image (np.ndarray): Image to visualise the flakes on.
            confidence_threshold (float, optional): The confidence threshold to use, flakes with less confidence are not drawn. Defaults to 0.5.

        Returns:
            np.ndarray: Image with the flakes visualised.
        """

        confident_flakes = [
            flake
            for flake in flakes
            if (1 - flake.false_positive_probability) > confidence_threshold
        ]

        # get a colors for each flake
        colors = cm.rainbow(np.linspace(0, 1, len(confident_flakes)))[:, :3] * 255

        image = image.copy()
        for idx, flake in enumerate(confident_flakes):
            flake_contour = cv2.morphologyEx(
                flake.mask, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)
            )
            image[flake_contour > 0] = colors[idx]

            # put the text on the top right corner of the image
            cv2.putText(
                image,
                f"{(idx + 1):2}. {flake.thickness:1}L {int(flake.size * 0.3844**2):4}um2 {1- flake.false_positive_probability:.0%}",
                (10, 30 * (idx + 1)),
                cv2.QT_FONT_NORMAL,
                1,
                (255, 255, 255),
                2,
            )

            # draw a line from the text to the center of the flake
            cv2.line(
                image,
                (370, 30 * (idx + 1) - 15),
                (int(flake.center[0]), int(flake.center[1])),
                colors[idx],
                2,
            )

        return image

    def calculate_focus_score(image):
        image_filtered = cv2.GaussianBlur(image, (9, 9), 0)
        laplacian = cv2.Laplacian(image_filtered, cv2.CV_64F)
        focus_score = laplacian.var()
        return focus_score
