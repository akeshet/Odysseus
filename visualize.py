#!/usr/bin/env python
"""Functions to create and/or save plots of images and fit results.

"""

import numpy as np
import scipy as sp
import matplotlib as mpl
import pylab

from imageprocess import calc_absimage


def show_fitresult(rcoord, od_prof, fit_prof, T, N, figname=None, showfig=False):
    """Plot the result of fitting an image.

    The figure that is generated contains a single plot of the profile of the
    optical density plus the fit. Also displayed are the temperature and
    number of atoms as determined by the fit and a legend.

    **Inputs**

      * rcoord: 1D array containing the radial coordinate
      * od_prof: 1D array containing the radially averaged optical density
                 profile
      * fit_prof: 1D array containing the fit to the optical density
      * T: temperature as determined by the fit
      * N: number of atoms as determined by the fit

    **Outputs**

      * fig: matplotlib figure instance

    **Optional inputs**

      * figname: str, if not None the figure is saved with this filename
      * showfig: bool, if True pop up a figure with pylab.show()

    """

    fig = pylab.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(rcoord, od_prof, 'b-', label=r'data')
    ax1.plot(rcoord, fit_prof, 'r-', label=r'$n_{2D}(r)$ fit')

    ax1.set_xlabel(r'$r$ [pix]')
    ax1.set_ylabel(r'$OD$')
    ax1.legend()
    ax1.text(0.7,0.5, r'$T/T_F=$ %1.2f'%T, color='r', transform=ax1.transAxes)
    ax1.text(0.7, 0.4, r'$N=$ %1.1f $\cdot10^6$'%(N*1e-6), color='r', \
             transform=ax1.transAxes)

    _save_or_show(figname=figname, showfig=showfig)

    return fig


def show_fitresult_errorbars(rcoord, od_prof, fit_profs, T, N, linestyles=None,
                             Terr=[0.03], figname=None, showfig=False):
    """Plot the result of fitting an image.

    The figure that is generated contains a single plot of the profile of the
    optical density plus the fit. Also displayed are the temperature and
    number of atoms as determined by the fit and a legend.

    **Inputs**

      * rcoord: 1D array containing the radial coordinate
      * od_prof: 1D array containing the radially averaged optical density
                 profile
      * fit_profs: list of 1D arrays, each 1D array is a fit to the optical
                   density, the first one the optimal fit, the next ones
                   give (graphical) error bars by fitting with fixed T/T_F
      * T: temperature as determined by the fit
      * N: number of atoms as determined by the fit

    **Outputs**

      * fig: matplotlib figure instance

    **Optional inputs**

      * linestyles: list of str, list of the same length as `fit_profs`, with
                    each string a plot style for the line
                    (i.e. 'r-' for a red solid line)
      * Terr: list of floats, one value for each two profiles in fit_profs
              that give the width of the error lines.
      * figname: str, if not None the figure is saved with this filename
      * showfig: bool, if True pop up a figure with pylab.show()

    """

    if not linestyles:
        linestyles = ['r-']
        for i in range(len(fit_profs)-1):
            linestyles.append('r--')
    proflabels = []
    for num in Terr:
        proflabels.append(r'$T/T_F\pm%s$'%str(num))
        proflabels.append(None)
    print proflabels

    fig = pylab.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(rcoord, od_prof, 'b-', lw=1.5, label=r'data')
    ax1.plot(rcoord, fit_profs[0], linestyles[0], label=r'$n_{2D}(r)$ fit')
    for prof, lstyle, label in zip(fit_profs[1:], linestyles[1:], proflabels):
        ax1.plot(rcoord, prof, lstyle, label=label)

    ax1.set_xlabel(r'$r$ [pix]')
    ax1.set_ylabel(r'$OD$')
    ax1.legend()
    ax1.text(0.7,0.5, r'$T/T_F=$ %1.2f'%T, color='r', transform=ax1.transAxes)
    ax1.text(0.7, 0.4, r'$N=$ %1.1f $\cdot10^6$'%(N*1e-6), color='r', \
             transform=ax1.transAxes)

    _save_or_show(figname=figname, showfig=showfig)

    return fig


def show_rawframes(rawdata, figname=None, showfig=False):
    """Plots the transmission image together with the 3 raw images

    **Inputs**

      * rawdata: 3D array, containing pwa, pwoa, df. Last dimension is frame
                 index
      * figname: str, if not None the figure is saved with this filename
      * showfig: bool, if True pop up a figure with pylab.show()

    **Outputs**

      * fig: matplotlib figure instance

    """

    transimg, odimg = calc_absimage(rawdata)
    aspect = transimg.shape[0]/float(transimg.shape[1])

    fig = pylab.figure(figsize=(8, 8*aspect))
    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)

    ax1.imshow(transimg, cmap=pylab.cm.gray, vmin=0, vmax=1.35)
    ax2.imshow(rawdata[:, :, 0], cmap=pylab.cm.gray)
    ax3.imshow(rawdata[:, :, 1], cmap=pylab.cm.gray)
    ax4.imshow(rawdata[:, :, 2], cmap=pylab.cm.gray)

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xticks([])
        ax.set_yticks([])

    _save_or_show(figname=figname, showfig=showfig)

    return fig


