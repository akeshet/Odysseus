#!/usr/bin/env python
"""Image processing functions

Some functionality is independent of the type of image, for example
smoothing, thresholding and interpolation. Other functionality is specific
to cold atom experiments, for example calculating optical density and
transmission for absorption images.

"""

import os

import scipy as sp
import scipy.ndimage as ndimage
import numpy as np
import Image
import matplotlib as mpl
import pylab


def trans2od(transimg, maxod=3.5):
    """Calculates the optical density image from a transmission image

    For pixels with strange values due to noise, replace the value of that pixel
    by the maximum OD that can be experimentally measured.

    """

    odimg = np.where(transimg>np.exp(-maxod), -np.log(transimg), maxod)

    return odimg


def od2trans(odimg, maxod=3.5):
    """Calculates the transmission image from an optical density image

    For pixels with strange values due to noise, replace the value of that pixel
    by the maximum OD that can be experimentally measured.

    """

    transimg = np.where(odimg<maxod, np.exp(-odimg), np.exp(-maxod))

    return transimg


def calc_absimage(raw_frames, norm_edge=False):
    """Calculates the transmission image and optical density.

    **Inputs**

      * raw_frames: 3D array, containing three or four images;
                    probe with atoms (pwa), probe without atoms (pwoa),
                    dark field (df) and `optionally` a second dark field (df2).
                    If there is no second dark field, the same one is used
                    twice.
      * norm_edge: bool, if True, normalize to one using the edge (it is assumed
                   no atoms are visible on the edge.

    **Outputs**

      * transimg: 2d array containing the transmission image,
              defined as (pwa - df)/(pwoa - df2).
      * odimg: 2d array containing the optical density for each pixel

    """

    pwa = raw_frames[:, :, 0]
    pwoa = raw_frames[:, :, 1]
    df = raw_frames[:, :, 2]
    try:
        df2 = raw_frames[:, :, 3]
    except IndexError:
        df2 = df

    nom = pwa - df
    den = pwoa - df2
    nom = np.where(nom<1, 1, nom)
    den = np.where(den<1, 1, den)
    if norm_edge:
        nom = normalize_edgestrip(nom)
        den = normalize_edgestrip(den)

    transimg = nom.astype(float)/den
    odimg = -np.log(transimg)

    return transimg, odimg
    
def calc_absimage_list(imgs):
    """Calculates the transmission image and optical density
    for a list of images. Uses the calc_absimage function
    for the calculation.

    **Inputs**

      * imgs:  A list of images formatted in the style
                of the input to calc_absimage.
                
    **Outputs**
        (trs, ods)
       *  trs: list of transmission images, formatted as in calc_image
       *  ods: list of optical density images


    """
    
    ods = []
    trs = []
    
    print("Calculating image ODs...")
    for im in imgs:
        (tr, od) = calc_absimage(im)
        ods.append(od)
        trs.append(tr)
    print("...done")
    
    return (trs,ods)


def threshold_image(img, thres=0.5, below=True):
    """Returns a binary array (ones and zeros) depending on pixel values.

    **Inputs**

      * img: array, containing an image (also works for non-image data)
      * thres: scalar value, the threshold value
      * below: boolean value, True means that each element of img that is below
           thres gives a 1 in the thresholded image, and each element that
	   is above it a 0.

    **Outputs**

      * thres_img: array, containing ones and zeros as a result of
                   thresholding the input array.

    """

    if below:
        thres_img = np.where(img<thres, 1, 0)
    else:
        thres_img = np.where(img<thres, 0, 1)

    return thres_img


def find_fitrange(od_prof, od_max=1, min_cutoff=8):
    """Select a suitable range of radii to use for fitting the image.

    When the optical density saturates at a certain range of radii, and then
    that data range is used for fitting, it throws off the fit. Therefore
    a cutoff value for the maximum optical density should be specified, and the
    fit only done for values of OD smaller than that. The data is smoothed,
    and the index for the radius where the OD drops below OD_max is determined.

    **Inputs**

      * od_prof: 1D array, containing the radially averaged optical density
                 profile.

    **Outputs**

      * cutoff: int, the larger value of index of rcoord where od_prof<od_max
                     or min_cutoff.

    **Optional inputs**

      * od_max: float, the maximum desired value of the optical density
      * min_cutoff: int, the minimum value for the cutoff index. The reason to
                    use this is that a radially averaged profile is very noisy
                    around the center which may skew a fit.

    """
    try:
        od_new = smooth(od_prof, window_len=15)
        cutoff = mpl.mlab.find(od_new<od_max).min()
    except ValueError:
        # no values below the cutoff
        cutoff = min_cutoff

    cutoff = max(cutoff, min_cutoff)
    if cutoff > od_prof.size:
        raise ValueError, 'Input array is smaller than min_cutoff'

    return cutoff


