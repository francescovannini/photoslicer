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

if sys.argv[1:]:
    slicer.open_directory(sys.argv[1])

root.mainloop()
