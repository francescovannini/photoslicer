import cv2
from tkinter.tix import *
from tools import *


class Parameter:
    def __init__(self, default, min, max, step, label):
        self.default = default
        self.min = min
        self.max = max
        self.step = step
        self.label = label
        self.control = None
        self.tk_var = IntVar(value=default)

    def get(self):
        return self.tk_var.get()

    def reset(self):
        self.tk_var.set(self.default)


class AutoslicerParams:
    def __init__(self):
        self.gaussian = Parameter(25, 0, 100, 1, "Gaussian blur (0=disabled)")
        self.bw_method = Parameter(0, 0, 2, 1, "BW Thresh Method (0=Simple, 1=Gauss, 2=Outso)")
        self.bw_thresh = Parameter(230, 0, 255, 5, "BW Simple/Outso Thresh Min Value")
        self.bw_gauss = Parameter(51, 0, 1000, 2, "BW Gauss block size")
        self.bbox_min_size_prop = Parameter(5, 0, 100, 1, "Detectable min surface (% total)")
        self.bbox_fill_thresh = Parameter(65, 0, 100, 1, "Bounding box fill ratio threshold")
        self.dilate_kernel = Parameter(15, 0, 500, 1, "Dilate kernel size (0=disabled)")
        self.preview_filter_output = Parameter(0, 0, 1, 1, "Preview filter output")