def radial_interpolate(img, com, dr, phi=None, elliptic=None, full_output=False):
    """Does radial averaging around the center of mass of the image.

    Radial averaging of the image data on circles spaced by dr around the
    center of mass. The number of points on each circle is dphi*sqrt(i+1),
    with i the circle index. A bilinear interpolation method is used.

    **Inputs**

      * img: 2D array, normally containing image data
      * com: 1D array with two elements, the center of mass coordinates in
             pixels
      * dr: radial step size in pixels

    **Outputs**

      * rcoord: 1D array containing the radial coordinate
      * rad_profile: 1D array containing the averaged profile

    **Optional inputs**

      * phi: 1D array, the angles along which line profiles are taken. More
             values in phi means a more precise radial average; default is
             2*pi times the maximum radius in pixels
      * elliptic: tuple, containing two elements. the first one is the
        ellipticity (or ratio of major and minor axes), the second one is the
        angle by which the major axis is rotated from the y-axis.
      * full_output: bool, selects whether rprofiles and phi are returned

    """

    xsize, ysize = img.shape
    # number of used points in radial direction, stops if image edge is reached
    rmax = np.array([xsize-com[0], com[0], ysize-com[1], com[1]]).min()
    rcoord = np.arange(0, rmax, dr)
    if not phi:
        phi = np.linspace(0, 2*np.pi, rmax*np.pi)

    rprofiles = lineprofiles(img, com, rcoord, phi, elliptic=elliptic)
    rad_profile = rprofiles.mean(axis=1)

    if full_output:
        return rcoord, rad_profile, rprofiles, phi
    else:
        return rcoord, rad_profile


def lineprofiles(img, com, rcoord, phi, elliptic=None):
    """Generate radial profiles around center of mass

    Line profiles without any averaging are generated. This is useful for
    comparing the radially averaged profile with, to make sure that that is a
    valid procedure.

    **Inputs**

      * img: 2D array, normally containing image data
      * com: 1D array with two elements, the center of mass coordinates in pixels
      * rcoord: 1D array, radial coordinate for line profiles
                this is usually obtained from radial_interpolate
      * phi: 1D array, angles along which line profiles are required

    **Outputs**

      * rprofiles: 2D array, containing radial profiles along angles

    **Optional inputs**

      * elliptic: tuple, containing two elements. the first one is the
        ellipticity (or ratio of major and minor axes), the second one is the
        angle by which the major axis is rotated from the y-axis. This should
        be the same as used for radial averaging.

    **Notes**

      The form used for mapping an ellipse to (x,y) coordinates is:
      x = a\cos\phi\cos\alpha - b\sin\phi\sin\alpha
      y = b\sin\phi\cos\alpha + a\cos\phi\sin\alpha

    """

    indshape = (phi.size, rcoord.size)

    if elliptic:
        (ell, rot) = elliptic
    else:
        (ell, rot) = (1, 0)

    xr = com[0] + (np.ones(indshape)*rcoord).transpose()*np.cos(phi)*np.cos(rot) -  \
         ell*(np.ones(indshape)*rcoord).transpose()*np.sin(phi)*np.sin(rot)
    yr = com[1] + ell*(np.ones(indshape)*rcoord).transpose()*np.sin(phi)*np.cos(rot) - \
         (np.ones(indshape)*rcoord).transpose()*np.cos(phi)*np.sin(rot)

    rprofiles = bilinear_interpolate(xr, yr, img)

    return rprofiles


# move out the plotting part!
def radialprofile_errors(odprofiles, angles, od_prof, od_cutoff, \
                         showfig=False, savefig_name=None, report=True):
    """Calculate errors in radial profiles as a function of angle

    **Inputs**

      * odprofiles: 2D array, containing radial OD profiles along angles
      * angles: 1D array, angles at which radial profiles are taken
                          (zero is postive x-axis)
      * od_prof: 1D array, radially averaged optical density
      * od_cutoff: integer, index of profiles at which maximum fit-OD is reached

    **Outputs**

      * av_err: float, sum of absolute values of errors in errsum

    **Optional inputs**

      * showfig: bool, determines if a figure is shown with density profile
                 and fit
      * report: bool, if True print the sums of the mean and rms errors
      * savefig_name: string, if not None and showfig is True, the figure is
                      not shown but saved as png with this string as filename.

    """

    err = (odprofiles[od_cutoff:, :].transpose() - \
           od_prof[od_cutoff:]).sum(axis=1)

    av_err = np.abs(err).mean()

    if report:
        print 'mean error is ', err.mean()
        print 'rms error is ', av_err

    if showfig:
        # angular plot of errors, red for positive, blue for negative values
        pylab.figure()
        poserr = pylab.find(err>0)
        negerr = pylab.find(err<0)

        pylab.polar(angles[negerr], np.abs(err[negerr]), 'ko', \
                    angles[poserr], np.abs(err[poserr]), 'wo')
        pylab.title('Angular dependence of fit error')
        pylab.text(np.pi/2+0.3, np.abs(err).max()*0.85, \
                   r'$\sum_{\phi}|\sum_r\Delta_{OD}|=%1.1f$'%av_err)
        if not savefig_name:
            pylab.show()
        else:
            pylab.savefig(''.join([os.path.splitext(savefig_name)[0], '.png']))

    return av_err