def show_transimg(img, vmin=0, vmax=1.35, cmap=None, com=None, colorbar=False,
                  figname=None, showfig=False):
    """Show a single transmission image

    **Inputs**

      * img: 2D array, the image data
      * vmin: float, the minimum value of the colormap
      * vmax: float, the maximum value of the colormap
      * cmap: instance, a matplotlib colormap instance. The default is
              a gray colormap.
      * com: 1D array, containing the coordinates of the center of mass. If
             com is supplied it is plotted as a red cross.
      * colorbar: bool, if True a color scale is displayed
      * figname: str, if not None the figure is saved with this filename
      * showfig: bool, if True pop up a figure with pylab.show()

    **Outputs**

      * fig: matplotlib figure instance

    """

    if not cmap:
        cmap = pylab.cm.gray

    fig = pylab.figure()
    ax = fig.add_subplot(111)
    ax.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks([])
    ax.set_yticks([])

    if com:
        ax.plot([com[1]], [com[0]], 'w+', ms=10, zorder=5)
    if colorbar:
        fig.colorbar(img)

    _save_or_show(figname=figname, showfig=showfig)

    return fig


def contourplot(img, numlines=100, filter=None, figname=None, showfig=False):
    """Aply a Gaussian filter and show the image with contour lines

    **Inputs**

      * img: 2D array, containing the image
      * numlines: int, the number of contour lines
      * filter: float, size of Gaussian filter in pixels. For more details,
                see the scipy.ndimage docs.
      * figname: str, if not None the figure is saved with this filename
      * showfig: bool, if True pop up a figure with pylab.show()

    **Outputs**

      * fig: matplotlib figure instance, the contour plot

    """

    if filter:
        img = sp.ndimage.gaussian_filter(img, filter)
    aspect = img.shape[1]/float(img.shape[0])
    fig = pylab.figure(figsize=(12, 12*aspect))
    ax = fig.add_subplot(111)
    ax.contourf(img, numlines, interpolation='nearest', cmap=pylab.cm.hot)
    ax.contour(img, numlines, interpolation='nearest', cmap=pylab.cm.Accent)

    _save_or_show(figname=figname, showfig=showfig)

    return fig


def show_img_and_com(img, com, cmap=pylab.cm.gray, figname=None, showfig=False):
    """Show the image and mark the center of mass with a cross


    **Inputs**

      * img: 2D array, containing the image
      * com: sequence, containing the two coordinates of the center of mass
      * cmap: colormap, a valid colormap from the matplotlib.cm module
      * figname: str, if not None the figure is saved with this filename
      * showfig: bool, if True pop up a figure with pylab.show()

    **Outputs**

      * fig: matplotlib figure instance, the contour plot

    """

    fig = pylab.figure()
    ax = fig.add_subplot(111)

    ax.plot([com[1]], [com[0]], 'r+', ms=15, zorder=5)
    ax.imshow(img, cmap=cmap)

    _save_or_show(figname=figname, showfig=showfig)

    return fig


def show_residuals(rcoord, od_prof, fit_prof, figname=None, showfig=False):
    """Plots the fit residuals

    **Inputs**

      * rcoord: 1D array, containing the radial coordinate
      * od_prof: 1D array, containing the radially averaged optical density
        profile
      * fit_prof: 1D array, containing the fit to the optical density

    **Outputs**

      * fig: matplotlib figure instance

    **Optional inputs**

      * figname: str, if not None the figure is saved with this filename
      * showfig: bool, if True pop up a figure with pylab.show()

    """

    fig = pylab.figure(figsize=(12,4))
    ax1 = fig.add_subplot(121)
    ax1.plot(rcoord, od_prof - fit_prof, 'b-')
    ax1.axhline(0, color='k', lw=0.5)
    ax1.set_xlabel(r'$r$ [pix]')
    ax1.set_ylabel(r'$OD_{data}-OD_{fit}$')

    od_prof = np.where(od_prof<0, 1e-10, od_prof)
    ax2 = fig.add_subplot(122)
    ax2.semilogy(rcoord**2, od_prof, 'b-', label=r'data')
    ax2.semilogy(rcoord**2, fit_prof, 'r-', label=r'$n_{2D}(r)$ fit')
    ax2.set_ylim(1e-5, fit_prof.max()*2)
    ax2.set_xlabel(r'$r^2$ [pix]')
    ax2.set_ylabel(r'$OD$')
    ax2.legend()

    _save_or_show(figname=figname, showfig=showfig)

    return fig


def _save_or_show(figname=None, showfig=False):
    """Save and/or show figure depending on inputs"""

    if figname:
        pylab.savefig(''.join([figname, '.png']))
        pylab.close()
    if showfig:
        pylab.show()