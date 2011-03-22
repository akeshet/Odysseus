#!/usr/bin/env python
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License.
# See the GNU General Public License for more details.


import sys
import os
import time
import platform
import glob
import cgitb # html formatting of tracebacks
import webbrowser

import numpy as np
import matplotlib as mpl
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import dirmonitor
from imageprocess import calc_absimage
import imageio
import filetools
from fitfermions import fit_img, find_ellipticity
import qrcresources
import pluginmanager
import importsettings
from mplwidgets import *
from guihelpfuncs import *


__version__ = "0.6.0"
cgitb.enable(display=0, logdir='logs', context=1)


class Fitter(QThread):
    """This class runs the fitting routines. This keeps the GUI responsive."""

    def __init__(self, img, pixcal, parent=None):
        super(Fitter, self).__init__(parent)
        self.img = img
        self.pixcal = pixcal
        self.func = 'idealfermi'
        self.check_ellipse = False


    def run(self):
        """Is called by QThread.start(), when returning stops complete thread"""

        try:
            if self.check_ellipse:
                elliptic = (find_ellipticity(self.img), 0)
            else:
                elliptic = None

            fitresult = fit_img(self.img, showfig=False, full_output='odysseus',
                                fitfunc=self.func, elliptic=elliptic,
                                pixcal=self.pixcal)
            self.emit(SIGNAL("fitresult"), fitresult)

        except ValueError:
            failmsg = 'Fitting failed - is the analysis ROI set correctly?'
            self.emit(SIGNAL("fitresult"), failmsg)


class GuiFitfuncs(object):
    def __init__(self, com, numatoms, temp, cloudsize):
        """Create reference to gui info boxes, and fit function dict.

        All fit functions that are available should be added to self.funcs,
        they will then automatically show up in the GUI. The fit function is
        defined here, of course the fitting is done in fitfermions.py. In
        that file fit_img and do_fit should be modified so the return values
        make sense.

        """

        self.com = com
        self.numatoms = numatoms
        self.temp = temp
        self.cloudsize = cloudsize
        self.roi = None
        self.txtfilename = None

        self.funcs = [{'name':'idealfermi', 'desc':'ideal Fermi gas',
                       'func':self.idealfermi},
                      {'name':'gaussian', 'desc':'Gaussian',
                       'func':self.gaussian},
                      {'name':'idealfermi_err', 'desc': 'ideal Fermi errorbar',
                       'func':self.idealfermi_err}]
        self.current_func = None
        self.current_datafilename = None


    def idealfermi(self, fig, fitresult):
        """Plot the OD and fitted profiles for fit with ideal Fermi gas"""

        ToverTF, N, com, fitparams, rcoord, od_prof, fit_prof = fitresult

        fig.ax.plot(rcoord, od_prof, 'k', lw=0.75)
        fig.ax.hold(True)
        fig.ax.plot(rcoord, fit_prof, '#FFAF7A', lw=1)
        fig.ax.hold(False)
        fig.ax.set_xlabel(r'$r$ [pix]')
        fig.ax.set_ylabel(r'$OD$')
        fig.draw()

        try:
            self._update_infoboxes(com, N, ToverTF, fitparams[2])
        except TypeError:
            pass


    def gaussian(self, fig, fitresult):
        """Plot the OD and fitted profiles for fit with a Gaussian"""

        ToverTF, N, com, fitparams, rcoord, od_prof, fit_prof = fitresult

        fig.ax.plot(rcoord, od_prof, 'k', lw=0.75)
        fig.ax.hold(True)
        fig.ax.plot(rcoord, fit_prof, '#FFAF7A', lw=1)
        fig.ax.hold(False)
        fig.ax.set_xlabel(r'$r$ [pix]')
        fig.ax.set_ylabel(r'$OD$')
        fig.draw()

        try:
            self._update_infoboxes(com, N, ToverTF, fitparams[1])
        except TypeError:
            pass


    def idealfermi_err(self, fig, fitresult):
        """Plot OD fitted and err profiles for fit with ideal Fermi gas"""

        ToverTF, N, com, fitparams, rcoord, od_prof, fit_prof, errprof_plus, \
               errprof_min = fitresult

        fig.ax.plot(rcoord, od_prof, 'k', lw=0.75)
        fig.ax.hold(True)
        fig.ax.plot(rcoord, fit_prof, '#FFAF7A', lw=1)
        fig.ax.plot(rcoord, errprof_plus, '#FFAF7A', lw=0.75, ls='--')
        fig.ax.plot(rcoord, errprof_min, '#FFAF7A', lw=0.75, ls='--')
        fig.ax.hold(False)
        fig.ax.set_xlabel(r'$r$ [pix]')
        fig.ax.set_ylabel(r'$OD$')
        fig.draw()

        try:
            self._update_infoboxes(com, N, ToverTF, fitparams[0][2])
        except TypeError:
            pass


    def _update_infoboxes(self, com, N, ToverTF, cloudsize):
        com = (com[1] + self.roi[0], com[0] + self.roi[2]) # inverted axes crap
        self.com.setText('(%1.1f, %1.1f)'%(com[0], com[1]))
        self.numatoms.setText('%1.2f million'%(N*1e-6))
        self.temp.setText('%1.2f T/T_F'%ToverTF)
        self.cloudsize.setText('%1.1f'%cloudsize)

        self._result_to_textfile(N, ToverTF)


    def _result_to_textfile(self, N, ToverTF):
        """Writes the fit result to a text file, to log results"""
        try:
            f = open(self.txtfilename, mode='a')
        except TypeError:
            return
        try:
            timestr = time.strftime('%H:%M:%S')
            fname = os.path.split(self.current_datafilename)[1]
            f.write('%1.3f    %1.3f    %s    %s\n'%(N*1e-6, ToverTF,
                                                    timestr, fname))
        finally:
            f.close()


