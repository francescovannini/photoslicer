from tkinter import *
from PIL import Image, ImageTk


class SlicingCanvas(Canvas):
    def __init__(self, parent, **kwargs):
        Canvas.__init__(self, parent, **kwargs)
        self.zoom = 1.0
        self.delta = 1.3
        self.image_container = None
        self.image = None
        self.imagetk = None
        self.width = 0
        self.height = 0

        # Events
        self.bind('<Configure>', self.update_view)
        self.bind('<ButtonPress-1>', self.drag_from)
        self.bind('<B1-Motion>', self.drag_to)
        self.bind('<MouseWheel>', self.mouse_wheel)
        self.bind('<Button-5>', self.mouse_wheel)
        self.bind('<Button-4>', self.mouse_wheel)

    def drag_from(self, event):
        self.scan_mark(event.x, event.y)

    def drag_to(self, event):
        self.scan_dragto(event.x, event.y, gain=1)
        self.update_view()  # redraw the image

    def mouse_wheel(self, event):
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)

        bbox = self.bbox(self.image_container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            pass  # Ok! Inside the image
        else:
            return  # zoom only inside image area

        scale = 1.0

        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down
            i = min(self.width, self.height)
            if int(i * self.zoom) < 300:
                return  # image is less than 30 pixels
            self.zoom /= self.delta
            scale /= self.delta

        if event.num == 4 or event.delta == 120:  # scroll up
            i = min(self.winfo_width(), self.winfo_height())
            if i < self.zoom:
                return  # 1 pixel is bigger than the visible area
            self.zoom *= self.delta
            scale *= self.delta

        self.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.update_view()

    def set_image(self, image):
        self.image = image
        self.width, self.height = self.image.size

        # Put image into container rectangle and use it to set proper coordinates to the image
        self.image_container = self.create_rectangle(0, 0, self.width, self.height, width=0)
        self.update_view()

    def update_view(self, event=None):

        if self.image_container is None:
            return

        bbox1 = self.bbox(self.image_container)  # get image area

        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvasx(0),  # get visible area of the canvas
                 self.canvasy(0),
                 self.canvasx(self.winfo_width()),
                 self.canvasy(self.winfo_height()))

        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]

        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]

        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]

        self.configure(scrollregion=bbox)  # set scroll region
        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]

        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.zoom), self.width)  # sometimes it is larger on 1 pixel...
            y = min(int(y2 / self.zoom), self.height)  # ...and sometimes not
            image = self.image.crop((int(x1 / self.zoom), int(y1 / self.zoom), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),
                                        anchor='nw', image=imagetk)
            self.lower(imageid)  # set image into background
            self.imagetk = imagetk  # keep an extra reference to prevent garbage-collection
