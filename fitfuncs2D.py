import numpy as np
import scipy as sp
from scipy import integrate, optimize
import matplotlib.pyplot as plt

from polylog import fermi_poly2, fermi_poly3

#from cython_fermipoly import fermi_poly2 as fp2cython
#from cython_fermipoly import fermi_poly2_complete as fp2cython

def idealfermi_2D(p, xx, yy):
    """The 2D distribution when imaging an ideal Fermi gas, can be elliptical.

    Note that the actual 2-D arrays need to be flattened to 1-D for a fit to
    work.

    **Inputs**

      p : array_like
          peters, an array of floats with the following elements:
          * p[0] cloud center x
          * p[1] cloud center y
          * p[2] TF width x
          * p[3] TF width y
          * p[4] peak OD
          * p[5] log fugacity
          * p[6] background offset
          * p[7] x slope
          * p[8] Y slope
      xx : ndarray
          The indices along the x-axis of the image.
      yy : ndarray
          The indices along the y-axis of the image.

    **Outputs**

      coldensity : ndarray
          The result of evaluating the 2D distribution.
    """

    fq = np.log(1 + np.exp(p[5])) * (1 + np.exp(p[5])) / np.exp(p[5])

    coldensity = p[4] * fermi_poly2(p[5] - ((xx-p[0])**2/p[2]**2 +
                                            (yy-p[1])**2/p[3]**2) * fq) \
               / fermi_poly2(p[5]) + p[6] + p[7] * xx + p[8] * yy

    return coldensity


def idealfermi_2D_angled(p, xx, yy):
    """The 2D distribution when imaging an ideal Fermi gas, can be elliptical.

    Similar to `idealfermi_2D` but including a rotation angle. This angle
    specifies how the cloud is rotated with respect to the image axis.
    This does make the fit slower.
    Note that the actual 2-D arrays need to be flattened to 1-D for a fit to
    work.

    **Inputs**

      p : array_like
          peters, an array of floats with the following elements:
          * p[0] cloud center x
          * p[1] cloud center y
          * p[2] TF width x
          * p[3] TF width y
          * p[4] peak OD
          * p[5] log fugacity
          * p[6] background offset
          * p[7] x slope
          * p[8] Y slope
          * p[9] rotation angle in rad of cloud with respect to the image axis
      xx : ndarray
          The indices along the x-axis of the image.
      yy : ndarray
          The indices along the y-axis of the image.

    **Outputs**

      coldensity : ndarray
          The result of evaluating the 2D distribution.
    """
    print 'called'
    # do the coordinate rotation
    rr = (xx - p[0]) * np.cos(p[9]) - (yy - p[1]) * np.sin(p[9])
    ss = (xx - p[0]) * np.sin(p[9]) + (yy - p[1]) * np.cos(p[9])

    fq = np.log(1 + np.exp(p[5])) * (1 + np.exp(p[5])) / np.exp(p[5])

    coldensity = p[4] * fermi_poly2(p[5] - (rr**2 / p[2]**2 +
                                            ss**2 / p[3]**2) * fq) \
               / fermi_poly2(p[5]) + p[6] + p[7] * xx + p[8] * yy

    #coldensity = p[4] * fp2cython(p[5] - (rr**2 / p[2]**2 +
                                            #ss**2 / p[3]**2) * fq) \
               #/ fermi_poly2(p[5]) + p[6] + p[7] * xx + p[8] * yy

    #coldensity = p[4] * fp2cython(p[5] - (rr**2 / p[2]**2 +
                                            #ss**2 / p[3]**2) * fq) \
               #/ fp2cython(np.array([p[5]])) + p[6] + p[7] * xx + p[8] * yy
    return coldensity


def ideal_fermi_numbers_2D(fitparams, pixcal, sigma=None):
    """Determine T/T_F and N for an ideal Fermi gas.

    **Inputs**

      * fitparams: array_like
               An array containing the central optical density,
               logarithm of the fugacity and thermal radius of the cloud in
               pixels.
      * pixcal: float,
               Calibration for the camera in meters per pixel.

    **Outputs**

      * ToverTF: temperature of the Fermi gas T/T_F
      * N: number of atoms

    **Optional inputs**

      * sigma: photon absorption cross-section
           The default value is the resonant cross-section for 6Li.

    """

    if sigma==None:
        sigma = 3*671e-9**2/(2*np.pi)
    mubeta = fitparams[5]
    ToverTF = (6*fermi_poly3(mubeta))**(-1./3)

    x, y, sx, sy = fitparams[0:4]
    sx=max(sx,5)
    sy=max(sy,5)
    [X, Y] = np.mgrid[x-5*sx:x+5*sx, y-5*sy:y+5*sy]
    odimg_fitted = idealfermi_2D(fitparams, X, Y)
    N = odimg_fitted.sum() * pixcal**2 / sigma

    return ToverTF, N

def ideal_fermi_numbers_2D_angled(fitparams, pixcal, sigma=None):
    """Determine T/T_F and N for an ideal Fermi gas.

    **Inputs**

      * fitparams: array_like
               An array containing the central optical density,
               logarithm of the fugacity and thermal radius of the cloud in
               pixels.
      * pixcal: float,
               Calibration for the camera in meters per pixel.

    **Outputs**

      * ToverTF: temperature of the Fermi gas T/T_F
      * N: number of atoms

    **Optional inputs**

      * sigma: photon absorption cross-section
           The default value is the resonant cross-section for 6Li.

    """

    if sigma==None:
        sigma = 3*671e-9**2/(2*np.pi)
    mubeta = fitparams[5]
    ToverTF = (6*fermi_poly3(mubeta))**(-1./3)

    x, y, sx, sy = fitparams[0:4]
    sx=max(sx,5)
    sy=max(sy,5)
    [X, Y] = np.mgrid[x-5*sx:x+5*sx, y-5*sy:y+5*sy]
    newparams=[fitparams[0],fitparams[1],fitparams[2],fitparams[3],fitparams[4],fitparams[5],0.,0.,0.]
    odimg_fitted = idealfermi_2D(newparams, X, Y)
    N = odimg_fitted.sum() * pixcal**2 / sigma

    return ToverTF, N

