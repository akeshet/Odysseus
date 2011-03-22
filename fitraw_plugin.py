from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT

from mplwidgets import BlankCanvas
from pluginmanager import IPlugin
import imageprocess


class SpinBalancePlugin(IPlugin):
    """Defines the interface for a plugin that pops up a dialog with an image"""

    def create_window(self, img, roi, name):
        """Create dialog and image inside it

        **Inputs**

          * img: 2d-array, containing the image data
          * roi: tuple of slices, contains two slice objects, one for each
                 image axis. The tuple can be used as a 2D slice object.
          * name: string, the name of the plugin

        """

        self.window = SpinBalanceDialog()

        # call the user-implemented functionality
        self.window.main(img, roi)
        # show the window
        self.window.show()

        return self.window


class SpinBalanceDialog(QDialog):
    """Displays two absorption images and calculates the ratio N1/N2."""

    def __init__(self, parent=None):
        super(SpinBalanceDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle('Spin balance dialog')

        self.fig1 = BlankCanvas()
        self.ax1 = self.fig1.ax
        self.fig2 = BlankCanvas()
        self.ax2 = self.fig2.ax
        self.toolbar1 = NavigationToolbar2QT(self.fig1, self)
        self.toolbar2 = NavigationToolbar2QT(self.fig2, self)
        self.balance_label = QLabel()

        layout1 = QVBoxLayout()
        layout1.addWidget(self.fig1)
        layout1.addWidget(self.toolbar1)
        layout2 = QVBoxLayout()
        layout2.addWidget(self.fig2)
        layout2.addWidget(self.toolbar2)
        layout = QHBoxLayout()
        layout.addLayout(layout1)
        layout.addLayout(layout2)
        layout.addWidget(self.balance_label)
        self.setLayout(layout)


    def main(self, img, roi):
        """Create dialog and image inside it"""

        self.img = img
        self.roi = roi

        pwa = img[:,:,0]
        pwoa = img[:,:,1]
        df = img[:,:,2]

        pwa=pwa[roi]
        pwoa=pwoa[roi]
        df=df[roi]

        transimg1, odimg1 = imageprocess.calc_absimage(img,norm_edge=True)

        ##transimg, odimg, com, n0, a, bprime = norm_and_guess(img)
        ##rad_coord, rad_profile = radial_interpolate(odimg, com, 0.3)

        ##self.ax.plot(rad_coord, rad_profile)
        ##self.ax.set_xlabel(r'pix')
        ##self.ax.set_ylabel(r'OD')

        pixcal = 10e-6 # 10um / pix

        # normalized the image
        transimg, odimg, com, n0, q, bprime = norm_and_guess(transimg1)

        # choose starting values for fit
        x, y, width_x, width_y = fitfuncs2D.gaussian_moments_2D(odimg)
        guess = np.zeros(10.)
        guess[0:4] = [com[0], com[1], width_x, width_y]
        guess[4] = n0
        guess[5:] = [q, 0., 0., 0., 0.]

        # do the fit, and find temperature and number of atoms
        ans = fitfuncs2D.fit2dfuncraw(fitfuncs2D.idealfermi_2D_angled, pwa, pwoa, df, guess, tol=1e-10)
        ToverTF, N = fitfuncs2D.ideal_fermi_numbers_2D_angled(ans, pixcal)

        #print ans
        #print 'T/TF = ', ToverTF[0]
        #print 'N = %1.2f million'%(N * 1e-6)

        self.ax.text(0.1, 0.8, str(ans))
        self.ax.text(0.1, 0.4, 'T/TF = %1.3f'%(ToverTF[0]))
        self.ax.text(0.1, 0.2, 'N = %1.2f million'%(N * 1e-6))

        ## show the fit residuals
        residuals = fitfuncs2D.residuals_2D(odimg, ans, func=fitfuncs2D.idealfermi_2D_angled, smooth=4, showfig=False)


        self.ax1.imshow(residuals, vmin=0, vmax=.1, cmap=mpl.cm.gray)
        self.ax2.imshow(odimg, vmin=0, vmax=1.35, cmap=mpl.cm.gray)
