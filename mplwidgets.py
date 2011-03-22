import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as np
import scipy as sp
import scipy.stats
import matplotlib as mpl
from pylab import show, close
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.figure import Figure

from guihelpfuncs import coldict


class Cursors:
    HAND, POINTER, SELECT_REGION, MOVE = range(4)
cursors = Cursors()


class MyQTToolbar(NavigationToolbar2QT):
    """Slight modification to the standard MPL QT4 toolbal.

    toolitems is the list of buttons to add to the toolbar, the format is:
    key for actions dict, tooltip_text, image_file, callback, checkable

    """

    def _icon(self, name):
        if name.startswith(':/'):
            return QIcon(name)
        else:
            return QIcon(os.path.join(self.basedir, name))


    def _init_toolbar(self):
        self.basedir = os.path.join(mpl.rcParams['datapath'], 'images')


        toolitems = (
            ('Save', 'Save the figure','filesave.ppm', self.save_figure, False),
            None,
            ('Home', 'Reset original view', 'home.svg', self.home, False),
            ('Back', 'Back to  previous view','back.ppm', self.back, False),
            ('Forward', 'Forward to next view','forward.ppm', self.forward,
             False),
            ('ZOOM', 'Zoom to rectangle','zoom_to_rect.svg', self.zoom, True),
            None,
            ('Analysis ROI', 'Set analysis ROI', ':/roi_analysis.svg',
             self.set_roi, True),
            ('Ncount ROI', 'Set Ncount ROI', ':/roi_ncount.svg',
             self.set_roi, True),
            None,
            ('0-1.35', 'Set colormap limits to default (0 - 1.35)',
             ':/default_viewlimits.svg', self.setlims_0_135, False),
            ('5/95', 'Adjust contrast to 5/95', ':/five_ninetyfive.svg',
             self.setlims_5_95, False),
            ('set colormap lims', 'Set colormap limits',
             ':/viewlimits_popup.svg', self.setlims_withdialog, False))

        self.actions = {}
        for item in toolitems:
            if item is not None:
                action = self.addAction(self._icon(item[2]), item[0], item[3])
                action.setToolTip(item[1])
                action.setCheckable(item[4])
                self.actions[item[0]] = action
            else:
                self.addSeparator()

        # drop-down menu to remove ROIs
        self.roimenu_analysis = QMenu()
        self.roimenu_analysis.addAction("Remove analysis ROI", self.clear_roi)
        self.actions['Analysis ROI'].setMenu(self.roimenu_analysis)
        self.roimenu_ncount = QMenu()
        self.roimenu_ncount.addAction("Remove ncount ROI", self.clear_roi)
        self.actions['Ncount ROI'].setMenu(self.roimenu_ncount)

        self.colmapCtrl = QComboBox()
        for cmap in self.canvas.colmaps.keys():
            self.colmapCtrl.addItem(cmap)
        self.colmapCtrl.setCurrentIndex(self.colmapCtrl.findText('gray'))
        self.addWidget(self.colmapCtrl)
        self.addSeparator()

        # names of actions that activate left-button dragging (only one active)
        self._activenames = ['ZOOM', 'Analysis ROI', 'Ncount ROI']
        # set ZOOM to be the active button at startup
        self.zoom()

        # Add the x,y location widget at the right side of the toolbar
        if self.coordinates:
            self.locLabel = QLabel( "", self )
            self.locLabel.setAlignment(Qt.AlignRight | Qt.AlignTop )
            self.locLabel.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                                    QSizePolicy.Ignored))
            labelAction = self.addWidget(self.locLabel)
            labelAction.setVisible(True)
        self.setMaximumWidth(self.canvas.width())

        self._make_connections()


    def _make_connections(self):
        """Make Qt signal-slot connections. Called at the end if _init."""

        self.connect(self.colmapCtrl, SIGNAL("currentIndexChanged(QString)"),
                     self.updateColormap)
        self.connect(self.canvas, SIGNAL("SizeChange"),
                     self.adjust_width)


    def _set_active(self, name_pressed):
        """Control behavior of buttons in self._activenames.

        If a button is activated, deactivate the others. If the active button
        is pressed, deactivate all.
        """
        if self._active == name_pressed:
            self._active = None
            self.actions[name_pressed].setChecked(False)
        else:
            self._active = name_pressed
            self.actions[name_pressed].setChecked(True)
            for name in self._activenames:
                if not name == name_pressed:
                    self.actions[name].setChecked(False)


    def zoom(self, *args):
        """Activate zoom to rect mode"""

        self._set_active('ZOOM')

        if self._idPress is not None:
            self._idPress = self.canvas.mpl_disconnect(self._idPress)

        if self._idRelease is not None:
            self._idRelease = self.canvas.mpl_disconnect(self._idRelease)

        if  self._active:
            self._idPress = self.canvas.mpl_connect('button_press_event',
                                                    self.press_zoom)
            self._idRelease = self.canvas.mpl_connect('button_release_event',
                                                      self.release_zoom)
            self.canvas.widgetlock(self)
        else:
            self.canvas.widgetlock.release(self)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self._active)


    def mouse_move(self, event):
        """copied from MPL backend_bases.py and modified"""
        if not event.inaxes or not self._active:
            if self._lastCursor != cursors.POINTER:
                self.set_cursor(cursors.POINTER)
                self._lastCursor = cursors.POINTER
        else:
            if self._active in self._activenames:
                if self._lastCursor != cursors.SELECT_REGION:
                    self.set_cursor(cursors.SELECT_REGION)
                    self._lastCursor = cursors.SELECT_REGION
                if self._xypress:
                    x, y = event.x, event.y
                    lastx, lasty, a, ind, lim, trans= self._xypress[0]
                    self.draw_rubberband(event, x, y, lastx, lasty)

        if event.inaxes and event.inaxes.get_navigate():
            try:
                x = int(event.xdata)
                y = int(event.ydata)
                if isinstance(self.canvas, SingleImageCanvas):
                    dataval = self.canvas.img[y, x, self.canvas.rawdata_index]
                else:
                    dataval = 0.0
                msg = '(X; Y)=(%s; %s) ;  I=%1.2f'%(x, y, dataval)
                self.set_message(msg)
            except ValueError:
                pass
            except OverflowError:
                pass


    def adjust_width(self):
        """Change the maximum width of the toolbar if canvas size changes"""
        self.setMaximumWidth(self.canvas.width())


    def set_roi(self, *args):
        """Activate set ROI mode"""
        if self.sender() is self.actions['Analysis ROI']:
            roiname = 'Analysis ROI'
        elif self.sender() is self.actions['Ncount ROI']:
            roiname = 'Ncount ROI'
        self._set_active(roiname)

        if self._idPress is not None:
            self._idPress = self.canvas.mpl_disconnect(self._idPress)

        if self._idRelease is not None:
            self._idRelease = self.canvas.mpl_disconnect(self._idRelease)

        if  self._active:
            self._idPress = self.canvas.mpl_connect('button_press_event',
                                                    self.press_roi)
            self._idRelease = self.canvas.mpl_connect('button_release_event',
                                                      self.release_roi)
            self.canvas.widgetlock(self)
        else:
            self.canvas.widgetlock.release(self)


    def clear_roi(self):
        """Clears the ROI box for the respective button"""
        if self.sender().text() == 'Remove analysis ROI':
            self.canvas.clearROI('analysis')
        elif self.sender().text() == 'Remove ncount ROI':
            self.canvas.clearROI('ncount')


    def press_roi(self, event):
        """The press mouse button in set ROI mode callback"""
        if event.button == 1:
            self._button_pressed = 1
        else:
            self._button_pressed = None
            return

        x, y = event.x, event.y
        self._xypress = []
        for i, a in enumerate(self.canvas.figure.get_axes()):
            if x is not None and y is not None and a.in_axes(event):
                self._xypress.append((x, y, a, i, a.viewLim.frozen(),
                                      a.transData.frozen()))


    def release_roi(self, event):
        """The release mouse button in set ROI mode callback"""
        if not self._xypress:
            return

        for cur_xypress in self._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, ind, lim, trans = cur_xypress

            # ignore singular clicks; 5 pixels is a threshold
            if abs(x - lastx) < 5 or abs(y - lasty) < 5:
                self._xypress = None
                self.draw()
                return

            # get ROI coordinates
            inverse = a.transData.inverted()
            lastx, lasty = inverse.transform_point( (lastx, lasty) )
            x, y = inverse.transform_point( (x, y) )
            Xmin, Xmax = a.get_xlim()
            Ymin, Ymax = a.get_ylim()

            # put coordinates in the correct order
            if Xmin < Xmax:
                if x < lastx:
                    x0, x1 = x, lastx
                else:
                    x0, x1 = lastx, x
                if x0 < Xmin:
                    x0 = Xmin
                if x1 > Xmax:
                    x1 = Xmax
            else:
                if x > lastx:
                    x0, x1 = x, lastx
                else:
                    x0, x1 = lastx, x
                if x0 > Xmin:
                    x0 = Xmin
                if x1 < Xmax:
                    x1 = Xmax

            if Ymin < Ymax:
                if y < lasty:
                    y0, y1 = y, lasty
                else:
                    y0, y1 = lasty, y
                if y0 < Ymin:
                    y0 = Ymin
                if y1 > Ymax:
                    y1 = Ymax
            else:
                if y > lasty:
                    y0, y1 = y, lasty
                else:
                    y0, y1 = lasty, y
                if y0 > Ymin:
                    y0 = Ymin
                if y1 < Ymax:
                    y1=Ymax

            roi = np.array([x0, x1, y1, y0], dtype=np.int32)
            if self._active == 'Analysis ROI':
                self.canvas.rois['analysis'] = roi
                self.canvas.drawROI('analysis')
            elif self._active == 'Ncount ROI':
                self.canvas.rois['ncount'] = roi
                self.canvas.drawROI('ncount')
            else:
                pass

        self.draw()
        self._xypress = None
        self._button_pressed = None


    def updateColormap(self, cmap):
        """Updates the colormap of the image."""

        self.canvas.set_colormap(str(cmap))


    def setlims_0_135(self):
        """Set the colormap limits to 5/95th percentiles."""

        if self.canvas.rawdata_index == 0:
            self.canvas.set_viewlimits(0, 1.35)
        else:
            self.canvas.set_viewlimits(None, None)
        self.canvas.draw()


    def setlims_5_95(self):
        """Set the colormap limits to 5/95th percentiles."""

        displayed_img = self.canvas.img[:, :, self.canvas.rawdata_index].flat
        vmin = sp.stats.scoreatpercentile(displayed_img, 5)
        vmax = sp.stats.scoreatpercentile(displayed_img, 95)
        self.canvas.set_viewlimits(vmin, vmax)
        self.canvas.draw()


    def setlims_withdialog(self):
        """Pops up dialog boxes to ask the user for vmin, vmax colormaps lims"""
        vmin, success = QInputDialog.getDouble(self, 'Set colormap limits',
                                               'Enter vmin',
                                               0.00, 0.00, 2147483647, 2)
        if success:
            vmax, success = QInputDialog.getDouble(self, 'Set colormap limits',
                                               'Enter vmax',
                                               1.35, vmin, 2147483647, 2)
            if success:
                self.canvas.set_viewlimits(vmin, vmax)
                self.canvas.draw()


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, img=np.ones((576, 384))*1.2, \
        width=3, aspect=576/384.):
        """width is in inches"""

        height = width*aspect
        self.aspect = aspect
        self.img = img
        # imgsize is used to check if the shape has changed, see shapechange()
        self.imgsize = self.img.shape
        self.datafilepath = None

        # roi is defined as [x0, x1, y0, y1]
        self.rois = {'ncount':None, 'analysis':None}
        self.roiboxes = {'ncount':None, 'analysis':None}
        self.roicols = {'ncount':coldict['purple'], 'analysis':coldict['blue']}
        self.marker = None
        self.markerlines = None
        self.colmaps = {'gray':mpl.cm.gray, 'copper':mpl.cm.copper,
                        'hot':mpl.cm.hot, 'jet':mpl.cm.jet,
                        'spectral':mpl.cm.spectral, 'earth':mpl.cm.gist_earth}

        mpl.pyplot.rc('figure.subplot', left=1e-3)
        mpl.pyplot.rc('figure.subplot', bottom=1e-3)
        mpl.pyplot.rc('figure.subplot', right=1-1e-3)
        mpl.pyplot.rc('figure.subplot', top=1-1e-3)
        mpl.pyplot.rc('figure', fc=coldict['bgcolor'], ec=coldict['bgcolor'])
        mpl.pyplot.rc('axes', fc=coldict['bgcolor'])
        mpl.pyplot.rc('axes', lw=0.5)
        mpl.pyplot.rc('axes', labelsize=10)
        mpl.pyplot.rc('xtick', labelsize=8)
        mpl.pyplot.rc('ytick', labelsize=8)

        self.fig = Figure(figsize=(width, height))
        self.ax = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.ax.hold(False)

        self.init_figure()
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, \
                QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.setMinimumSize(200, 200)
        self.setFocusPolicy(Qt.ClickFocus)


    def sizeHint(self):
        w, h = self.get_width_height()
        return QSize(w, round(w*self.aspect))


    def heightForWidth(self, width):
        """reimplemented from QWidget to ensure we have constant aspect ratio"""

        return round(width*self.aspect)


