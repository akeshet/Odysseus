"""A plugin for generating line profiles of images

Note regarding the code
-----------------------
The GUI is created from within Qt Designer, and saved in .ui format.
Generate the python class for the GUI with pyuic4:
``pyuic4 -o lineprofile_plugin_ui.py lineprofile_plugin_ui.ui``

After running pyuic4, it is necessary to edit the generated file and change
the toolbars:
self.toolbar = NavigationToolbar2QT(LineProfile)
self.toolbar_2 = NavigationToolbar2QT(LineProfile)
has to become:
self.toolbar = NavigationToolbar2QT(self.imgView, LineProfile)
self.toolbar_2 = NavigationToolbar2QT(self.lineprofileView, LineProfile)

"""


import numpy as np
import matplotlib as mpl
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT

from pluginmanager import IPlugin
from plugins.lineprofile_plugin_ui import Ui_LineProfile
from imageprocess import imgslice, smooth
from fitfermions import norm_and_guess


class LineProfilePlugin(IPlugin):
    """Defines the interface for a plugin that pops up a dialog with an image"""

    def create_window(self, img, roi, name):
        """Create dialog and image inside it

        **Inputs**

          * img: 2d-array, containing the image data
          * roi: tuple of slices, contains two slice objects, one for each
                 image axis. The tuple can be used as a 2D slice object.
          * name: string, the name of the plugin

        """

        self.window = LineProfileDialog(name)

        # call the user-implemented functionality
        self.window.main(img[roi])
        # show the window
        self.window.show()

        return self.window


class LineProfileDialog(QDialog, Ui_LineProfile):
    """Handles the window that the line profile plugin pops up"""

    def __init__(self, name, parent=None):
        super(LineProfileDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(name)

        self.setupUi(self)

        # code to test the dialog stand-alone
        if __name__=='__main__':
            self.img = np.random.rand(200, 200)
            self.roi = (slice(0, 150), slice(0, 150))
            self.main(self.img)

        # signal-slot connections
        self.connect(self.computeProfile, SIGNAL("clicked()"), \
                     self.compute_profile)
        self.connect(self.setCoM, SIGNAL("clicked()"), self.set_cpoint)
        self.connect(self.setAngles, SIGNAL("clicked()"), self.set_angles)


    def main(self, img):
        """Create dialog and image inside it

        **Inputs**

          * img: 2d-array, containing the image data
          * roi: tuple of slices, contains two slice objects, one for each
                 image axis. The tuple can be used as a 2D slice object.
          * name: string, the name of the plugin

        **Notes**

        This function is called from Odysseus.

        """

        self.img = img
        transimg, odimg, com, n0, a, bprime = norm_and_guess(self.img, norm=False)
        self.odimg = odimg
        self.com = com
        self.cpoint = com
        self.set_cpoint()
        self.defaultangles = self.anglesList.toPlainText()

        cpoint = self.get_cpoint()
        self.marker = self.imgView.ax.plot([cpoint[0]], [cpoint[1]], 'r+')[0]
        self.imgView.ax.imshow(self.img, cmap=mpl.cm.gray, vmin=0, vmax=1.35)
        self.imgView.ax.set_xticks([])
        self.imgView.ax.set_yticks([])

        self.compute_profile()


    def compute_profile(self):
        """Compute and plot the line profile(s)"""

        self.lineprofileView.ax.hold(False)
        len = self.smoothWindowlength.value()
        cp = self.get_cpoint()
        width = self.linewidth.value()

        angles = self.get_angles()
        for i, ang in enumerate(angles):
            if i==1:
                self.lineprofileView.ax.hold(True)
            lpcoord, lp, npts = imgslice(self.odimg, np.array([cp[0], cp[1]]),
                                         angle=ang, width=width)
            self.lineprofileView.ax.plot(lpcoord/float(npts),
                                         smooth(lp, window_len=len,
                                                window=str(self.smoothType.currentText()).lower()),
                                         label=r'$\alpha=%s^{\circ}$'%ang)

        self.lineprofileView.ax.legend()
        self.lineprofileView.ax.set_xlabel(r'$r_{CoM}$ [pix]')
        self.lineprofileView.ax.set_ylabel(r'$OD$')

        self.lineprofileView.draw()
        self.update_imgview()


    def update_imgview(self):
        """Update the image, keeping the zoom level the same."""

        cpoint = self.get_cpoint()
        self.marker.set_data(np.array([cpoint[1]]), np.array([cpoint[0]]))
        self.imgView.draw()


    def get_cpoint(self):
        """Updates the center point coordinates"""

        x = self.center_x.value()
        y = self.center_y.value()
        self.cpoint = [min(x, self.img.shape[0]), min(y, self.img.shape[1])]

        return self.cpoint


    def set_cpoint(self):
        """Updates the center point coordinate spinboxes to the CoM"""

        self.center_x.setValue(self.com[0])
        self.center_y.setValue(self.com[1])


    def get_angles(self):
        """Extracts the angles from the text edit area anglesList"""

        angles_str = self.anglesList.toPlainText()
        anglist = str(angles_str).splitlines()
        angarray = np.arange(len(anglist))
        for i, ang in enumerate(anglist):
            try:
                angarray[i] = int(ang)
            except ValueError:
                print 'The angles text list contains an invalid entry'

        return angarray


    def set_angles(self):
        """Sets the default angles"""

        self.anglesList.setPlainText(self.defaultangles)


if __name__=='__main__':
    import sys
    app = QApplication(sys.argv)
    form = LineProfileDialog('test standalone')
    form.show()
    app.exec_()