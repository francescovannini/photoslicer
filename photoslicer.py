from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import *
from pixtractor import *
from slicingcanvas import *
import os


class PhotoSlicer(Frame):

    def __update_bbox_list(self, bboxes):
        self.bbox_list.delete(0, END)
        c = 0
        for i in bboxes:
            self.bbox_list.insert(END, str(c))
            c += 1

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.parent = parent
        self.winfo_toplevel().title("PhotoSlicer")
        self.source_images = []
        self.source_index = None

        # Grid layout
        Grid.rowconfigure(self.parent, 0, weight=1)
        Grid.columnconfigure(self.parent, 1, weight=1)

        menu = Menu(self.parent)

        # File menu
        menu_file = Menu(menu, tearoff=0)
        menu_file.add_command(label="Open directory", command=self.open_directory)
        menu_file.add_separator()
        menu_file.add_command(label="Next image", command=self.next_image)
        menu_file.add_command(label="Previous image", command=self.prev_image)
        menu_file.add_command(label="Save", command=self.not_implemented)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.parent.quit)
        menu.add_cascade(label="File", menu=menu_file)

        # Edit menu
        menu_operation = Menu(menu, tearoff=0)
        menu_operation.add_command(label="Abort", command=self.abort_processing)
        menu.add_cascade(label="Oper", menu=menu_operation)

        self.parent.config(menu=menu)

        # Left side control panel
        self.frame_controls = Frame(self.parent, borderwidth=5)
        self.frame_controls.grid(row=0, column=0, sticky="nsw")

        # Generate controls from parameters
        params = PixtractorParams()
        row = 0
        for pi in params.__dict__:
            p = getattr(params, pi)
            Label(self.frame_controls, text=p.label).grid(row=row, column=0, sticky="w")
            row += 1
            p.control = Spinbox(self.frame_controls, from_=p.min, to=p.max, increment=p.step,
                                textvariable=DoubleVar(value=p.value), command=p.update)

            p.control.grid(row=row, column=0, sticky="we")
            row += 1

        self.button_update = Button(self.frame_controls, text="Update", command=self.update_preview)
        self.button_update.grid(row=row, column=0, sticky="we")

        row += 1
        Separator(self.frame_controls, orient=HORIZONTAL).grid(row=row, column=0, sticky="we")

        # Bbox List
        row += 1
        self.frame_list = Frame(self.frame_controls, borderwidth=0)
        self.frame_list.grid(row=row, column=0, sticky="nwes")
        self.frame_list.columnconfigure(0, weight=1)
        scrollbar = Scrollbar(self.frame_list, orient=VERTICAL)
        scrollbar.grid(row=0, column=1, sticky="nsew")
        self.bbox_list = Listbox(self.frame_list, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.bbox_list.yview)
        self.bbox_list.grid(row=0, column=0, sticky="nswe")

        self.statuslabel_stringvar = StringVar(self.parent)
        self.statuslabel = Label(self.parent, textvariable=self.statuslabel_stringvar, anchor="w", relief=SUNKEN).grid(
            row=0, column=0, sticky='swe')
        self.statuslabel_stringvar.set("Ready.")

        # Slicing canvas
        self.slicing_canvas = SlicingCanvas(self.parent)
        self.slicing_canvas.grid(row=0, column=1, sticky='nswe')
        self.slicing_canvas.update()
        self.slicing_canvas.set_on_bbox_updated(self.__update_bbox_list)
        self.pixtractor = Pixtractor(params)

    def update_statusbar(self, text):
        self.statuslabel_stringvar.set(text)
        print(text)
        self.parent.update()

    def load_image(self, move_index=0):

        if len(self.source_images) == 0:
            self.open_directory()

        if self.source_index is None:
            self.source_index = 0
        else:
            self.source_index += move_index

            if self.source_index < 0:
                self.source_index = 0
                messagebox.showwarning(title="No previous", message="This is the first image")
                return

            if self.source_index >= len(self.source_images):
                self.source_index = len(self.source_images) - 1
                messagebox.showwarning(title="No next", message="This is the last image")
                return

        self.pixtractor.load_image(self.source_images[self.source_index])
        if self.pixtractor.image_loaded():
            self.update_preview()

    def update_preview(self):
        if not self.pixtractor.image_loaded():
            return

        self.button_update["state"] = "disabled"
        bbxs, image = self.pixtractor.process_image(self.update_statusbar)
        self.slicing_canvas.set_image(Image.fromarray(image))
        self.slicing_canvas.set_bboxes(bbxs)
        self.slicing_canvas.update_view()
        self.button_update["state"] = "normal"
        self.statuslabel_stringvar.set("Ready.")

    def not_implemented(self):
        return

    def abort_processing(self):
        self.pixtractor.abort_operation()

    def open_directory(self, basedir=None):
        if basedir is None:
            basedir = filedialog.askdirectory()

        if basedir is not None:
            for file in os.listdir(basedir):
                if file.endswith(".png"):
                    self.source_images.append(os.path.join(basedir, file))

        if len(self.source_images) == 0:
            messagebox.showwarning(title="No images", message="No images available")
        else:
            self.load_image(0)

    def next_image(self):
        self.load_image(1)

    def prev_image(self):
        self.load_image(-1)
