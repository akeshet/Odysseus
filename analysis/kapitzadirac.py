import os

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

from .. import imageio, imageprocess, filetools, fitfuncs
from constants import hbar, mp


k = 2*np.pi/1064e-9
mass_Na = 23*mp
Er = hbar**2*k**2/(2*mass_Na)


def dampedsine(xx, freq, c1, c2, c3, c4):
    """xx is the variable, freq the fit parameter we need"""
    ans = c1 * np.sin(freq*xx+c2) * np.exp(-xx/c3) + c4
    return ans


def bandgap_dE(depth):
    """This is the energy gap between the bottoms of the first and third bands.

    This energy gap, E_{2,0} - E_{0,0}, determines the frequency of
    population oscillation between those bands that we measure. Note that
    this is an approximation that becomes inaccurate above lattice depths of
    about 10 Er. Between 5 and 10 Er seems best to do the calibration.

    """

    return Er*np.sqrt(16 + 12./25*depth**2)


def lat_depth(freq):
    """Calculate the lattice depth from Kapitza-Dirac calibration procedure"""

    def dE_minus_hw(depth):
        """Lattice depth in recoils"""
        return bandgap_dE(depth) - hbar*freq

    ans = sp.optimize.fsolve(dE_minus_hw, 10)
    return ans


def analyze_kapitzadirac(imglist, lat_time, roi, showfig=False):
    """Loads images in .xraw format, saves as hdf5, and extracts sum(OD) in ROI

    **Inputs**

      * imglist: list, containing the paths to the images to analyze
      * lat_time: 1D array, the time the lattice is pulsed on
      * roi: tuple of slices, the two slices that define the ROI
      * showfig: bool, if True show the OD image. Useful to determine the ROI.

    **Outputs**

      * count: float, the sum of OD in the ROI

    """

    assert len(imglist)==lat_time.size
    count = []
    for img in imglist:
        try:
            transimg = imageio.load_hdfimage(img)
        except IOError:
            imgarray = imageio.import_xcamera(img)
            transimg, odimg = imageio.calc_absimage(imgarray)
            save_hdfimage(transimg.astype(np.float32), img)

        transimg *= transimg.size/transimg.sum()
        odimg = imageprocess.trans2od(transimg)

        if showfig:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.imshow(odimg, vmin=0, vmax=1.35)
            plt.show()

        odimg = odimg[roi]
        count.append(odimg.sum())
        print img, odimg.sum()

    return count


def show_kd_result(time_on, sum_od, fitparams):
    """Show the fit of Kapitza-Dirac data, and graphically found lattice depth.

    The factor of 0.321 results from scaling the results for Na to Li. This
    factor is the ration of (mass * polarizability). See for example
    Greiner's thesis, eqs 3.19 and 3.7.

    **Inputs**

      * time_on: 1D array, the time the lattice is pulsed on in us.
      * sum_od: 1D array, the sum OD over the whole first order in the
                absorption picture after a K-D pulse.
      * fitparams: list, the fit parameters when dampedsine() is fitted to
                   the data.

    """

    Na_depth = lat_depth(fitparams[0]*1e6)
    Li_depth = Na_depth*0.3065 # ratio of ac Stark shift over Er for Na/Li
    print 'lattice depth for Na is: ', Na_depth
    print 'lattice depth for Li is: ', Li_depth

    fig = plt.figure()
    ax = fig.add_subplot(211)
    ax.plot(time_on, sum_od, 'bo')
    xx = np.linspace(0, time_on.max(), num=500)
    ax.plot(xx, dampedsine(xx, *fitparams), 'r-')
    ax.set_xlabel(r'$t_{TOF}$ [$\mu$s]')
    ax.set_ylabel(r'sum(OD)')

    ax2 = fig.add_subplot(212)
    xx = np.linspace(0.01, Na_depth*1.4)
    ax2.plot(xx, bandgap_dE(xx)/Er, 'r-')
    ax2.axhline(hbar*fitparams[0]*1e6/Er, color='b')
    ax2.axvline(Na_depth, ymin=0, ymax=hbar*fitparams[0]*1e6/Er,
                color='k', ls='--')
    ax2.set_xlabel(r'Na depth [$V_0/E_R$]')
    ax2.set_ylabel(r'$E/E_R$')
    ax2.text(0.08, 0.85, r'Na depth: %1.2f $E_R$'%Na_depth,
             transform=ax2.transAxes)
    ax2.text(0.08, 0.75, r'Li depth: %1.2f $E_R$'%Li_depth,
             transform=ax2.transAxes)

    plt.show()


def main():
    ########################
    ### left lattice data ##
    ########################
    """Calibration done with lattice setpoint 944mV on scope"""
    leftcal_list = filetools.get_files_in_dir('.', globexpr='kdleft1*.xraw0')
    leftcal_list = filetools.sort_files_by_date(leftcal_list, newestfirst=False)

    leftroi=[slice(340, 475), slice(625, 650)]
    leftcount = []
    # time the lattice beam was pulsed on in us
    left_time_on = np.arange(2, 46, 2)

    leftcount = analyze_kapitzadirac(leftcal_list, left_time_on, leftroi)
    guess = [0.4, 1e4, 0, 100, 5e3]
    ans = fitfuncs.fit1dfunc(dampedsine, left_time_on, leftcount, guess)
    show_kd_result(left_time_on, leftcount, ans)


if __name__ == "__main__":
    main()