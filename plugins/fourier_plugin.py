import numpy as np
from pluginmanager import DialogPlugin


class FourierPlugin(DialogPlugin):
    """Does Fourier transformation of an image"""

    def main(self, img):
        """Calculate and display the Fourier transform of img

        The zero frequency is shifted to the center of the image.

        """

        self.ax.imshow(np.abs(np.fft.fftshift(np.fft.fft2(img))))


