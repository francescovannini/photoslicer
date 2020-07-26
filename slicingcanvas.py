from tkinter import *
from PIL import Image, ImageTk
from shapely.geometry import Polygon


def slice_corner_tag(s, i):
    return "crn_" + str(s) + "x" + str(i)


def get_slice_and_corner_from_tags(tags):
    tag = next(filter(lambda x: x.startswith('crn_'), tags))
    sc = tag.split("_")[1].split("x")
    s = int(sc[0])
    c = int(sc[1])
    return s, c


def slice_edge_tag(s, i):
    return "edg_" + str(s) + "x" + str(i)


def get_slice_and_edge_from_tags(tags):
    tag = next(filter(lambda x: x.startswith('edg_'), tags))
    se = tag.split("_")[1].split("x")
    s = int(se[0])
    e = int(se[1])
    return s, e


def slice_tag(s):
    return "slice_" + str(s)


def slice_label_tag(s):
    return "lbl_" + str(s)


def polys_iou(poly1, poly2):
    poly_1 = Polygon(poly1)
    poly_2 = Polygon(poly2)
    iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
    return iou


class PhotoSlice:
    def __init__(self, bbox):
        self.bbox = bbox
        self.locked = False

    def set_locked(self, locked=True):
        self.locked = locked

    def set_upper_left_from_line_index(self, i):
        j = i
        bbox = []
        for k in range(4):
            j += k
            if j > 3:
                j = 0
            bbox.append(self.bbox[j])

        self.bbox = bbox

    def update_corner(self, ci, x, y):
        self.bbox[ci][0] = x
        self.bbox[ci][1] = y


