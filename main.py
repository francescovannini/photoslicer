from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *
from pixtractor import *
from slicingcanvas import *


# https://stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan/48137257#48137257

class MainWindow:

    def __update_bbox_list(self, bboxes):
        self.bbox_list.delete(0, END)
        c = 0
        for i in bboxes:
            self.bbox_list.insert(END, str(c))
            c +=1

    def __init__(self, initial_image_path=None):

        # Vars
        self.root = Tk()
        self.root.geometry("800x600+50+50")
        self.image = None
        self.width = 0
        self.height = 0

        # Grid layout
        Grid.rowconfigure(self.root, 0, weight=1)
        Grid.columnconfigure(self.root, 1, weight=1)

        menu = Menu(self.root)

        # File menu
        menu_file = Menu(menu, tearoff=0)
        menu_file.add_command(label="Open", command=self.open_file)
        menu_file.add_command(label="Save", command=self.not_implemented)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.root.quit)
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

        self.root.config(menu=menu)

        # Left side control panel
        self.frame_controls = Frame(self.root, borderwidth=5)
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

        # Slicing canvas
        self.slicing_canvas = SlicingCanvas(self.root)
        self.slicing_canvas.grid(row=0, column=1, sticky='nswe')
        self.slicing_canvas.update()
        self.slicing_canvas.set_on_bbox_updated(self.__update_bbox_list)

        self.pixtractor = Pixtractor(params)
        if initial_image_path is not None:
            self.pixtractor.load_image(initial_image_path)

        if self.pixtractor.image_loaded():
            self.update_preview()

        self.root.mainloop()

    def update_preview(self):
        if not self.pixtractor.image_loaded():
            return

        self.button_update["state"] = "disabled"
        bbxs, image = self.pixtractor.get_bbxs()
        self.slicing_canvas.set_view(Image.fromarray(image), bbxs)
        self.button_update["state"] = "normal"

    def not_implemented(self):
        return

    def open_file(self):
        selection = filedialog.askopenfilename(initialdir="~", title="Select file",
                                               filetypes=(("JPG", "*.jpg"),
                                                          ("PNG", "*.png"),
                                                          ("All files", "*.*")))

        if selection is not None and selection != "":
            self.slicing_canvas.load_image(selection)
            self.pixtractor.load_image(selection)


app = MainWindow("img/scan_1537784960.png")
