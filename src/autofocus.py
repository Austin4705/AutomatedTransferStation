import cv2
import numpy as np
import cpbd 

class Autofocus:
    def __init__(self):
        pass

    @staticmethod
    def calculate_focus_score(image):
        image_filtered = cv2.GaussianBlur(image, (9, 9), 0)
        laplacian = cv2.Laplacian(image_filtered, cv2.CV_64F)
        focus_score = laplacian.var()
        return focus_score

    @staticmethod
    def get_edge_count(image):
        edges = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(edges, 100, 200) 
        return np.sum(edges > 30)

    @staticmethod
    def get_color_features(image, saturation_threshold=40):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1]
        color_mask  = sat > saturation_threshold
        colorful_pixels = np.count_nonzero(color_mask)
        total_pixels = image.shape[0] * image.shape[1]

        color_ratio = colorful_pixels / total_pixels
        return color_ratio

    @staticmethod
    def exist_color_features(image, ratio_threshold=0.05):
        color_ratio = Autofocus.get_color_features(image)
        return color_ratio >= ratio_threshold

    @staticmethod
    def calculate_cpbd(image):
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        return cpbd.compute(gray)