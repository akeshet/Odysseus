"""A plugin for running texreport. This does checks on the temperature fit.

"""


import texreport
import imageio
import imageprocess
from pluginmanager import IPlugin


class TexreportPlugin(IPlugin):
    """The plugin class. This one does not need a dialog window."""

    def create_window(self, img, roi, name):
        """A misnomer, but this is what the function Odysseus calls.

        **Inputs**

          * img: 2d-array, containing the image data
          * roi: tuple of slices, contains two slice objects, one for each
                 image axis. The tuple can be used as a 2D slice object.
          * name: string, the name of the plugin

        """

        rawframes = imageio.import_rawframes(self.imgpath)
        transimg, odimg = imageprocess.calc_absimage(rawframes)
        # set the ROI
        transimg = transimg[roi]

        texreport.generate_report(rawframes, transimg, self.imgpath, showpdf=False)

        # no window, so return None
        return None





