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
        transimg1, odimg1 = imageprocess.calc_absimage(np.dstack([img[:, :, 1],
                                                                  img[:, :, 5],
                                                                  img[:, :, 3]]),
                                                       norm_edge=True)
        transimg2, odimg2 = imageprocess.calc_absimage(np.dstack([img[:, :, 2],
                                                                  img[:, :, 6],
                                                                  img[:, :, 4]]),
                                                       norm_edge=True)
        odimg1 = imageprocess.normalize_edgestrip(odimg1)
        odimg2 = imageprocess.normalize_edgestrip(odimg2)
        balance = odimg1[roi].mean() / odimg2[roi].mean()

        self.ax1.imshow(transimg1, vmin=0, vmax=1.35, cmap=mpl.cm.gray)
        self.ax2.imshow(transimg2, vmin=0, vmax=1.35, cmap=mpl.cm.gray)
        self.balance_label.setText('The balance is %s'%balance)