def fit2dfunc(func, data, guess, ind_scale=1., params=None, tol=1e-8):
    """Convenience function to fit 2-D data.

    Note that if the fitted data has no noise (i.e. it was simulated data),
    the fit will sometimes return 2 or 3 for success, but this usually
    still means that the fit was successful.

    **Inputs**

      * func: function, the 1-D function that has only xdata as an independent
              variable
      * data: 2-D array, the data to fit with `func`.
      * guess: sequence, the initial guess for the fit parameters of `func`.

    **Outputs**

      * ans: sequence, the final fitting parameters

    **Optional inputs**

      * ind_scale: float, the factor by which to scale the indices of `data`
                   to obtain the independent values for the fit.
      * params: sequence, containing the other input parameters to func
      * tol: relative tolerance of the fitting routine

    """

    # TODO: find a way to use params later, not implemented now
    if params is not None:
        raise NotImplementedError, "Passing params through is not yet supported"

    # flatten to 1-D arrays
    xsize, ysize = data.shape
    [X, Y] = np.mgrid[0:xsize, 0:ysize]
    X = X.ravel() * ind_scale
    Y = Y.ravel() * ind_scale
    data = data.ravel()

    residuals = lambda p: (func(p, X, Y) - data)
    ans, cov_x, infodict, mesg, success = sp.optimize.leastsq(residuals,
                                                              guess,
                                                              ftol=tol,
                                                              full_output=True)

    if success==1:
        return ans
    else:
        print 'Fitting was unsuccessful:\n', success, mesg
        return ans

def fit2dfuncraw(func, pwa, pwoa, df, guess, ind_scale=1., params=None, tol=1e-8):
    """Convenience function to fit 2-D data.

    Note that if the fitted data has no noise (i.e. it was simulated data),
    the fit will sometimes return 2 or 3 for success, but this usually
    still means that the fit was successful.

    **Inputs**

      * func: function, the 1-D function that has only xdata as an independent
              variable
      * data: 2-D array, the data to fit with `func`.
      * guess: sequence, the initial guess for the fit parameters of `func`.

    **Outputs**

      * ans: sequence, the final fitting parameters

    **Optional inputs**

      * ind_scale: float, the factor by which to scale the indices of `data`
                   to obtain the independent values for the fit.
      * params: sequence, containing the other input parameters to func
      * tol: relative tolerance of the fitting routine

    """

    # TODO: find a way to use params later, not implemented now
    if params is not None:
        raise NotImplementedError, "Passing params through is not yet supported"

    # flatten to 1-D arrays
    xsize, ysize = pwa.shape
    [X, Y] = np.mgrid[0:xsize, 0:ysize]
    X = X.ravel() * ind_scale
    Y = Y.ravel() * ind_scale
    pwa = pwa.ravel()
    pwoa = pwoa.ravel()
    df = df.ravel()

    residuals = lambda p: ((np.exp(-1*func(p, X, Y)) * (pwoa-df)) + df - pwa)
    ans, cov_x, infodict, mesg, success = sp.optimize.leastsq(residuals,
                                                              guess,
                                                              ftol=tol,
                                                              full_output=True)
                           
    if success==1:
        return ans
    else:
        print 'Fitting was unsuccessful:\n', success, mesg
        return ans
def gaussian_moments_2D(data):
    """Return the gaussian parameters of a 2D distribution

    This is done by calculating the moments of the distribution.

    **Inputs**

      data : 2-D array, the image data.

    **Outputs**

      out : tuple, the first two moments along each image axis, in the form
          (x, y, width_x, width_y).

    """

    total = data.sum()
    X, Y = np.indices(data.shape)
    x = (X * data).sum() / total
    y = (Y * data).sum() / total
    col = data[:, int(y)]
    width_x = np.sqrt(np.abs((np.arange(col.size) - y)**2 * col).sum() \
                      / col.sum())
    row = data[int(x), :]
    width_y = np.sqrt(np.abs((np.arange(row.size) - x)**2 * row).sum() \
                      / row.sum())

    return (x, y, width_x, width_y)


def residuals_2D(data, fitparams, func=idealfermi_2D, smooth=None, showfig=False):
    """Return a 2-D array of the same shape as `data` with the fit residuals.

    **Inputs**

      data : 2-D array, the data.
      fitparams : 1-D array, containing the fit parameters for the 2-D ideal
                  Fermi gas distribution.
      smooth : float, if given the residuals are smoothed with a Gaussian
               kernel with ``sigma = smooth``.
      showfig : bool, if True a figure of the residuals is shown.

    **Outputs**

      residuals : 2-D array, the fit residuals.

    """

    xsize, ysize = data.shape
    [X, Y] = np.mgrid[0:xsize, 0:ysize]
    fitted_data = func(fitparams, X, Y)
    residuals = (data - fitted_data) / fitparams[4] # in percentage of max OD

    if smooth:
        residuals = sp.ndimage.gaussian_filter(residuals, smooth)
    if showfig:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        im = ax.imshow(residuals)
        cb = fig.colorbar(im)
        cb.set_label(r'fraction of max(OD)')
        ax.set_title(r'Fit residuals')
        plt.show()

    return residuals
