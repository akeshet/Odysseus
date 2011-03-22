from PyQt4.QtCore import *
from PyQt4.QtGui import *


coldict = {'blue':'b', 'lightblue':'#7A88FF', 'purple':'#AF7AFF', \
             'orange':'#FFAF7A', 'bgcolor':'#DEDEDE'} #'blue':'#6600FF'
coldict_rgb = {'blue':(102, 0, 255), 'lightblue':(122, 136, 255), \
               'purple':(175, 122, 255), 'orange':(255, 175, 122), \
               'bgcolor':(222, 222, 222)}


def create_labeledbox(labeltext, direction='hor', stretch=None):
    """Convenience function to generate  a layout with two QLabels"""

    label = QLabel(labeltext)
    box = QLabel()
    box.setFrameStyle(QFrame.StyledPanel)
    if direction=='hor':
        layout = QHBoxLayout()
    elif direction=='vert':
        layout = QVBoxLayout()
    layout.addWidget(label)
    if not stretch:
        layout.addWidget(box)
    else:
        layout.addWidget(box, stretch)

    return box, layout


def create_labeledspinbox(labeltext, range=(0, 99), direction='hor',
                          stretch=None, intvals=True, active=False):
    """Convenience function to generate  a layout with a labeled spinbox

    If labelmsg is not None, right-clicking on the label emits a LabelMsg,
    with `labelmsg` as the string argument.

    """

    if active:
        label = RightClickLabel(labeltext)
    else:
        label = QLabel(labeltext)
    palette = QPalette()
    palette.setBrush(QPalette.Foreground, Qt.black)
    label.setPalette(palette)
    if intvals:
        box = QSpinBox()
    else:
        box = QDoubleSpinBox()
    box.setRange(*range)
    if direction=='hor':
        layout = QHBoxLayout()
    elif direction=='vert':
        layout = QVBoxLayout()
    layout.addWidget(label)
    if not stretch:
        layout.addWidget(box)
    else:
        layout.addWidget(box, stretch)

    if active:
        return box, layout, label
    else:
        return box, layout


def create_roibox(boxtext, xrange=(0, 2500), yrange=(0, 2500), color=None):
    """Returns a groupbox with ROI coordinate input boxes"""

    x0, x0layout, x0label = create_labeledspinbox('X0', range=xrange,
                                                  active=True)
    x1, x1layout, x1label = create_labeledspinbox('X1', range=xrange,
                                                  active=True)
    y0, y0layout = create_labeledspinbox('Y0', range=yrange)
    y1, y1layout = create_labeledspinbox('Y1', range=yrange)
    x1.setValue(xrange[1])
    y1.setValue(yrange[1])
    setbutton = QPushButton("Set ROI")
    clearbutton = QPushButton("Clear ROI")

    boxlayout = QGridLayout()
    boxlayout.addLayout(x0layout, 0, 0)
    boxlayout.addLayout(x1layout, 1, 0)
    boxlayout.addLayout(y0layout, 0, 1)
    boxlayout.addLayout(y1layout, 1, 1)
    boxlayout.addWidget(setbutton, 0, 2)
    boxlayout.addWidget(clearbutton, 1, 2)

    roibox = QGroupBox(boxtext)
    roibox.setLayout(boxlayout)
    roibox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    return (roibox, [x0, x1, y0, y1], setbutton, clearbutton, [x0label, x1label])


class ImgCtrlBox():
    def __init__(self, coldict, boxtext='Image Ctrl', color=None):
        """Returns a groupbox with a colormap combobox and vmin/max spinboxes."""

        self.colmapCtrl = QComboBox()
        for cmap in coldict.keys():
            self.colmapCtrl.addItem(cmap)
        self.colmapCtrl.setCurrentIndex(self.colmapCtrl.findText('gray'))

        self.minCtrl, minlayout = create_labeledspinbox('vmin', range=(0, 1e5),
                                                        intvals=False)
        self.maxCtrl, maxlayout = create_labeledspinbox('vmax', range=(0, 1e5),
                                                        intvals=False)
        self.maxCtrl.setValue(1.35)
        self.setVals = QPushButton("Set &values")

        boxlayout = QGridLayout()
        boxlayout.addLayout(minlayout, 0, 0)
        boxlayout.addLayout(maxlayout, 1, 0)
        boxlayout.addWidget(self.setVals, 0, 1)
        boxlayout.addWidget(self.colmapCtrl, 1, 1)

        self.colbox = QGroupBox(boxtext)
        self.colbox.setLayout(boxlayout)
        self.colbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        palette = QPalette()
        imgctrl_color = QColor()
        imgctrl_color.setNamedColor('steelblue')
        palette.setBrush(QPalette.WindowText, imgctrl_color)
        self.colbox.setPalette(palette)



class ImageMarker(QLabel):
    """Normal QLabel with the option to right-click and do something"""

    def mousePressEvent(self, event):
        """Left-click is handled by MPL, right-click not."""

        if event.button()==2:
            self.emit(SIGNAL("ClearMarker"))


class RightClickLabel(QLabel):
    """Normal QLabel with the option to right-click and emit 'update' signal"""

    def mousePressEvent(self, event):
        """Left-click is handled by MPL, right-click not."""

        if event.button()==2:
            self.emit(SIGNAL("LabelMsg"))


class MaxsizeDialog(QDialog):

    def __init__(self, labeltext, parent=None):
        """This is a dialog to show error messages from plugins."""
        super(MaxsizeDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle('Odysseus - Plugin Error')

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        self.errorText = QLabel(labeltext)
        self.errorText.setMaximumWidth(800)
        self.errorText.setWordWrap(True)
        scrollArea.setWidget(self.errorText)
        self.scrollArea = scrollArea

        layout = QVBoxLayout()
        layout.addWidget(self.scrollArea)
        self.setLayout(layout)


    def sizeHint(self):
        return QSize(850, 1000)