def bilinear_interpolate(xr, yr, img):
    """Do a bi-linear interpolation to get the value at image coordinates

    **Inputs**
      * xr: array-like, the x-coordinates of the point to be interpolated
      * yr: array-like, the y-coordinates of the point to be interpolated
      * img: 2d-array, the image data

    **Outputs**
      * ans: array-like, the result of the interpolation

    """

    ans = ndimage.map_coordinates(img, np.array([xr, yr]), order=1, \
                                  mode='nearest')
    return ans


def imgslice(img, cpoint, angle=0, width=None):
    """Take a line profile through the centerpoint

    **Inputs**
      * img: 2D array, the image data
      * cpoint: 1D array, the center point coordinates of the required slice

    **Outputs**
      * lprof_coord: 1D array, the slice indices in units of pixels
      * lprof: 1D array, the slice data

    **Optional inputs**

      * angle: float, the angle under which the slice is taken in degrees
      * width: float, the width over which the slice is averaged

    """

    angle = angle*np.pi/180 # deg to rad
    # determine coefficients a and b of center line y=ax+b
    a = np.tan(angle)
    b = cpoint[1] - cpoint[0]*a
    # max of indices
    xmax, ymax = img.shape
    xmax = xmax-1
    ymax = ymax-1
    # determine begin and end points of center line
    if 0 < b < ymax:
        startpt = (0, b)
    elif 0 < -b/a < xmax:
        startpt = (-b/a, 0)
    else:
        startpt = ((ymax-b)/a, ymax)
    if 0 < a*xmax+b < ymax:
        stoppt = (xmax, a*xmax+b)
    elif 0 < (ymax-b)/a < xmax:
        stoppt = ((ymax-b)/a, ymax)
    else:
        stoppt = (-b/a, 0)

    def dist(a, b):
        """Distance between points"""
        d = a - b
        return np.sqrt(np.dot(d,d))

    slicelen = min(dist(startpt, cpoint), dist(stoppt, cpoint))*0.8

    # generate the slice coordinates, discard endpoint (safer for interpolation)
    npts = 3
    xslice = cpoint[0] + np.arange(-slicelen, slicelen, 1./npts)*np.cos(angle)
    yslice = cpoint[1] + np.arange(-slicelen, slicelen, 1./npts)*np.sin(angle)

    if width:
        try:
            perpstep = np.linspace(-width/2., width/2., num=round(width))
            lprof = np.zeros((xslice.size, perpstep.size))
            for i in xrange(perpstep.size):
                xx_slice = xslice + perpstep[i]*np.cos(angle+np.pi/2)
                yy_slice = yslice + perpstep[i]*np.sin(angle+np.pi/2)
                lprof[:, i] = bilinear_interpolate(xx_slice, yy_slice, img)
            lprof = lprof.mean(axis=1)
        except IndexError:
            print 'Index out of bounds, may be an error in the if/else code above'
            raise IndexError
    else:
        xslice = xslice[1:-1]
        yslice = yslice[1:-1]
        lprof = bilinear_interpolate(xslice, yslice, img)

    lprof_coord = np.arange(lprof.size)-lprof.size/2.

    return lprof_coord, lprof, npts


def mirror_line(linedata, negative_mirror=False):
    """Mirrors a 1D array around its first element

    **Inputs**

      * linedata: 1D array, the array to be mirrored
      * negative_mirror: bool, if True the mirrors elements are multiplied by
                         -1. This is useful to mirror the x-axis of a plot.

    **Outputs**

      * mirrored: 1D array, the output array, which is now symmetric around its
                  midpoint.

    """

    mir_size = linedata.shape[0] -1
    mirrored = np.zeros(mir_size*2 + 1)
    mirror_idx = np.arange(mir_size, 0, -1)
    mirrored[:mir_size] = linedata[mirror_idx]
    mirrored[mir_size:] = linedata

    if negative_mirror:
        mirrored[:mir_size] *= -1

    return mirrored


