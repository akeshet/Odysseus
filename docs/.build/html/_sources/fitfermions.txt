User interface
==============

One of the goals of the development of Odysseus is to create an easy to use software package that fits images in a fast, simple and robust way. To achieve this, there is a single module, :mod:`fitfermions`, that contains high-level functions that can be used from user scripts. Most of the heavy lifting is being done by the function :func:`fitfermions.fit_img`, which takes the path to a single image file, opens it, radially averages the transmission image, constructs the optical density profile, fits the column density for an ideal Fermi gas to it and finally extracts the number of atoms and temperature from the fit. Several example scripts are provided, they can be easily modified - with for example the names of the image files that are of interest - and run interactively. 

Example script
--------------

Simply copy this script into a new file, modify and run!

.. code-block:: python
   :linenos:
    
   import os
   from odysseus.fitfermions import fit_img, find_ellipticity
   from odysseus.imageprocess import *
   from odysseus.imageio import *

   ## import a single image ##
   dirname = '../../../archives/2008-09-11/'
   #dirname = 'c:\\Data\\2008-05-27'
   fname = 'raw9.11.2008 7;35;23 PM.TIF'
   img_name = os.path.join(dirname, fname)
   
   rawframes = import_raw_frames(img_name)
   transimg, odimg = calc_absorption_image(rawframes)
   # set the ROI
   transimg = transimg[120:350, 50:275]
   
   # find the ellipticity if the expansion is not spherically symmetric
   ellip = find_ellipticity(transimg)
   # do the fit
   ToverTF, N, ans = fit_img(transimg, elliptic=(ellip, 0))

The above script results in the determined temperature and number of atoms being printed in the console, as well as an image containing the radially averaged transmission image, optical density profile and a fit of that OD profile with the expected one for an ideal Fermi gas, as shown below.

.. image:: .images/example_fit.png
   :width: 400pt
   :target: _images/example_fit.png

The fitfermions module
-------------------------------

.. automodule:: odysseus.fitfermions  
   :members: fit_img, norm_and_guess, do_fit

Sanity checks
-------------

To make sure that fits make sense, a lot of tests can be done. There is a straightforward way to run many of these tests at once and generate a test report for an image. This comes in the form of a pdf file generated through LaTeX. In the simple example below an image is loaded, the region of interest (ROI) is set and a report generated.

.. code-block:: python
   :linenos:
   
   import os
   from odysseus.imageprocess import *
   from odysseus.imageio import *
   from odysseus import texreport

   dirname = '/home/ralf/data/archives/raw_frames/'
   tifname = 'raw9.11.2008 7;35;23 PM.TIF'
   imgname = os.path.join(dirname, tifname)

   rawframes = import_raw_frames(imgname)
   transimg, odimg = calc_absorption_image(rawframes)
   transimg = transimg[120:350, 50:275] # ROI
   texreport.generate_report(rawframes, transimg, imgname)

The transmission and raw images are shown, the azimuthally averaged image with the best fit is shown, the fit results (T, N) are given, the residuals are displayed, and the ellipticity is checked.