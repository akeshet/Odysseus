#!/usr/bin/env python
"""A high level interface to the temperature fit routines for fermions.

The easiest to use function is fit_img(). When a single transmission image
is passed in to this function, the fit should just work. Normalization
is automatically taken care of. It is assumed that the atom cloud is
azimuthally symmetric around its center of mass. If this is not the case,
find_ellipticity() should be used to find the aspect ratio of the cloud first.

"""

import numpy as np
import scipy as sp
from scipy import optimize

from centerofmass import center_of_mass
import imageio
from imageprocess import *
from visualize import *
from fitfuncs import *


def average_images(imgs, roi=None):
    """Import one or more images and average them.

    **Inputs**

      * imgs: str or list, containing the paths to image files to be averaged.
              a single image is not averaged but simply opened.
      * roi: sequence of two slices, defining the region of interest.

    **Outputs**

      * od_avg: 2D array, containing the averaged OD image.
      * trans_avg: 2D array, containing the averaged transmission image.

    """

    odlist = []
    translist = []

    if isinstance(imgs, str):
        imgs = [imgs]

    try:
        imgs.remove(None)
    except ValueError:
        pass

    for img in imgs:
        img_array = imageio.imgimport_intelligent(img)
        transimg, odimg = calc_absimage(img_array)
        if roi:
            transimg = transimg[roi]
        odimg = trans2od(transimg)

        odlist.append(odimg)
        translist.append(transimg)

    od_avg = np.mean(np.array(odlist), axis=0)
    trans_avg = np.mean(np.array(translist), axis=0)

    return od_avg, trans_avg


def norm_and_guess(transimg, norm=True):
    """Normalize the transmission image and find initial fitting parameters"""

    odimg = trans2od(transimg)
    # determine CoM to use as parameter in fitting of n2D_radial to odimg
    com = center_of_mass(odimg)

    # guess initial fit parameters
    n0 = odimg[com[0]-5:com[0]+5, com[1]-5:com[1]+5].sum()*1e-2 # av. central OD
    a = 4 # log(fugacity)

    # approximate cloud size, with minimum 10 pixels in case this does not work
    # use something better, like moment estimation!
    # for elliptical clouds this is way off, and for low OD it fails!
    bprime = 0.5*(threshold_image(odimg.mean(axis=1), thres=0.1*n0, below=False)).sum()
    bprime = max(bprime, 10)

    # normalize the background
    if norm:
        try:
            transimg = normalize_img(transimg, com, bprime)
        except NotImplementedError:
            print "Couldn't normalize the image"

    # this maxod is specific to each experiment and needs to be checked
    odimg = trans2od(transimg, maxod=3)
    com = center_of_mass(odimg)

    return transimg, odimg, com, n0, a, bprime


def find_ellipticity(transimg, normalize=True, tol=2e-3):
    """Determines the ellipticity of an atom cloud

    The ellipticity is found by an optimization routine. A value is tried
    and the sum of residuals between the radial line profiles and the averaged
    result is computed. This value is then minimized. This method is accurate
    but slow. An alternative option is to use the second moments of the image.

    **Inputs**

      * transimg: 2D array, containing the absorption image
      * normalize: bool, if True transimg is normalized with norm_and_guess(),
                   otherwise the odimg is obtained directly from transimg.
      * tol: float, the required tolerance

    **Outputs**

      * ellip: float, the ellipticity of the atom cloud

    """

    if normalize:
        transimg, odimg, com, n0, a, bprime = norm_and_guess(transimg)
    else:
        odimg = trans2od(transimg)
        com = center_of_mass(odimg)

    def ellipticity(ell):
        rcoord, rad_profile, rprofiles, angles = radial_interpolate(odimg, com,\
                                    0.3, elliptic=(ell, 0), full_output=True)

        od_cutoff = find_fitrange(rad_profile)
        av_err = radialprofile_errors(rprofiles, angles, rad_profile, \
                                        od_cutoff, showfig=False, report=False)

        return av_err

    ellip = sp.optimize.fminbound(ellipticity, 0.6, 1.0, full_output=0, \
                                  xtol=tol)
    print 'ellipticity = %1.3f'%ellip

    return ellip


