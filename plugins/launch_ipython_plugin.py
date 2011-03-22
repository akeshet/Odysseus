import os
import platform
import tempfile
import numpy as np

from pluginmanager import IPlugin


class IpythonLaunchPlugin(IPlugin):
    """Launches an IPython window with the image data loaded"""

    def create_window(self, img, roi, name):
        """This is called by Odysseus"""

        tmpdir = tempfile.gettempdir()
        tmpimg = os.path.join(tmpdir, 'tempimg.npy')
        tmpfile = os.path.join(tmpdir, 'templaunchfile.py')

        np.save(tmpimg, img)
        pyfile = file(tmpfile, 'w')
        pyfile.write('from scipy import *' + '\n' + \
                     'img=load("%s")'%tmpimg)
        pyfile.close()

        if platform.system()=='Windows':
            # maybe 'start' works better?
            cmd = "cmd /K ipython %s"%tmpfile
        else:
            cmd = "konsole --workdir %s -e ipython -pylab %s"%(tmpdir, tmpfile)

        os.system(cmd)

