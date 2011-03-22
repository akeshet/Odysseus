.. _section-gui:

The Graphical User Interface
============================

The graphical user interface (GUI) has two uses. One is to view images and get live feedback from fitting them when running an experiment. The other is to apply standard data analysis functions to single images without having to write analysis scripts. This section will describe the elements of the GUI in detail.

Overview
--------

Here is an image of the GUI with images loaded, regions of interest and cursor displayed, and a temperature fit to the last image. The GUI is basically divided into three areas - central image view, image history and info panel. The GUI elements are discussed in later subsections.

.. image:: .images/odysseusgui.png
   :width: 500pt
   :target: _images/odysseusgui.png

Image types
-----------

Several image formats can be used for import and export. The main type, used by both Winview and XCamera, is TIFF. This is a very common bitmap format for scientific images. Unfortunately the 16-bit version is broken in both Python and C#, therefore it is recommended to use 32-bit files. XCamera outputs 24-bit color files with a special structure that can be decoded by Odysseus. For more details see the documentation in the `imageio` module.

In addition to TIFF Odysseus can import .xraw files, which are basically ascii files, and hdf5. There is ascii, npy (binary Numpy format) and hdf5 export available, and the images in the central image view can be saved as png, jpg, etc. For best interoperability one should use the hdf5 format, as it is the most commonly used standard scientific data format and can be read by Matlab, Mathematica, and most other program a scientist cares about.

Data path
---------

This path is the one that is monitored by Odysseus for new files. If new files are detected they will be opened and the most recent one loaded into the central image view. Note that if the directory contains many Gb of image files the monitoring will get slower and start eating up more CPU time. It is therefore best to back up image files after a while and move them out of the monitored directory.

Central image view
------------------

The central image view contains an absorption image and all the raw frames used to calculate that absorption image. Typically these are 'probe with atoms', 'probe without atoms' and 'dark field'. These can be viewed by clicking the + button on the top right corner of the view. 

There are two regions of interest (ROIs), *Analysis* and *Ncount* that can be set by the respective control boxes on the right side of the GUI. The *Analysis* ROI is used for fitting data and passing data to plugins, the *Ncount* ROI for getting an estimate of the total number of atoms in the image. This *ncount* number is shown below each image in the image history. Setting the ROI coordinates can be done by typing numbers in the spin boxes, or alternatively by right-clicking on the spin box labels. In the latter case the spin boxes will take the coordinate values of the cursor.

Right-clicking on the image will display the cursor at the point of the click. It can be moved around with the arrow keys. The coordinates and the image value are displayed in the light blue label above the image view. Right-clicking on that label will make the cursor disappear again.

At the bottom of the image view a row of buttons gives access to zoom levels and image saving. After activating the zoom functionality by clicking the button with the loupe, the image can be zoomed by left-dragging with the mouse. The arrow buttons and home button can be used to navigate back and forth through different zoom levels.

Image history
-------------

The row of images at the bottom of the GUI display the eight most recent images. Hovering the mouse over an image displays its file name in a tooltip. Left-clicking on an image loads it into the central image view, and right-clicking displays a list of plugins that can be invoked on the image.

Fitting
-------

A large part of the Current Image Info panel on the right of the GUI is used for controlling and displaying fits of the image data. Selecting *Autofit* automatically fits each loaded image with the selected function. If *Calc ellipticity* is selected, the radial average that most fit functions perform takes into account that the image is stretched along the vertical axis. Select this option if you know your image is not radially symmetric, for example due to an inhomogeneous magnetic field that affects the cloud shape in time-of-flight.

Plugins
-------

When right-clicking on an image in the history, a list of plugins is displayed. These plugins are a convenient way for users to add functionality without having to dig into the Odysseus source code. A simple format, documented in :ref:`writing plugins <writing-plugins>`, allows one to write plain Python code assuming there is image data available under the variable *img*. It can plot results in a pop-up window which the plugin system takes care of. 

Useful plugins that are already available are, among others,:
* Line profile
* Radial average
* Fourier transform