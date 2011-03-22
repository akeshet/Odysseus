#!/usr/bin/env python
"""Import image, radially average it and fit a bimodal Bose distribution to it.

NOTE that this file is a bit of a mess and not suitable for use as a library
file.

"""


from scipy import *
from pylab import *
import Image, numpy
from scipy.optimize import leastsq
from scipy.interpolate import RectBivariateSpline
import centerofmass as cmass
from polylog import g2, g52, g3
from imageprocess import radial_interpolate, plot_fitresults
from constants import kb, mp

fname = 'NaBEC' #'NaBEC_56ms_tof'
im = Image.open(''.join(['../../archives/2008-04-21/', fname, '.TIF']))
transimg = numpy.asarray(im)
# normalize to background transmission of 1
bg = transimg[0:-20, :]
transimg = transimg/(bg.sum()/bg.size)
od10img = where(transimg>1e-10, -log10(transimg), 10)
pixsize = 20e-6 #20 um/pixel
mag = 2 # magnification
mass_Na = 23*mp
wr = 84 # radial trap freq in Hz
t_tof = 56e-3 # time of flight in seconds

# determine center of mass to use as parameter in fitting of n2D_radial to od10img
com = cmass.center_of_mass(od10img)

def n2D_bose_thermal(r, n0_th, r0_th):
    """Column density for a thermal Bose gas.

    Assume radial symmetry of the cloud, n0_th and r0_th are fit parameters. r
    is a 1d array with values of r with respect to the center of the atom cloud.
    """
    return n0_th/g2(1)*g2(1-r**2/r0_th**2)

def n2D_bose_condensed(r, n0_c, r0_c):
    """Column density for a condensed Bose gas.

    Assume radial symmetry of the cloud, n0_c and r0_c are fit parameters. r
    is a 1d array with values of r with respect to the center of the atom cloud.
    """
    nc = 1-r**2/r0_c**2
    return n0_c*select([nc>0], [nc])**(1.5)

def bimodal(r, n0_th, r0_th, n0_c, r0_c):
    """Bimodal distribution for a partially condensed Bose gas."""
    return n2D_bose_thermal(r, n0_th, r0_th) + n2D_bose_condensed(r, n0_c, r0_c)

def n2D_r(r, fitparams):
    """2D density distribution used for determining the number of atoms"""
    n0_th, r0_th, n0_c, r0_c = fitparams
    oneDfunc = bimodal(r, n0_th, r0_th, n0_c, r0_c)
    return 2*pi*r*oneDfunc

# guess initial fit parameters
n0_c = od10img[com[0]-5:com[0]+5, com[1]-5:com[1]+5].sum()*1e-2 # av. central OD
n0_th = n0_c*0.1
r0_th = 50 # thermal radius after TOF expansion in pixels
r0_c = 25 # condensed radius after TOF expansion in pixels
p0 = [n0_th, r0_th, n0_c, r0_c]

def residuals(p, rr, rrdata):
    print 'p', p
    n0_th, r0_th, n0_c, r0_c = p
    """
    Returns the residuals of the fit of bimodal() to the od10 image.
    p is the array of fit parameters
    """
    err = rrdata - bimodal(rr, n0_th, r0_th, n0_c, r0_c)
    print 'err', (err**2).sum()
    return err

def residuals2(p, rr, rrdata):
    print 'p', p
    n0_th, r0_th = p
    """
    Returns the residuals of the fit of n2D_bose_thermal() to the od10 image.
    p is the array of fit parameters
    """
    err = rrdata - n2D_bose_thermal(rr, n0_th, r0_th)
    print 'err', (err**2).sum()
    return err

# radial averaging of transmission image
rcoord, rtrans_prof = radial_interpolate(transimg, com, 0.15, dphi=12)
# generate radial density profile
od_prof = where(rtrans_prof>1e-10, -log10(rtrans_prof), 10)

# fit density profile where it is not blacked out
ans, succes = leastsq(residuals, p0, args=(rcoord[100:], od_prof[100:]), ftol=1e-8)

#p02 = [ans[0], ans[1]]
#ans2, succes2 = leastsq(residuals2, p02, args=(rcoord[700:], od_prof[700:]), ftol=1e-8)

# determine temperature and number of atoms
T = 0.5*mass_Na*wr**2/(1+wr**2*t_tof**2)*(ans[1]*pixsize/mag)**2/kb
print 'T = ', T

sigma = 3*589e-9**2/(2*pi) # resonant photon absorption cross-section for Na
N = (pixsize/float(mag))**2*integrate.quad(n2D_r, 0, rcoord.max(), args=(ans))[0]/sigma
print 'N = %1.1f million'%(N*1e-6)

fit_prof = bimodal(rcoord, ans[0], ans[1], ans[2], ans[3])

fig = plot_fitresults(rcoord, rtrans_prof, od_prof, fit_prof, T, N)
show()

#if __name__ == 'main':
    #main()