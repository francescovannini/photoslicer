from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *
from pixtractor import *
from slicingcanvas import *


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

        # Grid layout
        Grid.rowconfigure(self.parent, 0, weight=1)
        Grid.columnconfigure(self.parent, 1, weight=1)

        menu = Menu(self.parent)

        # File menu
        menu_file = Menu(menu, tearoff=0)
        menu_file.add_command(label="Open", command=self.open_file)
        menu_file.add_command(label="Save", command=self.not_implemented)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.parent.quit)
        menu.add_cascade(label="File", menu=menu_file)

        # Edit menu
        menu_edit = Menu(menu, tearoff=0)
        menu_edit.add_command(label="Cut", command=self.not_implemented)
        menu_edit.add_command(label="Copy", command=self.not_implemented)
        menu_edit.add_command(label="Paste", command=self.not_implemented)
        menu.add_cascade(label="Edit", menu=menu_edit)

        # Help menu
        menu_help = Menu(menu, tearoff=0)
        menu_help.add_command(label="About", command=self.not_implemented)
        menu.add_cascade(label="Help", menu=menu_help)

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
        self.parent.update()

    def load_image(self, image_path):
        self.pixtractor.load_image(image_path)
        if self.pixtractor.image_loaded():
            self.update_preview()

    def update_preview(self):
        if not self.pixtractor.image_loaded():
            return

        self.button_update["state"] = "disabled"
        bbxs, image = self.pixtractor.process_image(self.update_statusbar)
        self.slicing_canvas.set_view(Image.fromarray(image), bbxs)
        self.button_update["state"] = "normal"
        self.statuslabel_stringvar.set("Ready.")

    def not_implemented(self):
        return

    def open_file(self):
        selection = filedialog.askopenfilename(initialdir="~", title="Select file",
                                               filetypes=(("JPG", "*.jpg"),
                                                          ("PNG", "*.png"),
                                                          ("All files", "*.*")))

        if selection is not None and selection != "":
            self.load_image(selection)