class SingleImageCanvas(MyMplCanvas):
    """Holds a single absorption image in an MPL figure."""

    def __init__(self, parent=None, img=np.ones((576, 384, 4))*1.2, \
        width=1.5, aspect=576/384.):
        """add index for raw data frames pwa, pwoa, df."""

        self.rawdata_index = 0
        self.cmap = mpl.cm.gray  # holds the current colormap
        self.hsizelims = (200, 800)
        self.vsizelims = (200, 600)

        super(SingleImageCanvas, self).__init__(parent, img=img, width=width)
        self.resize(img.shape[1], img.shape[0])


    def init_figure(self, vmin=0, vmax=1.35):
        """Generate a single image object and ROIs, markers, etc"""

        rawimage = self.img[:, :, self.rawdata_index]
        if self.rawdata_index==0:
            self.imobject = self.ax.imshow(rawimage, cmap=self.cmap,
                                           vmin=vmin, vmax=vmax,
                                           interpolation='nearest')
        else:
            self.imobject = self.ax.imshow(rawimage, cmap=self.cmap,
                                           interpolation='nearest')
        self.ax.set_xticks([])
        self.ax.set_yticks([])


    def update_img(self):
        """Redraws the image, but leaves zoom, cursor etc unchanged."""

        self.imobject.set_array(self.img[:, :, self.rawdata_index])
        if not self.img.shape==self.imgsize:
            self.shapechange()
        self.fig.canvas.draw()


    def set_viewlimits(self, vmin, vmax):
        """"""

        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
        self.imobject.set_norm(norm)


    def set_colormap(self, cmap='gray'):
        """Set the colormap of the image and draw it."""

        self.cmap = self.colmaps[cmap]
        self.imobject.set_cmap(self.cmap)
        self.figure.canvas.draw()


    def shapechange(self):
        """If the image has a different shape, update the widget geometry"""

        self.imgsize = self.img.shape
        imsize = self.imgsize

        def check_sizelims(vhsize, sizelims):
            """vhsize is the current size of the dimension to check, sizelims
            a two-element tuple (min,max). Return True if imsize is within
            lims, False otherwise.
            """
            if vhsize < sizelims[0] or vhsize > sizelims[1]:
                return False
            else:
                return True

        def find_scalefactor(vhsize, sizelims):
            """Return scale factor needed to get the size within given limits"""
            if vhsize < sizelims[0]:
                scale = np.ceil(sizelims[0] / float(vhsize))
            elif vhsize > sizelims[1]:
                scale = 1. / np.ceil(float(vhsize) / sizelims[1])
            else:
                scale = 1
            return scale


        hscale = find_scalefactor(imsize[1], self.hsizelims)
        if check_sizelims(imsize[0]*hscale, self.vsizelims):
            hsize = round(imsize[1] * hscale)
            vsize = round(imsize[0] * hscale)
        else:
            vscale = find_scalefactor(imsize[0], self.vsizelims)
            if check_sizelims(imsize[1]*vscale, self.hsizelims):
                hsize = round(imsize[1] * vscale)
                vsize = round(imsize[0] * vscale)
            else:
                # no common scale factor works, scale each dimension separately
                hsize = round(imsize[1] * hscale)
                vsize = round(imsize[0] * vscale)

        self.aspect = float(vsize) / hsize
        self.resize(hsize, vsize)
        self.updateGeometry()
        self.emit(SIGNAL("SizeChange"))

        # now do all the redrawing (we do not draw ROIs and marker)
        for key in self.rois.keys():
            self.clearROI(key)
            self.clearMarker()
        self.init_figure()


    def mousePressEvent(self, event):
        """Left-click is handled by MPL, right-click not."""

        x = event.pos().x()
        # flipy so y=0 is bottom of canvas
        y = self.figure.bbox.height - event.pos().y()

        if event.button()==1:
            button = self.buttond[event.button()]
            FigureCanvasBase.button_press_event( self, x, y, button )
        else:
            if event.button()==2:
                try:
                    xdata, ydata = self.ax.transData.inverted().\
                         transform_point((x, y))
                except ValueError:
                    xdata  = None
                    ydata  = None
                self.marker = [int(xdata), int(ydata)]
                self.drawMarker()


    def drawROI(self, roi_id):
        """roi_id is a string, specifying the key for the rois dictionaries"""

        if self.rois[roi_id] is not None:
            if self.roiboxes[roi_id]:
                self.roiboxes[roi_id].remove()
            roi = self.rois[roi_id]
            poly = mpl.patches.Polygon(((roi[0], roi[2]),
                                        (roi[1], roi[2]),
                                        (roi[1], roi[3]),
                                        (roi[0], roi[3])),
                                       ec=self.roicols[roi_id], fc='none',
                                       lw=0.5)
            self.ax.add_patch(poly)
            self.roiboxes[roi_id] = poly

            self.fig.canvas.draw()


    def clearROI(self, roi_id):
        """roi_id is a string, specifying the key for the rois dictionaries"""

        if self.rois[roi_id] is not None:
            if self.roiboxes[roi_id]:
                self.roiboxes[roi_id].remove()
                self.roiboxes[roi_id] = None

                self.fig.canvas.draw()
                self.rois[roi_id] = None


    def drawMarker(self, col=coldict['lightblue']):
        """Draws a cross at the point where the user left-clicked"""

        if self.marker:
            xx, yy = self.marker

            if self.markerlines:
                marker_hline, marker_vline = self.markerlines
                hpoints = marker_hline.get_ydata().size
                marker_hline.set_ydata(np.ones(hpoints)*yy)
                vpoints = marker_hline.get_xdata().size
                marker_vline.set_xdata(np.ones(vpoints)*xx)
            else:
                self.ax.hold(True)
                marker_hline = self.ax.axhline(yy, color=col)
                marker_vline = self.ax.axvline(xx, color=col)
                self.ax.hold(False)
                self.markerlines = [marker_hline, marker_vline]

            self.fig.canvas.draw()

            msg = '(X, Y)=(%s, %s) ;  I=%1.2f'\
                %(xx, yy, self.img[yy, xx, self.rawdata_index])
            self.emit(SIGNAL("MarkerPixval"), msg)


    def clearMarker(self):
        """Clears the marker and marker label"""

        self.marker = None
        if self.markerlines:
            for line in self.markerlines:
                line.remove()
            self.markerlines = None

        self.fig.canvas.draw()
        self.emit(SIGNAL("MarkerPixval"), "")


    def keyPressEvent(self, event):
        """Move marker with arrows on the keyboard"""

        if self.marker:
            if event.matches(QKeySequence.MoveToNextChar):
                try:
                    if self.marker[0] < self.img.shape[1] - 1:
                        self.marker[0] += 1
                        self.drawMarker()
                except IndexError:
                    pass
            elif event.matches(QKeySequence.MoveToPreviousChar):
                try:
                    if self.marker[0] > 0:
                        self.marker[0] -= 1
                        self.drawMarker()
                except IndexError:
                    pass
            elif event.matches(QKeySequence.MoveToNextLine):
                try:
                    if self.marker[1] < self.img.shape[0] - 1:
                        self.marker[1] += 1
                        self.drawMarker()
                except IndexError:
                    pass
            elif event.matches(QKeySequence.MoveToPreviousLine):
                try:
                    if self.marker[1] > 0:
                        self.marker[1] -= 1
                        self.drawMarker()
                except IndexError:
                    pass
            else:
                event.ignore()
        else:
            event.ignore()


    def getImgROI(self, roi_id='analysis'):
        """Returns the image data within the ROI as a 2D array

        roiname is string with value 'ncount' or 'analysis'

        """

        roi = self.rois[roi_id]
        if roi is not None:
            # roi is [x0, x1, y0, y1], where x is the second index of img
            imgroi = self.img[roi[2]:roi[3], roi[0]:roi[1], 0]
        else:
            imgroi = self.img[:, :, 0]

        return imgroi, roi


