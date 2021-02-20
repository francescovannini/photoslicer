import sys
import tkinter as tk
from photoslicer import PhotoSlicer

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

# Main menu
menu = tk.Menu(root)

# File menu
menu_file = tk.Menu(menu, tearoff=0)
menu_file.add_command(label="Open directory", command=slicer.open_directory)
menu_file.add_separator()
menu_file.add_command(label="Next image", command=slicer.next_image)
menu_file.add_command(label="Previous image", command=slicer.prev_image)
menu_file.add_command(label="Save locked slices", command=slicer.save_all)
menu_file.add_separator()
menu_file.add_command(label="Exit", command=root.quit)
menu.add_cascade(label="File", menu=menu_file)

# Edit menu
menu_operation = tk.Menu(menu, tearoff=0)
menu_operation.add_command(label="Abort", command=slicer.abort_processing)
menu_operation.add_command(label="Disable", command=slicer.test_disable)
menu_operation.add_command(label="Enable", command=slicer.test_enable)
menu.add_cascade(label="Job", menu=menu_operation)
root.config(menu=menu)

if sys.argv[1:]:
    slicer.open_directory(sys.argv[1])

root.mainloop()
