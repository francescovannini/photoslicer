import numpy as np


def distance_points(a, b):
    return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def crop_to_circle(img, center, radius):
    x1 = center[0] - radius
    y1 = center[1] - radius
    x2 = center[0] + radius
    y2 = center[1] + radius

    if x1 < 0 or y1 < 0 or x2 > img.shape[1] or y2 > img.shape[0]:
        img = np.pad(img, ((np.abs(np.minimum(0, y1)), np.maximum(y2 - img.shape[0], 0)),
                           (np.abs(np.minimum(0, x1)), np.maximum(x2 - img.shape[1], 0)),
                           (0, 0)),
                     mode="constant")

        y2 += np.abs(np.minimum(0, y1))
        y1 += np.abs(np.minimum(0, y1))
        x2 += np.abs(np.minimum(0, x1))
        x1 += np.abs(np.minimum(0, x1))

    return img[y1:y2, x1:x2, :]


def shift_points_to_min_distance(bbox1, bbox2):
    # TODO check input be quadrilateral
    dists = np.array([0, 0, 0, 0])
    for i, d in enumerate(dists):
        shifted = np.roll(bbox1, i, axis=0)
        for j, p in enumerate(bbox2):
            dists[i] += distance_points(shifted[j], p)

    best = np.where(dists == np.amin(dists))
    return np.roll(bbox1, best[0], axis=0), best[0][0]