class Autoslicer:
    def __init__(self, params=None):
        self.image = None
        self.image_gray = None
        self.abort_flag = False
        self.params = None
        self.set_params(params)

    def set_params(self, params):
        if params is not None:
            self.params = params
        else:
            self.params = AutoslicerParams()

    def image_loaded(self):
        return self.image is not None

    def load_image(self, image_path):
        self.image = cv2.imread(image_path)
        self.image_gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def abort_operation(self):
        self.abort_flag = True

    # Find all bbox related to n
    def get_box_relatives(self, hierarchy, n):
        relatives = []

        while 1:
            father = hierarchy[n][3]
            if father >= 0:
                relatives.append(father)
                n = father
            else:
                return relatives

    def autodetect_slices(self, update_status_callback=None):
        filter_out = self.image_gray
        self.abort_flag = False

        # Gaussian blur
        if self.params.gaussian.get() > 0:
            update_status_callback("Gaussian blur...")

            if self.params.gaussian.get() % 2 == 0:
                block = self.params.gaussian.get() + 1
            else:
                block = self.params.gaussian.get()
            filter_out = cv2.GaussianBlur(filter_out, (block, block), 0)

        # Binary filter
        if self.params.bw_method.get() == 0:
            update_status_callback("Simple binary thresholding...")
            ret, filter_out = cv2.threshold(filter_out, self.params.bw_thresh.get(), 255, cv2.THRESH_BINARY)

        # Adaptive thresh
        if self.params.bw_method.get() == 1:
            update_status_callback("Adaptive Gaussian thresholding...")
            if self.params.bw_gauss.get() % 2 == 0:
                block = self.params.bw_gauss.get() + 1
            else:
                block = self.params.bw_gauss.get()
            filter_out = cv2.adaptiveThreshold(filter_out, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                               block, 2)

        # Otsu thresh
        if self.params.bw_method.get() == 2:
            update_status_callback("Otsu thresholding...")
            ret, filter_out = cv2.threshold(filter_out, self.params.bw_thresh.get(), 255,
                                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Dilate
        if self.params.dilate_kernel.get() > 0:
            update_status_callback("Dilate...")
            kernel = np.ones((self.params.dilate_kernel.get(), self.params.dilate_kernel.get()), np.uint8)
            filter_out = cv2.dilate(filter_out, kernel)

        # Find contours
        update_status_callback("Finding contours...")
        _, contours, hierarchy = cv2.findContours(filter_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if hierarchy is not None:
            hierarchy = hierarchy[0]
        else:
            if self.params.preview_filter_output.get() > 0:
                return [], cv2.cvtColor(filter_out, cv2.COLOR_GRAY2RGB)
            else:
                return [], cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)

        # Calculate total image area and minimum box thresh
        h, w, channels = self.image.shape
        img_area = h * w
        min_area = self.params.bbox_min_size_prop.get() / 100 * img_area

        boxes = []
        good_ids = []
        discarded_ids = []
        for n, contour in enumerate(contours):

            if self.abort_flag:
                boxes = []
                break

            # No triangles
            if len(contour) < 4:
                discarded_ids.append(n)
                continue

            update_status_callback("Processing contour " + str(n) + "/" + str(len(contours)))

            # If child of a selected bbox, then it's discarded (it's inside)
            relatives = self.get_box_relatives(hierarchy, n)
            if set(relatives).intersection(good_ids):
                discarded_ids.append(n)
                continue

            # Find bounding box
            bbox_rot_rect = cv2.minAreaRect(contour)
            bounding_box = cv2.boxPoints(bbox_rot_rect)
            bounding_box = np.int0(bounding_box)
            shape_area = cv2.contourArea(contour)
            bbox_area = cv2.contourArea(bounding_box)

            # Too small or too big
            if shape_area < 1 or bbox_area < min_area or bbox_area > img_area * 0.90:
                discarded_ids.append(n)
                continue

            # Fill ratio
            fill_ratio = (bbox_area - (bbox_area - shape_area)) / bbox_area * 100
            if fill_ratio < self.params.bbox_fill_thresh.get():
                discarded_ids.append(n)
                continue

            # It's good
            good_ids.append(n)
            boxes.append(bounding_box)

        if self.params.preview_filter_output.get() > 0:
            return boxes, cv2.cvtColor(filter_out, cv2.COLOR_GRAY2RGB)
        else:
            return boxes, cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)

    def save_slice(self, hull_quad, out_path):

        src_img = self.image

        # Get bounding rotated rectangle containing the simplified hull
        hull_quad_rbb = cv2.minAreaRect(hull_quad)
        hull_quad_rbb_pts = cv2.boxPoints(hull_quad_rbb)

        # Minimize distance between hull points and its bbox points
        hull_quad = shift_points_to_min_distance(hull_quad, hull_quad_rbb_pts)

        # For debugging
        cv2.drawContours(src_img, [np.int0(hull_quad_rbb_pts)], -1, (0, 0, 255), 1)
        cv2.circle(src_img, tuple(hull_quad_rbb_pts[0]), 10, (0, 0, 255), 2)
        cv2.drawContours(src_img, [np.int0(hull_quad)], -1, (0, 255, 0), 1)
        cv2.circle(src_img, tuple(hull_quad[0]), 5, (0, 255, 0), 2)

        # Get the circle enclosing the bounding box enclosing the hull
        hull_quad_rbb_ecirc_c, hull_quad_rbb_ecirc_r = cv2.minEnclosingCircle(hull_quad_rbb_pts)
        hull_quad_rbb_ecirc_c = tuple(map(int, hull_quad_rbb_ecirc_c))
        hull_quad_rbb_ecirc_r = int(hull_quad_rbb_ecirc_r)
        hull_quad_rbb_topleft_pt = \
            (int(hull_quad_rbb_ecirc_c[0] - hull_quad_rbb_ecirc_r),
             int(hull_quad_rbb_ecirc_c[1] - hull_quad_rbb_ecirc_r))

        # For debugging
        cv2.circle(src_img, hull_quad_rbb_ecirc_c, hull_quad_rbb_ecirc_r, (0, 255, 0), 5)
        cv2.circle(src_img, hull_quad_rbb_ecirc_c, 10, (0, 255, 0), 2)
        cv2.circle(src_img, hull_quad_rbb_topleft_pt, 10, (255, 255, 0), 2)

        # Crop to circle
        hull_quad_img = crop_to_circle(src_img, hull_quad_rbb_ecirc_c, hull_quad_rbb_ecirc_r)

        # Calculate offset array and apply offset to hull, hull bbox and hull bbox enclosing circle center
        offset_a = np.array(hull_quad_rbb_topleft_pt)
        for i in range(0, 3):
            offset_a = np.append(offset_a, hull_quad_rbb_topleft_pt)
        offset_a = offset_a.reshape(4, 2)
        hull_quad = hull_quad - offset_a
        hull_quad_rbb_pts = hull_quad_rbb_pts - offset_a
        hull_quad_rbb_ecirc_c = tuple(map(lambda ki, kj: ki - kj, hull_quad_rbb_ecirc_c, hull_quad_rbb_topleft_pt))

        # Homography for perspective adjust
        hg_perspective_adj, _ = cv2.findHomography(hull_quad, hull_quad_rbb_pts)
        hull_quad_img_h, hull_quad_img_w = hull_quad_img.shape[:2]
        warped_img = cv2.warpPerspective(hull_quad_img, hg_perspective_adj, (hull_quad_img_h, hull_quad_img_w),
                                         flags=cv2.INTER_CUBIC)

        # Get hull rotated bounding box size and angle; center is taken from enclosing circle
        _, hull_quad_rbb_s, hull_quad_rbb_a = hull_quad_rbb
        hull_quad_rbb_s = tuple(map(int, hull_quad_rbb_s))

        # Get rotation matrix from rectangle
        hull_quad_rot_matrix = cv2.getRotationMatrix2D(hull_quad_rbb_ecirc_c, hull_quad_rbb_a, 1)

        # Perform rotation on src image
        warped_rotated_img = cv2.warpAffine(warped_img, hull_quad_rot_matrix, warped_img.shape[:2],
                                            flags=cv2.INTER_CUBIC)

        # Crop based on size of bbox and center of enclosing circle
        warped_rotated_cropped_img = cv2.getRectSubPix(warped_rotated_img, hull_quad_rbb_s, hull_quad_rbb_ecirc_c)
        cv2.imwrite(out_path, warped_rotated_cropped_img)