class CentralWidget(QWidget):

    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)

        # initialize data structures
        self.img_list = []
        self.ncount = []
        self.pnglist = []
        self.datafilelist = []
        self.importdict = importsettings.image_import_dict

        self.pathLabel, pathLayout = create_labeledbox('Monitoring path:',
                                                       stretch=1)
        self.pathButton = QPushButton("&Set Path...")
        pathLayout.addWidget(self.pathButton)

        # central image view
        self.absImage = SingleImageCanvas()
        self.absImage.setCursor(Qt.CrossCursor)
        # label with data for crosshair marker
        self.absMarker = ImageMarker()
        palette3 = QPalette()
        palette3.setColor(QPalette.WindowText,
                          QColor.fromRgb(*coldict_rgb['lightblue']))
        self.absMarker.setPalette(palette3)
        # add toolbar
        toolbar = MyQTToolbar(self.absImage, self)

        ## the info widget ##
        # center of mass
        self.com, comLayout = create_labeledbox('Center of mass:')
        # cloud size
        self.cloudsize, cloudsizeLayout = create_labeledbox('Cloud size [pix]:')
        # number of atoms
        self.numatoms, numatomsLayout = create_labeledbox('Number of atoms:')
        # temperature
        self.temp, tempLayout = create_labeledbox('Temperature:')

        # fit controls
        self.ellipseCalc = QCheckBox('Calc ellipticity')
        self.autoFit = QCheckBox('Autofit')
        self.guifitfuncs = GuiFitfuncs(self.com, self.numatoms, self.temp,
                                       self.cloudsize)
        self.fitFunc = QComboBox()
        for fitfunc in self.guifitfuncs.funcs:
            self.fitFunc.addItem(fitfunc['desc'])
        self.fitForceButton = QPushButton('Fit now')
        # the figure
        self.plotFigure = InfoPlotCanvas()
        toolbar2 = NavigationToolbar2QT(self.plotFigure, self)

        # infobox layouts
        fitinfoLayout = QVBoxLayout()
        fitinfoLayout.addLayout(comLayout)
        fitinfoLayout.addLayout(cloudsizeLayout)
        fitinfoLayout.addLayout(numatomsLayout)
        fitinfoLayout.addLayout(tempLayout)

        fitLayout = QVBoxLayout()
        fitLayout.addWidget(self.ellipseCalc)
        fitLayout.addWidget(self.autoFit)
        fitLayout.addWidget(self.fitFunc)
        fitLayout.addWidget(self.fitForceButton)

        infoLayout = QVBoxLayout()
        infoLayout.addWidget(self.plotFigure)
        infoLayout.addWidget(toolbar2)

        ctrlboxLayout = QVBoxLayout()
        ctrlboxLayout.addStretch()
        ctrlboxLayout.addLayout(fitLayout)
        ctrlboxLayout.addLayout(fitinfoLayout)
        ctrlboxLayout.addLayout(infoLayout)

        self.infobox = QGroupBox('Current Image Info')
        self.infobox.setLayout(ctrlboxLayout)

        # all the other layout stuff #
        absLayout = QVBoxLayout()
        self.absLabel = QLabel('Current image')
        self.cycleButton = QPushButton('+')
        absTopLayout = QHBoxLayout()
        absTopLayout.addWidget(self.absLabel)
        absTopLayout.addStretch()
        absTopLayout.addWidget(self.absMarker)
        absTopLayout.addWidget(self.cycleButton)
        absLayout.addLayout(absTopLayout)
        absLayout.addWidget(self.absImage)
        absLayout.addWidget(toolbar)

        imageLayout = QHBoxLayout()
        imageLayout.addLayout(absLayout)
        imageLayout.addStretch()

        middleLayout = QVBoxLayout()
        middleLayout.addLayout(pathLayout)
        middleLayout.addLayout(imageLayout)
        middleLayout.addStretch()

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(middleLayout)
        mainLayout.addStretch()
        mainLayout.addWidget(self.infobox)

        # now add the image grid #
        self.gridImages = []
        self.gridnum = 8
        self.pngnum = 25
        self.bottomLayout = QHBoxLayout()
        # size constraint is necessary to ensure that the layout works well
        # with the scroll area
        self.bottomLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        for i in range(self.gridnum):
            self.gridImages.append(PngWidget(":/blankimg.png", None,
                                             0, gridindex=i))
            self.bottomLayout.addWidget(self.gridImages[i])

        self.gridImageWidget = QGroupBox('Recent image history')
        self.gridImageWidget.setLayout(self.bottomLayout)

        self.gridScrollArea = QScrollArea()
        self.gridScrollArea.setWidget(self.gridImageWidget)

        layout = QVBoxLayout()
        layout.addLayout(mainLayout, 1)
        layout.addWidget(self.gridScrollArea)
        self.setLayout(layout)


        self._make_connections()
        self.setMouseTracking(True)


    def _make_connections(self):
        """Make signal-slot connections. Called by __init__()"""

        self.connect(self.absMarker, SIGNAL("ClearMarker"),
                     self.absImage.clearMarker)
        self.connect(self.absImage, SIGNAL("MarkerPixval"),
                     self.updateMarkerval)
        self.connect(self.cycleButton, SIGNAL("clicked()"), self.cycleImages)
        self.connect(self.fitForceButton, SIGNAL("clicked()"), self.fitImage)
        self.connect(self.absImage, SIGNAL("SizeChange"), self.update)
        for png in self.gridImages:
            self.connect(png, SIGNAL("updateAbsImage"), self.updateAbsImage)


    def mouseMoveEvent(self, event):
        """Restores the normal cursor"""
        QApplication.restoreOverrideCursor()


    def load_imgs(self, path_or_list):
        """Loads as many images from path as fit in GUI."""

        if isinstance(path_or_list, list):
            imgs_sorted = filetools.sort_files_by_date(path_or_list,
                                                       newestfirst=True)
        else:
            imgs_sorted = filetools.get_files_in_dir(str(path_or_list))

        # load as much images as fit in the GUI, if possible
        self.numload = min(self.gridnum, len(imgs_sorted))
        imgs_newestlast = (imgs_sorted[:self.numload])
        imgs_newestlast.reverse()

        for num, fname in enumerate(imgs_newestlast):
            QApplication.processEvents() # update GUI, keep it responsive
            self.load_newimg(fname)
            self.emit(SIGNAL("updateProgressBar"), num+1)
        # make sure the progress bar is not stuck halfway
        self.emit(SIGNAL("updateProgressBar"), self.numload+1)

        if not imgs_sorted:
            msg =  "No suitable images found"
            self.emit(SIGNAL("updateStatusBar"), msg)


    def load_newimg(self, fpathname):
        """Loads new image from path"""

        fpathname = str(fpathname)  # convert QString to Python str if needed
        file_ext = os.path.splitext(fpathname)[1]
        if file_ext == '.TIF':
            #rawdata = imageio.imgimport_intelligent(fpathname)
            rawdata, transimg, odimg = importsettings.process_import(fpathname,
                                                        dct=self.importdict)
        elif file_ext == '.xraw0':
            rawdata = imageio.import_xcamera(fpathname)
        else:
            msg = 'File does not have a valid extension'
            self.emit(SIGNAL("updateStatusBar"), msg)

        if rawdata is not None:
            #transimg, odimg = calc_absimage(rawdata)
            pngname = save_png(transimg, *(os.path.split(fpathname)))

            if len(self.img_list) == self.gridnum:
                # remove last image from list if the list is full
                self.img_list.pop()
            if len(self.pnglist) == self.pngnum:
                # remove last png thumbnail from list if it is full
                self.ncount.pop()
                self.pnglist.pop()
                self.datafilelist.pop()

            img = np.zeros((rawdata.shape[0], rawdata.shape[1],
                            rawdata.shape[2]+1), dtype=np.float32)
            img[:, :, 0] = transimg
            img[:, :, 1:] = rawdata
            self.img_list.insert(0, img)
            roi = self.absImage.getImgROI('ncount')[1]
            if roi is not None:
                odimg = odimg[roi[2]:roi[3], roi[0]:roi[1]]
            self.ncount.insert(0, self.calc_ncount(odimg))
            self.pnglist.insert(0, pngname)
            self.datafilelist.insert(0, fpathname)
            self.numload = min(self.gridnum, len(self.img_list))
        else:
            msg = "Warning: TIF image does not contain 3 frames"
            self.emit(SIGNAL("updateStatusBar"), msg)


    def calc_ncount(self, odimg):
        """Calculates the number of atoms in the image"""

        sigma = 3*671e-9**2/(2*np.pi)
        return odimg.sum() * self.pixcal**2/sigma


    def display_imgs(self):
        """Updates the GUI with new images."""

        if self.img_list:
            self.absImage.img = self.img_list[0]
            self.absImage.datafilepath = self.datafilelist[0]
            self.absImage.update_img()
            if self.autoFit.isChecked():
                self.fitImage()
        try:
            # insert new PngWidget's to fill the grid
            while len(self.gridImages) < len(self.pnglist):
                idx = len(self.gridImages)
                self.gridImages.append(PngWidget(":/blankimg.png", None, 0,
                                                 gridindex=idx))
                self.bottomLayout.addWidget(self.gridImages[idx])
            for i in range(self.pngnum):
                self.gridImages[i].update(self.pnglist[i], self.datafilelist[i],
                                          self.ncount[i])
        except IndexError:
            # when there are no more images left to display, stop
            pass


    def updatePixval(self, text):
        """Updates the status bar of the image with the pixel value

        **Inputs**

          * text: string, this string gets written directly into label

        """

        self.absBar.setText(text)


    def updateMarkerval(self, text):
        """Updates the marker label with the new pixel coords and value"""

        self.absMarker.setText(text)


    def updateAbsImage(self, index):
        """Called when left-clicking on a grid image, reloads raw image"""

        try:
            self.absImage.img = self.img_list[index]
            self.absImage.datafilepath = self.datafilelist[index]
            self.absImage.update_img()
        except IndexError: # image itself not in memory anymore
            pass

    def cycleImages(self):
        """Cycle through the raw images"""

        if self.absImage.rawdata_index == self.absImage.img.shape[2]-1:
            self.absImage.rawdata_index = 0
            self.absImage.set_viewlimits(0, 1.35)
        else:
            self.absImage.rawdata_index += 1
            self.absImage.set_viewlimits(None, None)
        self.setAbsLabel()
        self.absImage.update_img()


    def setAbsLabel(self):
        """Set the image label"""

        #labels = ['Current image', 'Probe with atoms',
                  #'Probe without atoms', 'Dark field', 'Dark field 2',
                  #'Raw img 5', 'Raw img 6']
        if self.absImage.rawdata_index == 0:
            self.absLabel.setText('Current image')
        else:
            self.absLabel.setText('Frame %s'%(self.absImage.rawdata_index-1))


    def fitImage(self):
        """Takes care of fitting the current image and plotting the result"""

        self.fitForceButton.setText('Fitting...')

        img, roi = self.absImage.getImgROI('analysis')
        self.guifitfuncs.roi = roi
        self.guifitfuncs.current_datafilename = self.absImage.datafilepath
        self.fitobj = Fitter(img, self.pixcal)
        self.connect(self.fitobj, SIGNAL("fitresult"), self.plotFitImage)
        self.fitobj.check_ellipse = self.ellipseCalc.isChecked()

        func_idx = self.fitFunc.currentIndex()
        self.guifitfuncs.current_func = self.guifitfuncs.funcs[func_idx]['func']
        self.fitobj.func = self.guifitfuncs.funcs[func_idx]['name']

        self.fitobj.start()


    def plotFitImage(self, fitresults):
        """Plot the result of a fit after it has finished"""

        if isinstance(fitresults, str):
            # fit failed if fitresults is a string
            self.emit(SIGNAL("updateStatusBar"), fitresults)
        else:
            self.emit(SIGNAL("updateStatusBar"), 'Fitting succeeded')
            self.guifitfuncs.current_func(self.plotFigure, fitresults)

        self.fitForceButton.setText('Fit now')


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.lock = QReadWriteLock()


        self.cwidget = CentralWidget()
        self.setCentralWidget(self.cwidget)

        self.dirmonitor = dirmonitor.Walker(self.lock, self)
        self.connect(self.dirmonitor, SIGNAL("changed"), self.changed)

        self.connect(self.cwidget.pathButton, SIGNAL("clicked()"), self.setPath)

        # display status bar string for central widget
        self.connect(self.cwidget, SIGNAL("updateStatusBar"),
                     self.updateStatusBar)
        self.connect(self.cwidget, SIGNAL("updateProgressBar"),
                     self.updateProgressBar)
        for img in self.cwidget.gridImages:
            self.connect(img, SIGNAL("updateStatusBar"), self.updateStatusBar)
            self.connect(img, SIGNAL("displayPluginMenu"), self.displayPluginMenu)
        self.status = self.statusBar()
        self.progress = QProgressBar()
        self.progress.setRange(0, 9)
        self.progress.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.progress.setMinimumWidth(125)
        self.status.addPermanentWidget(self.progress)
        self.status.showMessage(\
            "Click the 'Set Path' button to start monitoring")

        # populate drop down menus
        self._populate_dropdown_menus()

        # restore state from previous session
        self._restore_state()

        # import plugin scripts
        plugindir = [os.path.join(sys.path[0], 'plugins')]
        self.plugin_manager = pluginmanager.PluginManager(directories_list=plugindir,\
                                            plugin_info_ext="odysseus-plugin")
        self.plugin_manager.collectPlugins()
        self.pluginwindowlist = []

        self.setWindowTitle("Odysseus - the cold atom viewer")


    def _restore_state(self):
        """Restore the state of the GUI from a previous session."""

        settings = QSettings('OdysseusGUI')
        self.path = QDir.toNativeSeparators(\
            settings.value("Path", QVariant(QDir.homePath())).toString())
        self.restoreGeometry(settings.value("Geometry").toByteArray())
        self.restoreState(settings.value("MainWindow/State").toByteArray())

        self.cwidget.ellipseCalc.setChecked(settings.value("EllipseCalc").toBool())
        self.cwidget.autoFit.setChecked(settings.value("AutoFit").toBool())
        self.cwidget.pixcal = settings.value("PixCal", QVariant(10e-6)).toDouble()[0]


    def _save_state(self):
        """Save the state of the GUI."""

        settings = QSettings('OdysseusGUI')
        settings.setValue("Path", QVariant(self.path))
        settings.setValue("Geometry", QVariant(self.saveGeometry()))
        settings.setValue("MainWindow/State", QVariant(self.saveState()))

        settings.setValue("EllipseCalc",
                          QVariant(self.cwidget.ellipseCalc.isChecked()))
        settings.setValue("AutoFit", QVariant(self.cwidget.autoFit.isChecked()))
        settings.setValue("PixCal", QVariant(self.cwidget.pixcal))


    def setPath(self):
        path = QFileDialog.getExistingDirectory(self,
                    "Choose a Path to Monitor and Display", self.path)
        if path.isEmpty():
            if self.dirmonitor.isRunning():
                self.status.showMessage("Continuing to monitor the same path,"\
                    "click the 'Set Path' button to alter path")
            else:
                self.status.showMessage(\
                    "Click the 'Set Path' button to start monitoring")
            return
        if self.dirmonitor.isRunning():
            self.dirmonitor.setWaiting(True)
        self.path = str(QDir.toNativeSeparators(path))
        self.cwidget.pathLabel.setText(self.path)
        self.status.clearMessage()

        # set log file
        self.cwidget.guifitfuncs.txtfilename = os.path.join(self.path,
                                                            'fitresults.txt')

        # load images from path into GUI
        self.cwidget.load_imgs(self.path)
        self.cwidget.display_imgs()

        # start monitoring for new images
        self.dirmonitor.setPath(self.path)
        if self.dirmonitor.isRunning():
            self.dirmonitor.setWaiting(False)
            self.status.showMessage("Monitoring resumed")
        else:
            self.dirmonitor.start()
            self.status.showMessage("Monitoring started")
        self.updateProgressBar(9)


    def changed(self, fnames):
        """Called when dir_monitor detects a change in TIF files

        fnames is a list of new files. If there is just one new file, it
        is loaded, if there is more than one all files get sorted again and
        reloaded.

        """

        # check to not detect the same image twice
        try:
            if self.cwidget.datafilelist[0] == fnames[0]:
                return
        except IndexError:
            pass

        try:
            self.updateProgressBar(0)
            if len(fnames) == 1:
                self.cwidget.load_newimg(fnames[0])
                self.cwidget.display_imgs()
                self.status.showMessage(\
                        ''.join(['Latest image: ', str(fnames[0])]))
                self.updateProgressBar(9)
            else:
                self.cwidget.load_imgs(self.path)
                self.cwidget.display_imgs()
                self.status.showMessage('Multiple new images loaded')
                self.updateProgressBar(9)
        except IOError:
            self.status.showMessage('Can not open image, maybe a permissions problem?')


    def updateStatusBar(self, msg):
        """Displays the string msg in the status bar"""

        self.status.showMessage(msg)


    def updateProgressBar(self, val):
        """Updates the progress bar, val should be integer in range (0, 9)"""

        if not self.progress.isVisible():
            self.status.addPermanentWidget(self.progress)
            self.progress.show()
        self.progress.setValue(val)
        if val == self.progress.maximum():
            QTimer.singleShot(8000, self.hideProgressBar)


    def hideProgressBar(self):
        """Hides the progress bar, used with timer"""

        # removeWidget is a badly named method, it just hides the widget
        self.status.removeWidget(self.progress)


    def fileOpen(self):
        """Open a raw image file and display as first image"""

        fnames = list(QFileDialog.getOpenFileNames(self,
                        "Odysseus - Choose Image", self.path,
                        "Raw image files (*.TIF);;XCamera image files (*.xraw0)"))
        if fnames:
            self.cwidget.load_imgs(fnames)
            self.cwidget.display_imgs()


    def fileSaveas(self):
        """Save a file in a format (.h5/ .npy/ .txt) selectable by extension"""

        fname = QFileDialog.getSaveFileName(self, \
                        "Save the image data as ... (default format is .h5)",
                        getattr(self, 'savedir', self.path),
                        "All supported files (*.h5 *.npy *.txt);;HDF5 files (*.h5);;Numpy binary files (*.npy);;ASCII text files (*.txt)")
        if fname:
            name, ext = os.path.splitext(str(fname))
            self.savedir, savefile = os.path.split(name)
            if not ext:
                ext = '.h5'
            imgdata = self.cwidget.absImage.img[:, :, 0]
            fname = ''.join([name, ext])

            if ext == '.h5':
                imageio.save_hdfimage(imgdata, fname)
            elif ext == '.npy':
                np.save(fname, imgdata)
            elif ext == '.txt':
                np.savetxt(fname, imgdata, fmt='%1.4f')


    def closeEvent(self, event=None):
        self.dirmonitor.setStopped()
        self._save_state()


    def setPixCal(self):
        """Pops up a dialog to specify the pixel calibration.

        Pixcal is set to m/pixel but specified in um/pixel.

        """

        pixcal, success = QInputDialog.getDouble(self, 'Set pixel calibration',
                                                 'Enter calibration in um/pix',
                                                 self.cwidget.pixcal*1e6,
                                                 0.01, 1e3, 2)
        if success:
            self.cwidget.pixcal = pixcal*1e-6
        else:
            popupbox = MaxsizeMessagebox.information(self, "Warning",
                                            "Setting pixel calibration failed")


    def showImportSettings(self):
        """Show the Image import settings dialog"""
        self.importdialog = importsettings.ImportSettingsDialog(self.cwidget.importdict)
        self.importdialog.show()


    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


    def _populate_dropdown_menus(self):
        """All the dropdown menu entries for the GUI, called by __init__()"""

        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                                           QKeySequence.Open, "fileopen",
                                           "Open an existing image file")
        fileSaveAction = self.createAction("&Save As...", self.fileSaveas,
                                           "Ctrl+S",
                                           "Save the image as ...")
        fileQuitAction = self.createAction("&Quit", self.close,
                "Ctrl+Q", "filequit", "Close the application")

        setPixCalAction = self.createAction("Pixel calibration", self.setPixCal)

        showImportAction = self.createAction("Image import",
                                             self.showImportSettings)

        helpAboutAction = self.createAction("&About Odysseus",
                self.helpAbout)
        openManualAction = self.createAction("User Manual", self.openManual)

        fileMenu = self.menuBar().addMenu("&File")
        preferencesMenu = self.menuBar().addMenu("&Preferences")
        helpMenu = self.menuBar().addMenu("&Help")

        self.addActions(fileMenu, (fileOpenAction, fileSaveAction, None,
                                   fileQuitAction))
        self.addActions(preferencesMenu, (setPixCalAction, None,
                                          showImportAction))
        self.addActions(helpMenu, (openManualAction, None, helpAboutAction))


    def helpAbout(self):
        if platform.system() == 'Windows':
            pyversion = sys.winver
        else:
            pyversion = platform.python_version()
        QMessageBox.about(self, "About Odysseus",
                """<b>Odysseus - the cold atom viewer</b> v %s
                <p>Copyright &copy; 2008-2009 Ketterle group, MIT.
                All rights reserved.
                <p>This application can be used to view images
                obtained from cold atom experiments.
                <p>Python %s - Qt %s - PyQt %s on %s""" % (
                __version__, pyversion,
                QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))


    def openManual(self):
        """Launch a browser (or a new tab) and open the user manual in it"""
        url = os.path.join(sys.path[0], 'docs', '.build', 'html', 'index.html')
        webbrowser.open_new_tab(url)


    def displayPluginMenu(self, imgnumber, imgpath):
        """Displays a menu with all available plugins."""

        if imgnumber > self.cwidget.gridnum:
            return # image itself not in memory anymore, do nothing

        # populate the context menu
        contextMenu = QMenu('Analysis Plugins', self)
        for plugin in self.plugin_manager.getPluginsOfCategory('Default'):
            # plugin is a PluginInfo object
            contextMenu.addAction(plugin.name)
        clickAction = contextMenu.exec_(QCursor.pos())

        # respond to a context menu click
        if clickAction:
            # save and reset rc params (so plugins can do whatever they want)
            currentparams = mpl.pyplot.rcParams.copy()
            mpl.pyplot.rcdefaults()

            # execute main() function of plugin
            plugin_name = clickAction.text()
            plugin = self.plugin_manager.getPluginByName(plugin_name)
            plugin.plugin_object.imgpath = imgpath
            try:
                roilist = self.cwidget.absImage.rois['analysis']
                clicked_img = self.cwidget.img_list[imgnumber][:, :, 0]
                if self.cwidget.absImage.roiboxes['analysis']:
                    roislice = (slice(roilist[2], roilist[3]),
                                slice(roilist[0], roilist[1]))
                else:
                    roislice = (slice(0, clicked_img.shape[0]),
                                slice(0, clicked_img.shape[1]))
                allframes = self.cwidget.img_list[imgnumber]
                # TODO: find a good way to pass more arguments to plugins.
                #       maybe in a dict, so each plugin can use what it needs?
                self.pluginwindowlist.append(plugin.plugin_object.create_window(\
                        allframes, clicked_img, roislice, plugin_name, imgpath))
#                self.pluginwindowlist.append(plugin.plugin_object.create_window(\
#                        clicked_img, roislice, plugin_name))
            except:
                errordialog = MaxsizeDialog(cgitb.html(sys.exc_info()))
                errordialog.exec_()

            # restore rc params
            mpl.pyplot.rcParams.update(currentparams)


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("Ketterle group, MIT")
    app.setOrganizationDomain("cua.mit.edu/ketterle_group/")
    app.setApplicationName("Odysseus")
    app.setWindowIcon(QIcon(":/icon.png"))

    form = MainWindow()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
