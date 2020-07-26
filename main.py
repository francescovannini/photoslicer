from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import *
from autoslicer import *
from slicingcanvas import *
import os


class MyFrame(Frame):

    def enable(self, state='!disabled'):

        def set_status(widget):
            if widget.winfo_children:
                for child in widget.winfo_children():
                    child_type = child.winfo_class()
                    if child_type not in ('Frame', 'Labelframe'):
                        child.state((state,))
                    set_status(child)

        set_status(self)

    def disable(self):
        self.enable('disabled')

class PhotoSlicer(MyFrame):

    def __init__(self, tk_parent=None):
        MyFrame.__init__(self, tk_parent)
        self.tk_parent = tk_parent

        self.winfo_toplevel().title("PhotoSlicer")
        self.source_images = []
        self.source_index = None

        # Grid layout
        Grid.rowconfigure(self.tk_parent, 0, weight=1)
        Grid.columnconfigure(self.tk_parent, 1, weight=1)

        menu = Menu(self.tk_parent)

        # File menu
        menu_file = Menu(menu, tearoff=0)
        menu_file.add_command(label="Open directory", command=self.open_directory)
        menu_file.add_separator()
        menu_file.add_command(label="Next image", command=self.next_image)
        menu_file.add_command(label="Previous image", command=self.prev_image)
        menu_file.add_command(label="Save locked slices", command=self.save_all)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.tk_parent.quit)
        menu.add_cascade(label="File", menu=menu_file)

        # Edit menu
        menu_operation = Menu(menu, tearoff=0)
        menu_operation.add_command(label="Abort", command=self.abort_processing)
        menu_operation.add_command(label="Disable", command=self.test_disable)
        menu_operation.add_command(label="Enable", command=self.test_enable)
        menu.add_cascade(label="Oper", menu=menu_operation)

        self.tk_parent.config(menu=menu)

        # Left side control panel
        self.frame_controls = Frame(self.tk_parent, borderwidth=5)
        self.frame_controls.grid(row=0, column=0, sticky="nsw")

        # Set defaults
        row = 0
        self.button_setdef = Button(self.frame_controls, text="Set defaults", command=self.set_default_parameters)
        self.button_setdef.grid(row=row, column=0, sticky="we")

        # Generate controls from parameters
        row += 1
        self.params = AutoslicerParams()
        for pi in self.params.__dict__:
            p = getattr(self.params, pi)
            Label(self.frame_controls, text=p.label).grid(row=row, column=0, sticky="w")
            row += 1
            p.control = Spinbox(self.frame_controls, from_=p.min, to=p.max, increment=p.step, textvariable=p.tk_var)
            p.control.grid(row=row, column=0, sticky="we")
            row += 1

        row += 1
        self.button_update = Button(self.frame_controls, text="Detect pictures", command=self.update_preview)
        self.button_update.grid(row=row, column=0, sticky="we")

        row += 1
        self.button_addbox = Button(self.frame_controls, text="Add manual bounding box", command=self.add_box)
        self.button_addbox.grid(row=row, column=0, sticky="we")

        self.status_text = StringVar(self.tk_parent)
        self.statuslabel = Label(self.tk_parent, textvariable=self.status_text, anchor='w',
                                 width=1, relief=SUNKEN).grid(row=1, column=0, columnspan=2, sticky='swe')

        self.status_text.set("Ready.")

        # Slicing canvas
        self.slicing_canvas = SlicingCanvas(self.tk_parent)
        self.slicing_canvas.grid(row=0, column=1, sticky='nswe')
        self.slicing_canvas.update()
        self.autoslicer = Autoslicer(self.params)

    def update_statusbar(self, text):
        self.status_text.set(text)
        self.tk_parent.update()

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

        self.disable()
        self.autoslicer.load_image(self.source_images[self.source_index])
        if self.autoslicer.image_loaded():
            self.update_preview()
            self.update_statusbar("Loaded " + self.source_images[self.source_index])
        self.enable()

    def update_preview(self):
        if not self.autoslicer.image_loaded():
            return

        self.disable()
        bbxs, image = self.autoslicer.autodetect_slices(self.update_statusbar)
        self.slicing_canvas.set_image(Image.fromarray(image))
        self.slicing_canvas.update_bboxes(bbxs)
        self.slicing_canvas.update_view()
        self.status_text.set("Ready.")
        self.enable()

    def save_all(self):

        if self.source_images is None or self.source_index < 0:
            messagebox.showwarning(title="No image loaded", message="Load an image first")
            return

        self.disable()

        i = -1
        for slice in self.slicing_canvas.slices:
            if not slice.locked:
                continue

            i += 1
            outname = self.source_images[self.source_index].replace(".png", "_" + f'{i:03}' + ".png", 1)
            self.autoslicer.save_slice(slice.bbox, outname)
            self.update_statusbar("Saved " + outname)

        if i < 0:
            messagebox.showwarning(title="No locked slice to save!",
                                   message="To lock one slice, click on its central number")
        else:
            i += 1
            messagebox.showinfo(title="Slices saved", message=f"{i} slices have been saved")

        self.enable()

    def not_implemented(self):
        messagebox.showwarning(title="Not implemented", message="Sorry, not there yet")
        return

    def abort_processing(self):
        self.autoslicer.abort_operation()

    def add_box(self):
        new_slice = PhotoSlice([[10, 10], [200, 10], [200, 200], [10, 200]])
        new_slice.toggle_locked()
        self.slicing_canvas.add_bbox(new_slice)

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

    def set_default_parameters(self):
        for pi in self.params.__dict__:
            p = getattr(self.params, pi)
            p.reset()
        self.tk_parent.update()
        return

    def test_disable(self):
        self.disable()

    def test_enable(self):
        self.enable()


root = Tk()
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))
app = PhotoSlicer(root)
if sys.argv[1:]:
    app.open_directory(sys.argv[1])
root.mainloop()
