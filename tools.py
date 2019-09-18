import math


def distance_to_line(x, y, ax, ay, bx, by):
    x_diff = bx - ax
    y_diff = by - ay
    num = abs(y_diff * x - x_diff * y + bx * ay - by * ax)
    den = math.sqrt(y_diff ** 2 + x_diff ** 2)
    return num / den


def contour_box_avg_distance(contour, bounding_box):
    avg = 0
    for i, p in enumerate(contour):
        p = p[0]
        d = None
        for c1 in range(4):
            c2 = (c1 + 1) % 4
            dx = distance_to_line(p[0], p[1],
                                  bounding_box[c1][0], bounding_box[c1][1],
                                  bounding_box[c2][0], bounding_box[c2][1])

            if d is None or dx < d:
                d = dx

        if i == 0:
            avg = d
        else:
            avg = (avg * (i - 1) + d) / i

    return avg
