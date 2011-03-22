#!/usr/bin/env python
"""Collection of functions that can be used to fit images of cold atom clouds.

**References**

[1] "Making, probing and understanding ultracold Fermi gases", W. Ketterle and
M. Zwierlein, arXiv:cond-mat/0801.2500 (2008)

[2] "Making, probing and understanding Bose-Einstein condensates:, W. Ketterle,
D.S. Durfee and D.M. Stamper-Kurn, arXiv:cond-mat/9904034 (1999)

"""


import scipy as sp
import numpy as np
from scipy import integrate, optimize

from polylog import fermi_poly2, fermi_poly3


def ideal_fermi_radial(r, n0, q, r_cloud):
    """1D radial column density of an ideal Fermi gas

    The radial column density of an ideal Fermi gas around its center of mass.
    This is usually obtained by radially averaging an image of the atom cloud
    after time of flight from a trap with equal trap frequencies along both
    image axes.

    **Inputs**

      * r: 1D array containing the radial coordinate
      * n0: central optical density
      * q: logarithm of the fugacity, q = mu*beta
      * r_cloud: the radius of the atom cloud after expansion, in pixels.
                 for low temperatures T/T_F << 1, this is equal to the
                 Fermi radius times the expansion factor, for high T/T_F
                 to the thermal radius times the expansion factor.

    **Outputs**

      * coldensity: 1D array of the same length as r, containing the column
                    density for the ideal Fermi gas

    **References**

    [1] Ketterle and Zwierlein, p.69, eq.65

    """

    r_cloud = np.float(r_cloud)
    fq = np.log(1+np.exp(q)) * (1+np.exp(q))/np.exp(q)
    coldensity = n0*fermi_poly2(q-r**2/r_cloud**2*fq)/fermi_poly2(q)

    return coldensity


def ideal_fermi_numbers(fitparams, pixcal, sigma=None):
    """Determine T/T_F and N for an ideal Fermi gas.

    **Inputs**

      * fitparams: the result of fitting the image with ideal_fermi_radial
               fitparams is a list containing the central optical density,
               logarithm of the fugacity and thermal radius of the cloud in
               pixels
      * pixcal: calibration for the camera in meters per pixel

    **Outputs**

      * ToverTF: temperature of the Fermi gas T/T_F
      * N: number of atoms

    **Optional inputs**

      * sigma: photon absorption cross-section
           the default value is the resonant cross-section for 6Li

    """

    if sigma==None:
        sigma = 3*671e-9**2/(2*np.pi)
    mubeta = fitparams[1]
    ToverTF = (6*fermi_poly3(mubeta))**(-1./3)
    N = pixcal**2*sp.integrate.quad(n2D_radial, 0, np.infty,\
                                 args=(ideal_fermi_radial, fitparams))[0]/sigma

    return ToverTF, N


def gaussian_numbers(fitparams, pixcal, sigma=None):
    """Determine T/T_F and N for an ideal Fermi gas.

    **Inputs**

      * fitparams: list, the result of fitting the image with gaussian().
               fitparams is a list containing the central optical density,
               and thermal radius of the cloud in pixels
      * pixcal: calibration for the camera in meters per pixel

    **Outputs**

      * N: number of atoms

    **Optional inputs**

      * sigma: photon absorption cross-section
           the default value is the resonant cross-section for 6Li

    """

    if sigma==None:
        sigma = 3*671e-9**2/(2*np.pi)
    N = pixcal**2*sp.integrate.quad(n2D_radial, 0, np.infty,\
                                    args=(gaussian, fitparams))[0]/sigma

    return N


def fugacity_from_temp(ToverTF):
    """Finds the fugacity from the temperature by a minimization routine"""

    def best_fugacity(logfugacity):
        return abs(ToverTF - (6*fermi_poly3(logfugacity))**(-1./3))

    fugacity = sp.optimize.brent(best_fugacity, brack=(1e-5, 1e5), \
                                 full_output=0, tol=1e-5)

    return fugacity


def gaussian(r, n0, sigma):
    """1d radial column density of a gas with Gaussian profile

    **Inputs**

      * r: 1d array containing the radial coordinate
      * n0: float, central optical density
      * sigma: float, Gaussian width

    **Outputs**

      * coldensity: 1d array of the same length as r, containing the column density

    """

    coldensity = n0*np.exp(-r**2/sigma**2)

    return coldensity


def n2D_radial(r, oneDfunc, oneDparams):
    """2D density distribution used for determining the number of atoms.

    This is a convenience function that takes a 1D function that depends on
    radius, and multiplies it by 2*pi*r so it can be integrated over in 2D.

    **Inputs**

      * r: radial coordinate, this is the independent variable of oneDfunc
      * oneDfunc: function, the 1D function that depends only on r
      * oneDparams: sequence, a list or tuple containing the other input
                    parameters to oneDfunc

    **Outputs**

      * twoDfunc: oneDfunc times 2*pi*r

    """

    twoDfunc = 2*np.pi*r*oneDfunc(r, *oneDparams)

    return twoDfunc


def fit1dfunc(func, xdata, ydata, guess, weights=None, params=None, tol=1e-8):
    """Convenience function to fit 1d data

    Note that if the fitted data has no noise, the fit will sometimes return
    2 or 3 for success, but this usually still means that the fit was successful.

    **Inputs**

      * func: function, the 1D function that has only xdata as an independent
              variable
      * xdata: 1D array, the independent variable of func
      * ydata: 1D array, the independent variable of func we're fitting
      * guess: sequence, the initial guess for the fit parameters of func

    **Outputs**

      * ans: sequence, the final fitting parameters

    **Optional inputs**

      * weights: 1D array, the weights of the data points
      * params: sequence, containing the other input parameters to func
      * tol: relative tolerance of the fitting routine

    """

    # TODO: find a way to use params later, not implemented now
    if params is not None:
        raise NotImplementedError, "Passing params through is not yet supported"

    if not weights:
        weights = np.ones(xdata.shape)
    residuals = lambda p, rr, rrdata: (func(rr, *p) - rrdata) * weights
    ans, cov_x, infodict, mesg, success = sp.optimize.leastsq(residuals, guess,\
                    args=(xdata, ydata), ftol=tol, full_output=True)

    if success==1:
        # calculate the correlation matrix from the covariance matrix
        var = np.sqrt(np.array([np.diag(cov_x)]))
        scale = var*var.transpose()
        corr_matrix = cov_x/scale
        return ans
    else:
        print 'Fitting was unsuccessful:\n', success, mesg
        return ans