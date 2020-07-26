import cv2
import numpy as np
from random import randint


class HullTools:

    def __init__(self, h):
        self.hull = np.reshape(h, (-1, 2))

    def _tri_area(self, a, b, c):
        return abs(0.5 * (((b[0] - a[0]) * (c[1] - a[1])) - ((c[0] - a[0]) * (b[1] - a[1]))))

    def _seg_intersect(self, a1, a2, b1, b2):
        l1 = [(a1[1] - a2[1]), (a2[0] - a1[0]), -(a1[0] * a2[1] - a2[0] * a1[1])]
        l2 = [(b1[1] - b2[1]), (b2[0] - b1[0]), -(b1[0] * b2[1] - b2[0] * b1[1])]

        d = l1[0] * l2[1] - l1[1] * l2[0]
        dx = l1[2] * l2[1] - l1[1] * l2[2]
        dy = l1[0] * l2[2] - l1[2] * l2[0]
        if d != 0:
            x = dx / d
            y = dy / d
            return x, y
        else:
            return False

    def simplify(self, v):
        history = []

        # https://stackoverflow.com/a/2050478/8562992
        hull_buffer = np.copy(self.hull)
        while len(hull_buffer) > v:
            history.append(np.copy(hull_buffer))
            min_area = None
            rmv_idx_1 = None
            rmv_idx_2 = None
            new_idx = None

            for idx in range(len(hull_buffer)):

                # For every 4 consecutive vertices, 3 consecutive segments on the hull path...
                i0 = idx
                i1 = (idx + 1) % len(hull_buffer)
                i2 = (idx + 2) % len(hull_buffer)
                i3 = (idx + 3) % len(hull_buffer)

                # Find the intersection between the external segments when extended to infinity
                s = self._seg_intersect(hull_buffer[i0], hull_buffer[i1], hull_buffer[i2], hull_buffer[i3])

                # Check that if it exists...
                if not s:
                    continue

                # ...the intersection is outside the hull (should always be for a convex hull)
                # if cv2.pointPolygonTest(self.hull, s, False) > 0:
                #     continue

                # Calculate area of triangle built on the intersection point and the central segment
                tri_area = self._tri_area(hull_buffer[i1], hull_buffer[i2], s)

                # Check if area is smaller than other triangles
                if min_area is None or tri_area < min_area:
                    min_area = tri_area
                    rmv_idx_1 = i1
                    rmv_idx_2 = i2
                    new_idx = s

            # We can't simplify the hull
            if min_area is None:
                return None, None

            # Replace two points of the hull with one point
            # The points to be replaced are at the base of the smallest triangle found
            # The new point is the opposing to the base vertex of the triangle (the intersection from above)
            new_hl = []
            for idx, p in enumerate(hull_buffer):
                if idx == rmv_idx_1:
                    new_hl.append(new_idx)
                    continue

                if idx == rmv_idx_2:
                    continue

                new_hl.append(p)

            hull_buffer = np.reshape(new_hl, (-1, 2))

        return np.int0(hull_buffer), history
