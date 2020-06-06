from tkinter import *
from PIL import Image, ImageTk


class SlicingCanvas(Canvas):
    def __init__(self, parent, **kwargs):
        Canvas.__init__(self, parent, **kwargs, borderwidth=0, highlightthickness=0, bg="black")
        self.zoom = 1.0
        self.image = None
        self.imagetk = None
        self.picture_frame = None
        self.bbxs = None
        self.cross = [-1, -1, 8, -1, 8, 1, -8, 1, -8, -1, -1, -1, -1, -8, 1, -8, 1, 8, -1, 8]
        self.origin = [0, 0]
        self._on_bbox_updated = None

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

        self.corner_dragging_buffer = {"x": 0, "y": 0, "item": None}
        self.view_dragging_buffer = {"x": 0, "y": 0}

    def set_on_bbox_updated(self, fn):
        self._on_bbox_updated = fn

    def set_view(self, image, bbxs=None):
        if self.image is None or self.image.width != image.width or self.image.height != image.height:
            self.xview_moveto(0)
            self.yview_moveto(0)
            self.zoom = 1.0
            self.delete("frame")
            self.picture_frame = self.create_rectangle(0, 0, image.width, image.height, outline="", tags=("frame",))

        self.image = image
        self.bbxs = bbxs

        self.delete("corner")
        self.delete("bbox")
        self.delete("label")

        b = 0
        for box in self.bbxs:
            i = 0
            for corner in box:
                tag = "crn_" + str(b) + "x" + str(i)
                cx = corner[0]
                cy = corner[1]
                poly = self.create_polygon(self.cross, outline="blue", activeoutline="red",
                                           fill="gray", stipple='@transp.xbm', width=3,
                                           tags=("corner", tag))
                self.move(poly, cx, cy)
                self.scale(poly, 0, 0, self.zoom, self.zoom)
                i += 1
            self.__redraw_bbox(b)
            b += 1

        self.update_view()
        if self._on_bbox_updated is not None:
            self._on_bbox_updated(self.bbxs)

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
        tag = next(filter(lambda x: x.startswith('crn_'), self.gettags(self.corner_dragging_buffer["item"])))
        bc = tag.split("_")[1].split("x")
        b = int(bc[0])
        c = int(bc[1])

        # Update bbox coords
        self.bbxs[b][c][0] = (self.coords(self.corner_dragging_buffer["item"])[0] + 1) / self.zoom
        self.bbxs[b][c][1] = (self.coords(self.corner_dragging_buffer["item"])[1] + 1) / self.zoom
        self.__redraw_bbox(b)

        if self._on_bbox_updated is not None:
            self._on_bbox_updated(self.bbxs)

    def __redraw_bbox(self, b):
        # Redraw bbox

        midx = 0
        midy = 0
        bbox = []
        for i in range(4):
            t = self.find_withtag("crn_" + str(b) + "x" + str(i))
            coords = self.coords(t)
            bbox.append(coords[0] + 1)
            bbox.append(coords[1] + 1)
            midx += (coords[0] + 1)
            midy += (coords[1] + 1)

        midx /= 4
        midy /= 4

        bbx_tag = "bbx_" + str(b)
        self.delete(bbx_tag)
        self.create_polygon(bbox, outline="lightgreen", fill="", width=2, tags=("bbox", bbx_tag))

        lbl_tag = "lbl_" + str(b)
        self.delete(lbl_tag)
        self.create_text([midx, midy], fill="lightgreen", text=str(b), font=('Arial', 30), tags=("label", lbl_tag))

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
        self.imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
        imageid = self.create_image(max(canvas_bbx[0], pic_bbx[0]), max(canvas_bbx[1], pic_bbx[1]),
                                    anchor='nw', image=self.imagetk)
        self.lower(imageid)
