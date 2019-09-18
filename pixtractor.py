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
        self.bw_thresh = Parameter(200, 0, 255, 10, "B/W Thresh")
        self.bbox_min_size_prop = Parameter(5, 0, 100, 1, "Detectable min surface (% total)")
        self.bbox_fill_thresh = Parameter(75, 0, 100, 1, "Boundind box % fill-up threshold")


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

    def get_bbxs(self, draw_contours=False):

        ret, thresh = cv2.threshold(self.image_gray, self.params.bw_thresh.value, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if hierarchy is not None:
            hierarchy = hierarchy[0]

        h, w, channels = self.image.shape
        img_area = h * w
        min_area = self.params.bbox_min_size_prop.value / 100 * img_area

        if draw_contours:
            preview = self.image.copy()
        else:
            preview = None

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
                # Draw contour and bbox
                if preview is not None:
                    cv2.polylines(preview, [contour], True, (255, 0, 0))
                    cv2.polylines(preview, [bounding_box], True, (0, 0, 255), 2)
                print(f'Contour {n}: parent: {parent} fill_ratio: {fill_ratio} bbox_area: {bbox_area}')

        if preview is not None:
            return bboxes, cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        else:
            return bboxes, cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)