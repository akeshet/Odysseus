import numpy as np

from pluginmanager import DialogPlugin
from imageprocess import radial_interpolate
from fitfermions import norm_and_guess
import fitfuncs2D


class TwoDFitPlugin(DialogPlugin):
    """Does 2-D fitting with a T-F profile of an image."""

    def main(self, img):
        """Calculate and display the Fourier transform of img"""

        ##transimg, odimg, com, n0, a, bprime = norm_and_guess(img)
        ##rad_coord, rad_profile = radial_interpolate(odimg, com, 0.3)

        ##self.ax.plot(rad_coord, rad_profile)
        ##self.ax.set_xlabel(r'pix')
        ##self.ax.set_ylabel(r'OD')

        pixcal = 10e-6 # 10um / pix

        # normalized the image
        transimg, odimg, com, n0, q, bprime = norm_and_guess(img)

        # choose starting values for fit
        x, y, width_x, width_y = fitfuncs2D.gaussian_moments_2D(odimg)
        guess = np.zeros(10.)
        guess[0:4] = [com[0], com[1], width_x, width_y]
        guess[4] = n0
        guess[5:] = [q, 0., 0., 0., 0.]

        # do the fit, and find temperature and number of atoms
        ans = fitfuncs2D.fit2dfunc(fitfuncs2D.idealfermi_2D_angled, odimg, guess,
                                   tol=1e-10)
        ToverTF, N = fitfuncs2D.ideal_fermi_numbers_2D_angled(ans, pixcal)

        #print ans
        #print 'T/TF = ', ToverTF[0]
        #print 'N = %1.2f million'%(N * 1e-6)

        self.ax.text(0.1, 0.8, str(ans))
        self.ax.text(0.1, 0.4, 'T/TF = %1.3f'%(ToverTF[0]))
        self.ax.text(0.1, 0.2, 'N = %1.2f million'%(N * 1e-6))

        ## show the fit residuals
        residuals = fitfuncs2D.residuals_2D(odimg, ans, func=fitfuncs2D.idealfermi_2D_angled, smooth=4, showfig=True)