class InfoPlotCanvas(MyMplCanvas):
    """Displays the results of the image fitting"""

    def __init__(self, parent=None, figsize=(6,4), dpi=100):
        """figsize is in inches"""

        mpl.pyplot.rc('figure.subplot', left=0.15)
        mpl.pyplot.rc('figure.subplot', bottom=0.15)
        mpl.pyplot.rc('figure.subplot', right=0.95)
        mpl.pyplot.rc('figure.subplot', top=0.95)

        self.fig = Figure(figsize=figsize, dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.ax.hold(False)
        self.compute_figure()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, \
                    QSizePolicy.Preferred, QSizePolicy.Preferred)
        FigureCanvas.updateGeometry(self)
        self.setMinimumSize(150, 100)
        self.setMaximumSize(400, 266)


    def sizeHint(self):
        w, h = self.get_width_height()
        return QSize(w, h)


    def compute_figure(self):
        """Plot the fit"""

        self.ax.set_xlabel(r'$r$ [pix]')
        self.ax.set_ylabel(r'$OD$')


class PngWidget(QWidget):
    """The widget for the image history"""

    def __init__(self, pngimg, datapath, ncount, gridindex=0, parent=None):
        """pngimg is the full path to the .png file, datapath to the raw data"""
        super(PngWidget, self).__init__(parent)

        self.imgpath = pngimg
        self.datapath = datapath
        self.index = int(gridindex)
        self.img = QLabel()
        self.img.setPixmap(QPixmap(pngimg))
        self.ncount = QLabel()
        if ncount:
            self.ncount.setText('N = %1.1fk'%(ncount*1e-3))
        else:
            self.ncount.clear()

        self.ncount.setFrameStyle(QFrame.StyledPanel)
        pngbox = QVBoxLayout()
        pngbox.addStretch()
        pngbox.addWidget(self.img)
        pngbox.addWidget(self.ncount)
        pngbox.addSpacing(8)
        self.setLayout(pngbox)


    def update(self, pngimg, datapath, ncount):
        self.imgpath = pngimg
        self.datapath = datapath
        if pngimg:
            imgname = os.path.split(pngimg)[1][:-4]
            self.img.setToolTip(imgname)
            self.img.setPixmap(QPixmap(pngimg))
            self.ncount.setText('N = %1.2fm'%(ncount*1e-6))


    def mousePressEvent(self,event):
        """Left-click loads image in rawImage, right-click does plugins"""

        pngdir, imgname = os.path.split(self.imgpath)
        # catch left click on non-blank images
        if event.button()==1 and not imgname=='blankimg.png':
            self.emit(SIGNAL("updateAbsImage"), self.index)

        # catch right click on non-blank images
        if event.button()==2 and not imgname=='blankimg.png':
            # construct path to tiff image
            tiffname = imgname.replace('.png', '.TIF')
            tiffdir = os.path.split(pngdir)[0]
            tiffpath = os.path.join(tiffdir, tiffname)
            #display menu
            self.emit(SIGNAL("displayPluginMenu"), self.index, tiffpath)


