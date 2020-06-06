import cv2
import numpy as np


class Parameter:
    def __init__(self, value, min, max, step, label):
        self.value = value
        self.min = min
        self.max = max
        self.step = step
        self.label = label
        self.control = None

    def update(self):
        self.value = int(self.control.get())


class PixtractorParams:
    def __init__(self):

        self.bw_method = Parameter(0, 0, 2, 1, "BW Thresh Method (0=Simple, 1=Gauss, 2=Outso)")
        self.bw_thresh = Parameter(180, 0, 255, 5, "BW Simple Thresh Min Value")
        self.bw_gauss = Parameter(50, 0, 1000, 10, "BW Gauss block size")
        self.bbox_min_size_prop = Parameter(1, 0, 100, .1, "Detectable min surface (% total)")
        self.bbox_fill_thresh = Parameter(50, 0, 100, 1, "Bounding fill ratio threshold")
        self.dilate_kernel = Parameter(10, 0, 500, 1, "Dilate matrix size (0=disabled)")
        self.preview_filter_output = Parameter(0, 0, 1, 1, "Preview filter output")


class Pixtractor:
    def __init__(self, params=None):
        self.image = None
        self.image_gray = None

        if params is not None:
            self.params = params
        else:
            self.params = PixtractorParams()

    def image_loaded(self):
        return self.image is not None

    def load_image(self, image_path):
        self.image = cv2.imread(image_path)
        self.image_gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def get_bbxs(self):

        filter_out = self.image_gray

        # Binary filter
        if self.params.bw_method.value == 0:
            ret, filter_out = cv2.threshold(self.image_gray, self.params.bw_thresh.value, 255, cv2.THRESH_BINARY)

        if self.params.bw_method.value == 1:
            if self.params.bw_gauss.value % 2 == 0:
                block = self.params.bw_gauss.value + 1
            else:
                block = self.params.bw_gauss.value
            filter_out = cv2.adaptiveThreshold(self.image_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                               block, 2)

        if self.params.bw_method.value == 2:
            ret, filter_out = cv2.threshold(self.image_gray, self.params.bw_thresh.value, 255,
                                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Erosion
        if self.params.dilate_kernel.value > 0:
            kernel = np.ones((self.params.dilate_kernel.value, self.params.dilate_kernel.value), np.uint8)
            filter_out = cv2.dilate(filter_out, kernel)

        # Find contours
        contours, hierarchy = cv2.findContours(filter_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if hierarchy is not None:
            hierarchy = hierarchy[0]

        h, w, channels = self.image.shape
        img_area = h * w
        min_area = self.params.bbox_min_size_prop.value / 100 * img_area

        bboxes = []
        for n, contour in enumerate(contours):
            parent = hierarchy[n][3]

            if len(contour) < 4:
                continue

            # Find bounding box
            bbox_rot_rect = cv2.minAreaRect(contour)
            bounding_box = cv2.boxPoints(bbox_rot_rect)
            bounding_box = np.int0(bounding_box)

            shape_area = cv2.contourArea(contour)
            bbox_area = cv2.contourArea(bounding_box)

            # Too small or too big
            if shape_area < 1 or bbox_area < min_area or bbox_area > img_area * 0.80:
                continue

            fill_ratio = (bbox_area - (bbox_area - shape_area)) / bbox_area * 100

            if fill_ratio > self.params.bbox_fill_thresh.value:
                bboxes.append(bounding_box)

        if self.params.preview_filter_output.value > 0:
            return bboxes, cv2.cvtColor(filter_out, cv2.COLOR_BGR2RGB)
        else:
            return bboxes, cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
