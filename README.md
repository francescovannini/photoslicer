# PhotoSlicer

So, one day your gradnma gives you a big box full of old family photos and you think it would be good to digitize them before they turn into a mush...

You have a A4 flatbed scanner, which is slow but of good quality. Given the amount of photos you immediately realize it would be unthinkable to scan one by one and let the scanner do the cropping.

You also noticed that a lot of those photos have an annoying boderd you would want to get rid of later. Some have stains, some others are discolored, some have missing corners or are irregularly cut. There are dozen of different formats...

So what do you do?

You obvisouldy scan as many photos as possible at once and worry about cropping them later.

And this repo is about what happened later:

![demo](assets/photoslicer.gif)

## Using OpenCV and Python to automatically crop old photos

Since I had never written a desktop app in Python before but I knew a bit of OpenCV, I decided to combine these two and write my own little tool.

And so, PhotoSlicer was born. As often happens, what was supposed to be a simple rudimentary tool to do one job, became sort of a fully fledged application that probably could be useful to other people with a similar problem.

Here the features:

* Scan recursively all PNGs from a directory
* Autodetect photos using OpenCV
* Multiple parameters to tune autodetection such as:
  * Black and White Threshold (simple, Gauss, Outso methods)
  * Ignore detected areas below a certain size (proportional to total scanned size)
  * Ignore detected areas which don't look like a rectangle
  * Tunable dilate filter
  * Flag to preview filter output (good to see how the autodetection filter "sees")
* UI interactions
  * Navigate through input PNGs or open directories
  * Click on a border to mark is as upper photo edge
  * Click and drag corners to adjust edges
  * Click on photo label to enable/disable export
  * Zoom in/out using mouse wheel
  * Click and drag to move viewport
  * Manually add bounding box when detection fails
* Automatic crop, straighten and perspective correction
* Automatic export to PNG

## Usage

From the root of this repo, just type

    pip3 install --upgrade pip
    pip3 install .

This should install photoslicer for your user in your path, so that you can then do

    photoslicer /media/disk/bunch_of_old_scans

## To do

A lot of refinements and bugfixes, but overall this thing got my job done very well. 

It's easy to add more detection parameters by just defining them into the AutoslicerParams class and the UI will automatically render them in the left panel. 

Something that would be nice to have is automatic orientation to detect which one is the upper corner. I did a quick attempt to detect human faces using OpenCV using a cascade classifier, but it worked only on few cases (and only when people were in the picture) so maybe a more generic approach using perhaps a CNN would be the best.

## License
[GPLv3](./LICENSE)
