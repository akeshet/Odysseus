Theory
======

The fitting procedure to extract the temperature from only the shape of the cloud seems to be most sensitive for temperatures between T/T_F = 0.05 and T/T_F = 0.4. For higher T/T_F the cloud starts to resemble a Gaussian and for lower T/T_F the differences become small because a smaller fraction of the atoms contributes to deviations in shape. In the figure below we can see the relative changes in shape for curves with different T/T_F fitted to the same image.

.. image:: .images/fit_several_temperatures.png
   :width: 500pt
   :target: _images/fit_several_temperatures.png


Temperature fitting - dos and don'ts
------------------------------------

There are some things to keep in mind when you want a reliable temperature fit. First of all, it is very important that the image is as clean as possible (few fringes). This can be achieved by cleaning optical surfaces, by aperturing the imaging beam to limit backreflections, by angling optical surfaces, and by using a short optical path length after the imaging fiber.

Other things that can be done are:

- use a ROI with size at least two or three times the cloud size (otherwise we get normalization errors, or cut off significant parts of the data)
- for a ROI, stay away from regions with no light and image edge by at least 10 pixels
- use images with a central OD between ~ 0.6 and 1.6
- results are not sensitive to TOF or cutoff OD when the above is done (check!)