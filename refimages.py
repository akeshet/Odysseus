#!/usr/bin/env python
"""Generate some images that can be used to test the fit routines

Some reference images without any noise are generated to assess if the result
when fitting the images is the same as the inputs used to generate the images.
Then noise can be added to images to see what noise we have to worry about.

"""

import os

import numpy as np
import scipy as sp
from scipy import optimize

import fitfuncs
from centerofmass import center_of_mass
from imageprocess import trans2od, od2trans
from polylog import fermi_poly3
#from .analysis.constants import *


def generate_image(dims=(576, 384), com=None, ODmax=3, fugacity=6, \
                   cloudradius=60):
    """Generate a single reference image"""

    xx, yy = np.mgrid[0:dims[0], 0:dims[1]]
    # center of mass coordinates
    if com==None:
        com = (dims[0]/2.07, dims[1]/2.03)
    rr = np.sqrt((xx-com[0])**2 + (yy-com[1])**2)

    odimg = fitfuncs.ideal_fermi_radial(rr, ODmax, fugacity, cloudradius)
    transimg = od2trans(odimg)

    return transimg


def stretch_img(img, factor):
    """Stretch image along the first axis by `factor`

    **Inputs**

      * img: 2D array, containing the image data
      * factor: float, has to be larger than 1.

    """

    xr = np.arange(img.shape[0])/factor
    for i in xrange(img.shape[1]-1):
        img[:, i] = np.interp(xr/factor, xr, img[:, i])

    return img


def add_noise(img, ampl=0.05, noisetype='random', fringeargs=None):
    """Noise is added to an image.

    **Inputs**

      * img: 2d array, containing image data
      * ampl: float, amplitude of the noise
      * noisetype: string, value can be one of

        * 'random', adds unbiased white noise
        * 'linear_x', adds a linear gradient along x from 0 to ampl
        * 'linear_y', adds a linear gradient along y from 0 to ampl
        * 'fringes', adds fringes with parameters fringeargs

      * fringeargs: sequence, containing four values

        * angle: float, angle of fringes in radians with respect to the x-axis
        * freq: float, frequency of the fringes in pixels^{-1}
        * pos: tuple, central position of the fringes with respect to the CoM
        * size: float, size of the Gaussian envelope of the fringes

    **Outputs**

      * img: 2d array, the input image with noise added to it

    """

    noisetypes = ['random', 'linear_x', 'linear_y', 'fringes']
    if not noisetype in noisetypes:
        raise ValueError, \
	      """noisetype is one of: %s"""%noisetypes

    if noisetype=='random':
        img = img + (np.random.random_sample(img.shape)-0.5)*ampl

    elif noisetype=='linear_x':
        noise = np.ones(img.shape).transpose()*np.arange(img.shape[0])\
              /img.shape[0]*ampl
        img = img + noise.transpose()

    elif noisetype=='linear_y':
        noise = np.ones(img.shape)*np.arange(img.shape[1])/img.shape[1]*ampl
        img = img + noise

    elif noisetype=='fringes':
        if not len(fringeargs)==4:
            print "fringeargs needs to contain four values: angle, freq, pos, size"
        angle, freq, pos, size = fringeargs
        xx, yy = np.mgrid[0:img.shape[0], 0:img.shape[1]]

        # center of mass coordinates
        odimg = trans2od(img)
        com = center_of_mass(odimg)
        xx0 = xx - com[0] - pos[0]
        yy0 = yy - com[1] - pos[1]
        yy0 = np.where(yy0==0, 1e-6, yy0)
        rr = np.sqrt(xx0**2 + yy0**2)

        # coordinate projection along fringe axis
        rangle = np.arctan(xx0.astype(float)/yy0)
        rangle = np.where(yy0>0, rangle, rangle + np.pi)
        rfringe = rr*np.cos(angle - rangle)

        noise = fitfuncs.gaussian(rr, ampl, size) * np.sin(2*np.pi*rfringe*freq)
        img = img + noise

    return img


def fugacity(ToverTF):
    """Calculate the log of the fugacity e^{\beta\mu}"""

    minpoly3 = lambda x, num: fermi_poly3(x) - num
    a = sp.optimize.brentq(minpoly3, -1e3, 1e3, args=(ToverTF**(-3)/6))

    return a


def cloudsize(ToverTF, N, tof, wr, wz):
    """Calculate the cloud size of an ideal Fermi gas

    **Inputs**

      * ToverTF: float, temperature in units of the Fermi temperature T_F
      * N: float, number of atoms
      * tof: float, time-of-flight in seconds
      * wr: float, radial trap frequency in Hz
      * wz: float, axial trap frequency in Hz

    **Outputs**

      * bprime: the size of the cloud in meters [1], (p.69, there called Ri)

    **References**

    [1] "Making, probing and understanding ultracold Fermi gases", W. Ketterle
         and M. Zwierlein, arXiv:cond-mat/0801.2500 (2008)

    """

    a = fugacity(ToverTF)
    fa = np.log(1+np.e**a)*(1+np.e**a)/np.e**a

    TF = hbar/kb*(6*N*wr**2*wz)**(1./3)
    T = TF*(6*fermi_poly3(a))**(-1./3)
    mass = 6*mp

    bprime = expansionfactor(tof, wr)*fa*np.sqrt(2*kb*T/(mass*wr**2))

    return bprime


def idealfermi_fitparams(ToverTF, N, tof=0, wr=2e3, wz=100, pixcal=10e-6):
    """Find the central OD, log(fugacity) and cloudsize for a Fermi cloud

    **Inputs**

      * ToverTF: float, temperature in units of the Fermi temperature T_F
      * N: float, number of atoms
      * tof: float, time-of-flight in seconds
      * wr: float, radial trap frequency in Hz
      * wz: float, axial trap frequency in Hz
      * pixcal: float, pixel size calibration in m/pix.

    **Outputs**

      * central_od: float, optical density in the center of the cloud
      * a: float, log(fugacity) = \mu\beta
      * bprime: cloud size in pixels

    """

    a = fugacity(ToverTF)
    bprime = cloudsize(ToverTF, N, tof, wr, wz)/pixcal

    def inverse_N_helper(central_od, a, bprime, N):
        """Function to help determine central OD with optimization routine."""

        fitparams = (central_od, a, bprime)
        ToverTF, NN = fitfuncs.ideal_fermi_numbers(fitparams, pixcal)

        return NN-N

    # use optimization function brentq to iteratively find centralOD from N
    central_od = sp.optimize.brentq(inverse_N_helper, 0, 1e3, args=(a, bprime, N))

    return central_od, a, bprime


def expansionfactor(tof, wr):
    """Expansion factor for ballistic time-of-flight expansion.

    Note that this assumes that during TOF there is no confining potential at
    all. In the case of a weaker (anti-)confining potential see Yong's
    note on this subject.

    **Inputs**

      * tof: float, time-of-flight in seconds
      * wr: float, trap frequency in Hz

    **Outputs**

      * expfactor: float, expansion factor of the cloud for given TOF and wr

    """

    expfactor = np.sqrt(1+wr**2*tof**2)

    return expfactor