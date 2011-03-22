import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import imageio
import imageprocess
import importsettingsdialog


class ImportSettingsDialog(QDialog, importsettingsdialog.Ui_ImportSettingsDialog):
    """A modeless dialog to configure the image import.

    It should handle the designation of pwa/pwoa/df1/df2 to frames, as well as
    splitting up images taken in kinetics mode. If active, it overrides the
    Odysseus defaults.
    """

    def __init__(self, importdict, parent=None):
        super(ImportSettingsDialog, self).__init__(parent)
        self.setupUi(self)
        self.importdict = importdict
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Image import settings")

        self.connect(self.buttonBox.button(QDialogButtonBox.Apply),
                     SIGNAL("clicked()"), self.apply)
        self.connect(self.buttonBox, SIGNAL("rejected()"), self,
                     SLOT("reject()"))
        self.connect(self.numberSpinBox, SIGNAL("valueChanged(int)"), self.load)

        self.load() # load defaults


    def load(self):
        """Load the settings for the number of frames."""
        try:
            fsett = self.importdict[str(self.numberSpinBox.value())]

            self.pwaSpinBox.setValue(fsett.pwa)
            self.pwoaSpinBox.setValue(fsett.pwoa)
            self.df1SpinBox.setValue(fsett.df1)
            self.df2SpinBox.setValue(fsett.df2)

            self.kineticsGroupBox.setChecked(fsett.kinetics)
            self.lineshiftSpinBox.setValue(fsett.lineshift)
            self.stripsperframeSpinBox.setValue(fsett.strips_per_frame)
            if fsett.orientation=='V':
                self.vertRadioButton.setChecked(True)
            else:
                self.horRadioButton.setChecked(True)
            if fsett.startat=='BR':
                self.bottomRadioButton.setChecked(True)
            else:
                self.topRadioButton.setChecked(True)

            self.execTextEdit.document().setPlainText(fsett.text)
            self.customfuncCheckBox.setChecked(fsett.usetext)

        except KeyError:
            pass


    def apply(self):
        """Apply the changes."""
        try:
            fsett = self.importdict[str(self.numberSpinBox.value())]
        except KeyError:
            fsett = FrameSetting()
            self.importdict[str(self.numberSpinBox.value())] = fsett

        fsett.pwa = self.pwaSpinBox.value()
        fsett.pwoa = self.pwoaSpinBox.value()
        fsett.df1 = self.df1SpinBox.value()
        fsett.df2 = self.df2SpinBox.value()

        fsett.kinetics = self.kineticsGroupBox.isChecked()
        fsett.lineshift = self.lineshiftSpinBox.value()
        fsett.strips_per_frame = self.stripsperframeSpinBox.value()
        if self.vertRadioButton.isChecked():
            fsett.orientation = 'V'
        else:
            fsett.orientation = 'H'
        if self.bottomRadioButton.isChecked():
            fsett.startat = 'BR'
        else:
            fsett.startat = 'TL'

        fsett.usetext = self.customfuncCheckBox.isChecked()
        if fsett.usetext:
            rawtext = self.execTextEdit.document().toPlainText()
            if self.validate_text(rawtext):
                fsett.text = rawtext


    def validate_text(self, rawinput):
        """Checks if the code in the executable text edit window is valid"""
        funcstr = _construct_custom_func(rawinput)
        try:
            exec(funcstr)
            return True
        except SyntaxError, e:
            QMessageBox.about(self, "Syntax error", str(e))
            return False


def _construct_custom_func(rawinput):
    """Create the function as given by the user."""
    funcstr = ("def imgfunc(pwa, pwoa, df1, df2, frames):\n%s\nreturn result"\
               %rawinput).replace('\n', '\n    ')

    return funcstr


class FrameSetting():
    """Class to hold all import settings for a given number of frames."""

    def __init__(self, pwa=0, pwoa=1, df1=2, df2=2, kinetics=False,
                 lineshift=256, strips_per_frame=3,
                 orientation='V', startat='BR'):
        self.pwa = pwa
        self.pwoa = pwoa
        self.df1 = df1
        self.df2 = df2
        self.kinetics = kinetics
        self.lineshift = lineshift
        self.strips_per_frame = strips_per_frame
        self.orientation = orientation
        self.startat = startat
        self.text = ''
        self.usetext = False


_1frame = FrameSetting(kinetics=True)
_2frame = FrameSetting(kinetics=True)
_3frame = FrameSetting()
_4frame = FrameSetting(df2=3)
_6frame = FrameSetting(pwa=3, pwoa=2, df1=5, df2=4)

image_import_dict = dict({'1':_1frame, '2':_2frame, '3':_3frame, '4':_4frame,
                          '6':_6frame})


def process_import(fname, dct=image_import_dict):
    imglist = imageio.list_of_frames(fname)
    fsett = dct[str(len(imglist))]
    pwa, pwoa, df1, df2 = fsett.pwa, fsett.pwoa, fsett.df1, fsett.df2

    # split the individual frames if kinetics mode is specified
    if fsett.kinetics:
        templist = []
        for frame in imglist:
            for i in xrange(fsett.strips_per_frame):
                if fsett.startat == 'BR':
                    if fsett.orientation == 'V':
                        size = imglist[pwa].shape[0]
                    else:
                        size = imglist[pwa].shape[1]
                    idx = slice(size - (i+1)*fsett.lineshift,
                                size - i*fsett.lineshift)
                else:
                    idx = slice(i*fsett.lineshift, (i+1)*fsett.lineshift)
                if fsett.orientation == 'V':
                    templist.append(frame[idx, :])
                else:
                    templist.append(frame[:, idx])
        imglist = templist

    rawframes = np.dstack(imglist)
    if not fsett.usetext:
        transimg, odimg = default_calc_transimg(imglist[pwa], imglist[pwoa],
                                                imglist[df1], imglist[df2])
    else:
        funcstr = _construct_custom_func(fsett.text)
        exec(funcstr) # create the function
        transimg = imgfunc(imglist[pwa], imglist[pwoa],
                           imglist[df1], imglist[df2], imglist)
        odimg = imageprocess.trans2od(transimg)

    return rawframes, transimg, odimg


def default_calc_transimg(pwa, pwoa, df1, df2):
    """The default treatment to obtain a transmission image."""

    nom = pwa - df1
    den = pwoa - df2
    nom = np.where(nom<1, 1, nom)
    den = np.where(den<1, 1, den)

    transimg = nom.astype(float)/den
    odimg = -np.log(transimg)

    return transimg, odimg

