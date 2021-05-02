import os
import sys
import ntpath
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import PIL
from PIL import Image
from PIL import ImageTk
from autoslicer import Autoslicer, AutoslicerParams
from slicingcanvas import SlicingCanvas, PhotoSlice


class DisableableFrame(tk.Frame):

    def enable(self, state='normal'):

        def set_status(widget):
            if widget.winfo_children:
                for child in widget.winfo_children():
                    child_type = child.winfo_class()
                    if child_type not in ('Frame', 'Labelframe'):
                        child['state'] = state
                    set_status(child)

        set_status(self)

    def disable(self):
        self.enable('disabled')


class PhotoSlicer(DisableableFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        self.winfo_toplevel().title("PhotoSlicer")
        self.source_images = []
        self.source_index = None

        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=1)

        # Left side control panel
        self.frame_controls = DisableableFrame(self, borderwidth=5)
        self.frame_controls.grid(row=0, column=0, sticky="nsw")

        # Open directory
        row = 0
        self.button_opendir = tk.Button(self.frame_controls, text="Open directory", command=self.open_directory)
        self.button_opendir.grid(row=row, column=0, sticky="we")

        # Prev/Next img
        row += 1
        self.button_previmg = tk.Button(self.frame_controls, text="Prev Img", command=self.prev_image)
        self.button_previmg.grid(row=row, column=0, sticky="w")
        self.button_nextimg = tk.Button(self.frame_controls, text="Next Img", command=self.next_image)
        self.button_nextimg.grid(row=row, column=0, sticky="e")

        # Save images
        row += 1
        self.button_saveimgs = tk.Button(self.frame_controls, text="Save images", command=self.save_all)
        self.button_saveimgs.grid(row=row, column=0, sticky="we")

        # Generate controls from parameters
        row += 1
        self.params = AutoslicerParams()
        for pi in self.params.__dict__:
            p = getattr(self.params, pi)
            tk.Label(self.frame_controls, text=p.label).grid(row=row, column=0, sticky="w")
            row += 1
            p.control = tk.Spinbox(self.frame_controls, from_=p.min, to=p.max, increment=p.step, textvariable=p.tk_var)
            p.control.grid(row=row, column=0, sticky="we")
            row += 1

        # Set defaults
        row += 1
        self.button_setdef = tk.Button(self.frame_controls, text="Set defaults", command=self.set_default_parameters)
        self.button_setdef.grid(row=row, column=0, sticky="we")

        row += 1
        self.button_update = tk.Button(self.frame_controls, text="Detect pictures", command=self.update_preview)
        self.button_update.grid(row=row, column=0, sticky="we")

        row += 1
        self.button_addbox = tk.Button(self.frame_controls, text="Add manual bounding box", command=self.add_box)
        self.button_addbox.grid(row=row, column=0, sticky="we")

        self.status_text = tk.StringVar(self)
        self.statuslabel = tk.Label(self, textvariable=self.status_text, anchor='w',
                                    width=1, relief=tk.SUNKEN).grid(row=1, column=0, columnspan=2, sticky='swe')

        self.status_text.set("Ready.")

        # Slicing canvas
        self.slicing_canvas = SlicingCanvas(self)
        self.slicing_canvas.grid(row=0, column=1, sticky='nswe')
        self.slicing_canvas.update()
        self.autoslicer = Autoslicer(self.params)

    def update_statusbar(self, text):
        self.status_text.set(text)
        self.update()

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
            self.update_preview(new_image=True)
            self.update_statusbar("Loaded " + self.source_images[self.source_index])
        self.enable()

    def update_preview(self, new_image=False):
        if not self.autoslicer.image_loaded():
            return

        self.disable()
        bbxs, image = self.autoslicer.autodetect_slices(self.update_statusbar)
        self.slicing_canvas.set_image(Image.fromarray(image), new_image)
        self.slicing_canvas.update_bboxes(bbxs)
        self.slicing_canvas.update_view()
        self.update_statusbar("Ready.")
        self.enable()

    def save_all(self):

        if self.source_images is None or self.source_index < 0:
            messagebox.showwarning(title="No image loaded", message="Load an image first")
            return

        basedir = filedialog.askdirectory(title="Select destination directory")
        if basedir is None or len(basedir) == 0:
            return

        self.disable()

        total_saved = 0
        for i, slice in enumerate(self.slicing_canvas.slices):
            if not slice.locked:
                continue

            basename = ntpath.basename(self.source_images[self.source_index])
            basename = os.path.splitext(basename)[0] + '_' + f'{i:03}' + '.png'

            outname = basedir + os.path.sep + basename
            self.autoslicer.save_slice(slice.bbox, outname)
            self.update_statusbar("Saved " + outname)
            total_saved += 1

        if total_saved == 0:
            messagebox.showwarning(title="No locked slice to save!",
                                   message="To lock one slice, click on its central number")
        else:
            messagebox.showinfo(title="Slices saved", message=f"{total_saved} slices have been saved")

        self.enable()

    def not_implemented(self):
        messagebox.showwarning(title="Not implemented", message="Sorry, not there yet")
        return

    def abort_processing(self):
        self.autoslicer.abort_operation()

    def add_box(self):
        new_slice = PhotoSlice(None)
        new_slice.toggle_locked()
        self.slicing_canvas.add_bbox(new_slice)

    def open_directory(self, basedir=None):
        if basedir is None:
            basedir = filedialog.askdirectory()

        extensions = ['png', 'jpg', 'jpeg']
        if basedir is not None:
            for file in os.listdir(basedir):
                for e in extensions:
                    if file.lower().endswith("." + e):
                        self.source_images.append(os.path.join(basedir, file))
                        break

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
        self.update()
        return

    def test_disable(self):
        self.disable()

    def test_enable(self):
        self.enable()


def main():
    # Main window
    root = tk.Tk()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("%dx%d+0+0" % (w, h))

    # All area to the main slicer frame
    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 0, weight=1)

    # Main frame
    slicer = PhotoSlicer(root)
    slicer.grid(row=0, column=0, sticky="nswe")

    if sys.argv[1:]:
        slicer.open_directory(sys.argv[1])

    root.mainloop()


if __name__ == "__main__":
    main()
