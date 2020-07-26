from photoslicer import *

root = Tk()
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))
app = PhotoSlicer(root)
if sys.argv[1:]:
    app.open_directory(sys.argv[1])
root.mainloop()