def smooth(x, window_len=10, window='hanning'):
    """Smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    Adapted from the Scipy Cookbook by Ralf Gommers.

    **Inputs**

      * x: 1D array, data that needs to be smoothed

    **Outputs**

      * x_smooth: 1D array, the smoothed signal

    **Optional inputs**

      * window_len: int, the size of the smoothing window
      * window: str, the type of window from 'flat', 'hanning', 'hamming',
                     'bartlett', 'blackman'. A flat window will produce a
                     moving average smoothing.

    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        window_len = round(x.size/2)

    if window_len<3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, \
              """Window is on of 'flat', 'hanning', 'hamming',
              'bartlett', 'blackman'"""

    s = np.r_[2*x[0]-x[window_len:1:-1], x, 2*x[-1]-x[-1:-window_len:-1]]

    if window=='flat': # moving average
        w = np.ones(window_len, 'd')
    else:
        w = eval('np.'+window+'(window_len)')

    y = np.convolve(w/w.sum(), s, mode='same')
    x_smooth = y[window_len-1:-window_len+1]

    return x_smooth


def maxod_correct(odimg, odmax):
    """Corrects calculated OD from an absorption image for finite OD_max

    This idea was taken from Brian DeMarco's thesis, but it does not seem to
    make much of a difference at low OD. For high-OD images it causes errors
    because there will be data points with measured OD higher than the maximum
    observable OD due to noise in the image.

    It is left in here for completeness, but it is recommended to not use this
    method. Instead, images should be taken in a regime where this correction
    is negligibly small anyway (i.e. below an OD of 1.5).

    """

    c = np.exp(odmax) - 1
    realOD = -np.log((c+1.)/c*np.exp(-odimg) - 1./c)

    return realOD


def normalize_img(img, com, size):
    """Mask off the atoms, then fit linear slopes to the image and normalize

    We assume that there are no atoms left outside 1.5 times the size. This
    seems to be a reasonable assumption, it does not influence the result of
    the normalization.

    **Inputs**

      * img: 2D array, containing the image
      * com: tuple, center of mass coordinates
      * size: float, radial size of the cloud

    **Outputs**

      * normimg: 2D array, the normalized image

    """

    xmax, ymax = img.shape

    # create mask
    x_ind1 = round(com[0] - 1.5*size)
    x_ind2 = round(com[0] + 1.5*size)
    y_ind1 = round(com[1] - 1.5*size)
    y_ind2 = round(com[1] + 1.5*size)

    # fit first order polynomial along x and y (do not use quadratic terms!!)
    if x_ind1>0 and x_ind2<xmax and y_ind1>0 and y_ind2<ymax:
        normx = np.zeros(x_ind1 + xmax - x_ind2, dtype=float)
        xx = np.ones(normx.shape)
        xx[:x_ind1] = np.arange(x_ind1)
        xx[x_ind1:] = np.arange(x_ind2, xmax)
        normx[:x_ind1] = img[:x_ind1, :].mean(axis=1)
        normx[x_ind1:] = img[x_ind2:, :].mean(axis=1)

        # fit normx vs xx
        fitline = np.polyfit(xx, normx, 1)

        divx = np.ones(img.shape, dtype=float).transpose()*\
             np.polyval(fitline, np.arange(img.shape[0])).transpose()
        normimg = img/divx.transpose()

        normy = np.zeros(y_ind1 + ymax - y_ind2, dtype=float)
        yy = np.ones(normy.shape)
        yy[:y_ind1] = np.arange(y_ind1)
        yy[y_ind1:] = np.arange(y_ind2, ymax)
        normy[:y_ind1] = normimg[:, :y_ind1].mean(axis=0)
        normy[y_ind1:] = normimg[:, y_ind2:].mean(axis=0)

        # fit normx vs yy
        fitline = np.polyfit(yy, normy, 1)

        divy = np.ones(normimg.shape, dtype=float)*\
             np.polyval(fitline, np.arange(normimg.shape[1]))
        normimg = normimg/divy
    else:
        print "atom cloud extends to the edge of the image, can't normalize"
        raise NotImplementedError

    return normimg


def normalize_edgestrip(img, normval=1., striplen=5):
    """Normalizes the image so the average value on the edges is normval.

    This is simply a multiplication of the whole image array by a number
    so that the average intensity on the edges of the image is `normval`.

    **Inputs**

      * img: 2D array, image data
      * normval: float, the value to which img is normalized
      * striplen: int, number of pixels along each edge used for normalization

    **Outputs**

      * normimg: 2D array, the normalized image

    """

    vstrip = (img[:striplen, :] + img[-striplen:, :])*0.5
    hstrip = (img[:, :striplen] + img[:, -striplen:])*0.5
    normfactor = (hstrip.sum() + vstrip.sum())/(hstrip.size + vstrip.size)
    normimg = img*normval/normfactor

    return normimg