class SlicingCanvas(Canvas):
    def __init__(self, parent, **kwargs):
        Canvas.__init__(self, parent, **kwargs, borderwidth=0, highlightthickness=0, bg="black")
        self.zoom = 1.0
        self.image = None
        self.image_viewport = None
        self.picture_frame = None
        self.cross = [-1, -1, 8, -1, 8, 1, -8, 1, -8, -1, -1, -1, -1, -8, 1, -8, 1, 8, -1, 8]
        self.origin = [0, 0]
        self._on_bbox_updated = None
        self.slices = []

        # Events
        self.bind('<Configure>', self.update_view)
        self.bind('<ButtonPress-1>', self.view_drag_start)
        self.bind('<ButtonRelease-1>', self.view_drag_stop)
        self.bind('<B1-Motion>', self.view_drag)
        self.bind('<MouseWheel>', self.mouse_wheel)
        self.bind('<Button-5>', self.mouse_wheel)
        self.bind('<Button-4>', self.mouse_wheel)

        self.tag_bind("corner", "<ButtonPress-3>", self.corner_drag_start)
        self.tag_bind("corner", "<B3-Motion>", self.corner_drag)
        self.tag_bind("corner", "<ButtonRelease-3>", self.corner_drag_stop)

        # self.tag_bind("edge", "<ButtonPress-3>", self.edge_select_top)

        self.corner_dragging_buffer = {"x": 0, "y": 0, "item": None}
        self.view_dragging_buffer = {"x": 0, "y": 0}

    def set_on_bbox_updated(self, fn):
        self._on_bbox_updated = fn

    def set_image(self, image):
        if self.image is None or self.image.width != image.width or self.image.height != image.height:
            self.xview_moveto(0)
            self.yview_moveto(0)
            self.zoom = 1.0
            self.delete("frame")
            self.picture_frame = self.create_rectangle(0, 0, image.width, image.height, outline="", tags=("frame",))
            self.slices = []
        self.image = image

    def set_bboxes(self, bbxs=None):
        if bbxs is not None:
            merged_slices = []
            for sl in self.slices:
                if sl.locked:
                    merged_slices.append(sl)

            for box in bbxs:
                # Check if bbox is the same as one of our slices
                overlaps_locked = False
                # for sl in merged_slices:
                #     if polys_iou(box, sl.bbox) > 0.8:
                #         overlaps_locked = True
                #         break
                if not overlaps_locked:
                    s = PhotoSlice(box)
                    merged_slices.append(s)

            self.slices = merged_slices

        self.delete("slice")
        for b in range(len(self.slices)):
            self.__draw_slice(b)

        self.update_view()
        # if self._on_bbox_updated is not None:
        #     self._on_bbox_updated(self.bbxs)

    def view_drag_start(self, event):
        self.scan_mark(event.x, event.y)
        self.view_dragging_buffer["x"] = event.x
        self.view_dragging_buffer["y"] = event.y

    def view_drag(self, event):
        self.scan_dragto(event.x, event.y, gain=1)
        self.update_view()  # redraw the image

    def view_drag_stop(self, event):
        self.scan_dragto(event.x, event.y, gain=1)
        self.origin[0] += event.x - self.view_dragging_buffer["x"]
        self.origin[1] += event.y - self.view_dragging_buffer["y"]

    def mouse_wheel(self, event):
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)

        # Zoom only when pointer over image
        bbox = self.bbox(self.picture_frame)
        if not (bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]):
            return

        scale = 1.00000000
        delta = 1.10000000

        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:
            if self.zoom < 0.01:
                return

            self.zoom /= delta
            scale /= delta

        if event.num == 4 or event.delta == 120:  # scroll up
            if self.zoom > 20:
                return
            self.zoom *= delta
            scale *= delta

        self.scale('all', 0, 0, scale, scale)
        self.update_view(x, y)

    def corner_drag_start(self, event):
        self.corner_dragging_buffer["item"] = self.find_withtag("current")[0]
        self.corner_dragging_buffer["x"] = event.x
        self.corner_dragging_buffer["y"] = event.y

    def corner_drag(self, event):
        delta_x = event.x - self.corner_dragging_buffer["x"]
        delta_y = event.y - self.corner_dragging_buffer["y"]
        self.move(self.corner_dragging_buffer["item"], delta_x, delta_y)
        self.corner_dragging_buffer["x"] = event.x
        self.corner_dragging_buffer["y"] = event.y

    def corner_drag_stop(self, event):
        b, c = get_slice_and_corner_from_tags(self.gettags(self.corner_dragging_buffer["item"]))

        # Update bbox coords
        x = self.coords(self.corner_dragging_buffer["item"])[0] + 1
        y = self.coords(self.corner_dragging_buffer["item"])[1] + 1

        x /= self.zoom
        y /= self.zoom

        self.slices[b].update_corner(c, x, y)

        print(b, c)

        self.__draw_slice(b)

        # if self._on_bbox_updated is not None:
        #     self._on_bbox_updated(self.bbxs)

    def edge_select_top(self, event):
        line = self.find_withtag("current")[0]
        si, e = get_slice_and_edge_from_tags(self.gettags(line))
        self.slices[si].set_upper_left_from_line_index(e)
        self.__draw_slice(si)

    def __draw_slice(self, si):
        s = self.slices[si]
        s_tag = slice_tag(s)
        self.delete(s_tag)

        o = None
        q = None
        i = 0
        for p in s.bbox:

            poly = self.create_polygon(self.cross, outline="blue", activeoutline="red",
                                       fill="gray", stipple='@transp.xbm', width=3,
                                       tags=(s_tag, slice_corner_tag(si, i), "corner", "slice"))
            self.move(poly, p[0], p[1])
            self.scale(poly, 0, 0, self.zoom, self.zoom)

            if o is None:
                o = p
                q = p
                continue

            if i == 0:
                self.create_line(q[0] * self.zoom, q[1] * self.zoom, p[0] * self.zoom, p[1] * self.zoom,
                                 fill="red", width=3, tags=(s_tag, slice_edge_tag(si, i), "edge", "slice"))
            else:
                self.create_line(q[0] * self.zoom, q[1] * self.zoom, p[0] * self.zoom, p[1] * self.zoom,
                                 fill="lightgreen", width=2, tags=(s_tag, slice_edge_tag(si, i), "edge", "slice"))
            q = p
            i += 1

        self.create_line(q[0] * self.zoom, q[1] * self.zoom, o[0] * self.zoom, o[1] * self.zoom, fill="lightgreen",
                         width=2, tags=(s_tag, slice_edge_tag(si, i), "edge", "slice"))

        center = Polygon(s.bbox).centroid.coords[:]
        self.create_text(center, fill="lightgreen", text=str(si), font=('Arial', 30),
                         tags=("label", slice_label_tag(si), "slice"))

        self.tag_raise("corner")

    def update_view(self, x=0, y=0):
        if self.image is None:
            return

        pic_bbx = self.bbox(self.picture_frame)
        pic_bbx = (pic_bbx[0] + 1, pic_bbx[1] + 1, pic_bbx[2] - 1, pic_bbx[3] - 1)
        canvas_bbx = (self.canvasx(0),
                      self.canvasy(0),
                      self.canvasx(self.winfo_width()),
                      self.canvasy(self.winfo_height()))

        x1 = max(canvas_bbx[0] - pic_bbx[0], 0)
        y1 = max(canvas_bbx[1] - pic_bbx[1], 0)
        x2 = min(canvas_bbx[2], pic_bbx[2]) - pic_bbx[0]
        y2 = min(canvas_bbx[3], pic_bbx[3]) - pic_bbx[1]

        if int(x2 - x1) <= 0 or int(y2 - y1) <= 0:
            return

        x = min(int(x2 / self.zoom), self.image.width)
        y = min(int(y2 / self.zoom), self.image.height)

        image = self.image.crop((int(x1 / self.zoom), int(y1 / self.zoom), x, y))
        self.image_viewport = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
        canvas_image = self.create_image(max(canvas_bbx[0], pic_bbx[0]), max(canvas_bbx[1], pic_bbx[1]),
                                         anchor='nw', image=self.image_viewport)
        self.lower(canvas_image)