def do_fit(rcoord, od_prof, od_cutoff, guess, pixcal, fitfunc='idealfermi', T=None):
    """Fits an absorption image with an ideal Fermi gas profile

    **Inputs**

      * rcoord: 1D array containing the radial coordinate
      * od_prof: 1D array containing the radially averaged OD profile
      * od_cutoff: int, the index of rcoord from where the fit has to be
                   performed.
      * guess: tuple, initial fit parameters, the three elements are n0, a,
        bprime
      * pixcal: float, pixel size calibration in m/pix.

    **Outputs**

      * ToverTF: float, the temperature of the Fermi gas in units of T_F
      * N: float, the number of atoms of the Fermi gas
      * ans: tuple, containing the fit result

    **Optional inputs**

      * fitfunc: string, name of the fit function to be used. Valid choices are
        idealfermi, gaussian, idealfermi_fixedT
      * T: float, the temperature for idealfermi_fixedT

    """

    def fit_idealfermi():
        ans = fit1dfunc(ideal_fermi_radial, rcoord[od_cutoff:], \
                        od_prof[od_cutoff:], guess)#, \
                        #weights=np.sqrt(rcoord[od_cutoff:]))
        # compute temperature and number of atoms and print result
        ToverTF, N = ideal_fermi_numbers(ans, pixcal)
        print 'T/T_F = %1.5f'%(ToverTF[0])
        print 'N = %1.1f million \n'%(N*1e-6)

        return ans, ToverTF, N

    def fit_idealfermi_fixedT():
        # this is used by texreport.py
        logfugacity = fugacity_from_temp(T)
        residuals = lambda p, rr, rrdata: ideal_fermi_radial(rr, p[0], \
                                                    logfugacity, p[1]) - rrdata
        ans, cov_x, infodict, mesg, success = sp.optimize.leastsq(residuals, \
                    [guess[0], guess[2]], args=(rcoord[od_cutoff:], od_prof[od_cutoff:])\
                    , full_output=True)
        ToverTF = 0 # fix later
        N = 0 # fix later
        ans = (ans[0], logfugacity, ans[1])

        return ans, ToverTF, N

    def fit_gaussian():
        ans = fit1dfunc(gaussian, rcoord[od_cutoff:], \
                        od_prof[od_cutoff:], [guess[0], guess[2]])
        ToverTF = 1e3 # fix later
        N = gaussian_numbers(ans, pixcal)

        return ans, ToverTF, N


    if fitfunc=='idealfermi':
        ans, ToverTF, N = fit_idealfermi()
    elif fitfunc=='idealfermi_err':
        ans, ToverTF, N = fit_idealfermi()
        T = ToverTF + 0.03
        ans_plus = fit_idealfermi_fixedT()[0]
        T = max(0.001, ToverTF - 0.03)
        ans_min = fit_idealfermi_fixedT()[0]
        return ToverTF, N, [ans, ans_plus, ans_min]
    elif fitfunc=='idealfermi_fixedT':
        ans, ToverTF, N = fit_idealfermi_fixedT()
    elif fitfunc=='gaussian':
        ans, ToverTF, N = fit_gaussian()
    else:
        print 'Fitfunc has an unknown value'

    return ToverTF, N, ans


def fit_img(transimg, odmax=1., showfig=True, elliptic=None, pixcal=10e-6,
            fitfunc='idealfermi', T=None, full_output=None, norm=True):
    """Fits an absorption image with an ideal Fermi gas profile

    The image is normalized, then azimuthally averaged, then fitted. If the
    input is a list of imaged they are separately normalized and then averaged
    and fitted.

    **Inputs**

      * transimg: 2D array or list of 2D arrays, containing the image data

    **Outputs**

      * ToverTF: float, the temperature of the Fermi gas in units of T_F
      * N: float, the number of atoms of the Fermi gas

    **Optional inputs**

      * od_max = float, the maximum optical density that is used in the fit
      * showfig: boolean, determines if a figure is shown with density profile
                 and fit
      * elliptic: tuple, containing two elements. the first one is the
        ellipticity (or ratio of major and minor axes), the second one is the
        angle by which the major axis is rotated from the y-axis
      * pixcal: float, pixel size calibration in m/pix.
      * fitfunc: string, name of the fit function to be used. Valid choices are
        idealfermi, gaussian, idealfermi_fixedT
      * T: float, the temperature for idealfermi_fixedT
      * full_output: string, if value is ``odysseus`` the correct objects for
        the Odysseus GUI are returned
      * norm: bool, if False the normalization of the image is turned off.
              This is mainly useful if you fit computer-generated images or
              images that you already normalized some other way.

    """

    # if the input is a list of images, they are separately normalized and
    # then averaged here. also, the ellipticity of the averaged image is found
    if isinstance(transimg, list):
        avgimg = np.zeros(transimg[0].shape)
        for img in transimg:
            avgimg += norm_and_guess(img)[0]
        transimg = avgimg/np.float(len(transimg))
        if elliptic:
            elliptic = (find_ellipticity(transimg), 0)
    else:
        pass

    if norm:
        transimg, odimg, com, n0, a, bprime = norm_and_guess(transimg)
    else:
        transimg, odimg, com, n0, a, bprime = norm_and_guess(transimg, norm=False)

    # radial averaging of transmission image
    rcoord, rtrans_prof = radial_interpolate(transimg, com, 0.3,
                                             elliptic=elliptic)

    # generate radial density profile
    od_prof = trans2od(rtrans_prof)

    # determine which part of od_prof to fit, to reduce effect
    # of saturation of OD
    od_cutoff = find_fitrange(od_prof, odmax)

    # do the fit
    guess = (n0, a, bprime)
    ToverTF, N, ans = do_fit(rcoord, od_prof, od_cutoff, guess, pixcal,
                             fitfunc=fitfunc, T=T)

    # plot results
    if showfig:
        fit_prof = ideal_fermi_radial(rcoord, *ans)
        fig = show_fitresult(rcoord, od_prof, fit_prof, ToverTF, N, showfig=True)

    if not full_output:
        return (ToverTF, N, ans)
    elif full_output=='odysseus':
        if fitfunc=='idealfermi':
            fit_prof = ideal_fermi_radial(rcoord, *ans)
        elif fitfunc=='idealfermi_err':
            fit_prof = ideal_fermi_radial(rcoord, *ans[0])
            errprof_plus = ideal_fermi_radial(rcoord, *ans[1])
            errprof_min = ideal_fermi_radial(rcoord, *ans[2])
            return (ToverTF, N, com, ans, rcoord, od_prof, fit_prof,
                    errprof_plus, errprof_min)
        elif fitfunc=='idealfermi_fixedT':
            fit_prof = ideal_fermi_radial(rcoord, *ans)
        elif fitfunc=='gaussian':
            # T is high (inf) for Gaussian, put it back in to not mess up GUI
            #ans = (ans[0], 4., ans[1])
            fit_prof = gaussian(rcoord, *ans)
            ans = (ans[0], 4., ans[1])
        else:
            print 'fitfunc has the wrong value'
            raise ValueError

        return (ToverTF, N, com, ans, rcoord, od_prof, fit_prof)
    else:
        print 'Unknown input value for full_output!\n'
        raise ValueError