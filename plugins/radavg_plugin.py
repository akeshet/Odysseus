import numpy as np

from pluginmanager import DialogPlugin
from imageprocess import radial_interpolate
from fitfermions import norm_and_guess


class RadialAveragePlugin(DialogPlugin):
    """Does radial averaging of an image"""

    def main(self, img):
        """Calculate and display the Fourier transform of img"""

        transimg, odimg, com, n0, a, bprime = norm_and_guess(img)
        rad_coord, rad_profile = radial_interpolate(odimg, com, 0.3)

        self.ax.plot(rad_coord, rad_profile)
        self.ax.set_xlabel(r'pix')
        self.ax.set_ylabel(r'OD')

