#!/usr/bin/env python
"""Center of mass algorithm based on Fourier transform and filtering"""

import numpy as np


def center_of_mass(img):
    """Find the center of mass of a focused spot on a noisy background.

    This is done by the Fourier transform method as discussed by Weisshaar et al.
    (http://www.mnd-umwelttechnik.fh-wiesbaden.de/pig/weisshaar_u5.pdf), which
    is insensitive to noise. This usually skews the result towards the center of
    the image for the classical CoM algorithm. A tuple with the CoM coordinates
    is returned.

    **Inputs**

      * img: 2D array, containing image data

    **Outputs**

      * com: tuple, containing the x,y coordinates of the center of mass

    """

    img = np.matrix(img)
    rbnd, cbnd = img.shape

    i = np.matrix(np.arange(0, rbnd))
    sin_a = np.sin((i-1)*2*np.pi / (rbnd-1))
    cos_a = np.cos((i-1)*2*np.pi / (rbnd-1))

    j = np.matrix(np.arange(0, cbnd)).transpose()
    sin_b = np.sin((j-1)*2*np.pi / (cbnd-1))
    cos_b = np.cos((j-1)*2*np.pi / (cbnd-1))

    a = (cos_a * img).sum()
    b = (sin_a * img).sum()
    c = (img * cos_b).sum()
    d = (img * sin_b).sum()

    if a>0:
        if b>0:
            rphi = 0
        else:
            rphi = 2*np.pi
    else:
        rphi = np.pi

    if c>0:
        if d>0:
            cphi = 0
        else:
            cphi = 2*np.pi
    else:
        cphi = np.pi

    x = (np.arctan(b/a) + rphi) * (rbnd - 1)/(2*np.pi) + 1
    y = (np.arctan(d/c) + cphi) * (cbnd - 1)/(2*np.pi) + 1
    com = (x, y)
    return com