def save_png(img, path, fname, hsize=1.5, vmin=0., vmax=1.35):
    """Save an image as a png file

    **Inputs**

      * img: 2D array, usually the transmission image
      * path: str, the directory above the one where the png image will be saved
      * fname: str, the desired filename, with or without extension

    **Outputs**

      * pngpath: str, the complete path to the generated png file

    """

    path = str(path)
    fname = str(fname)
    pngdir = os.path.join(path, 'png')
    try:
        os.mkdir(pngdir)
    except OSError:
        # if png directory already exists, do nothing
        pass

    aspect = float(img.shape[0])/img.shape[1]
    mpl.pyplot.rc('figure.subplot', left=1e-3)
    mpl.pyplot.rc('figure.subplot', bottom=1e-3)
    mpl.pyplot.rc('figure.subplot', right=1-1e-3)
    mpl.pyplot.rc('figure.subplot', top=1-1e-3)

    maxvsize = 2.2
    if aspect < maxvsize:
        fig = Figure(figsize=(hsize, hsize*aspect))
    else:
        fig = Figure(figsize=(maxvsize/aspect, maxvsize))
    canvas = FigureCanvas(fig)

    ax = fig.add_subplot(111)
    ax.imshow(img, cmap=mpl.cm.gray, vmin=vmin, vmax=vmax)
    ax.set_xticks([])
    ax.set_yticks([])

    fname = os.path.splitext(fname)[0] + '.png'
    pngpath = os.path.join(pngdir, fname)
    fig.savefig(pngpath)
    close(fig)

    return pngpath


class BlankCanvas(FigureCanvas):
    """Initialize a blank image, to be used in popup plugins etc.

    Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.).

    """

    def __init__(self, parent=None):
        """width is in inches"""

        self.fig = Figure(figsize=(6, 4))
        self.ax = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, \
                QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class BlankCanvasWithToolbar(FigureCanvas):
    """Initialize a blank image, to be used in popup plugins etc.

    Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.).

    """

    def __init__(self, parent=None):
        """width is in inches"""

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)