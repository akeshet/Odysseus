import os
import re
import popen2
import platform

import numpy as np
import matplotlib as mpl
from pylab import figure, savefig, show, close

from fitfermions import fit_img, do_fit, find_ellipticity
from imageprocess import *
from fitfuncs import *
from centerofmass import center_of_mass
from visualize import *


def write_TeXreport(texname, img_name, ellip, ellip_figname, fitresults):
    """Writes the LaTeX source for a report with test results for an image

    **Inputs**

      * texname: string, name of the output .tex file
      * img_name: string, the name of the image
      * ellip: float, the ellipticity of the atom cloud
      * ellip_figname: string, name of the figure with residuals of lineprofiles
      * fitresults: tuple, containing the results of the fit: T/T_F, N,
        fugacity, B'

    """

    img_name = os.path.split(img_name)[1]

    LaTeXpreamble = r"""\documentclass[onecolumn,amsmath,amssymb]{revtex4}

    \usepackage{graphicx}
    \usepackage{amsmath}

    \graphicspath{{???}}
    """

    tex_main = r"""\begin{document}

    \title{/title}
    \author{BEC2}
    \affiliation{Research Laboratory of Electronics, Massachusetts Institute of Technology, 77 Massachusetts Avenue, Cambridge, Massachusetts 02139, United States}
    \date{\today}

    \begin{abstract}
    This is the test report for image \textit{/imagename}.
    \end{abstract}

    \maketitle

    The transmission image and raw frames are shown in figure~\ref{fig:rawframes}.

    \begin{figure}
    \begin{center}
    \includegraphics[width=4.5in]{trans_rawframes}
    \caption{Transmission image (left top) and raw frames - probe with atoms
    (right top), probe without atoms (left bottom) and dark field (right bottom)
    .}
    \label{fig:rawframes}
    \end{center}
    \end{figure}

    The azimuthally averaged data together with the best fit are shown in
    figure~\ref{fig:fitresult}. The fitted temperature is $T/T_F=/tovertf$, the
    fitted number of atoms is $N=/number \cdot10^6$ , the fugacity is $\eta=e^{/fugacity}$ and
    the cloud size is $B'=/bprime$ pixels.

    \begin{figure}
    \begin{center}
    \includegraphics[width=4.5in]{fitresult}
    \caption{The azimuthally averaged optical density together with the fit result.}
    \label{fig:fitresult}
    \end{center}
    \end{figure}

    The fit residuals are shown in figure~\ref{fig:residuals}. The fit is most
    sensitive near the center and where it starts deviating visibly from zero.
    Therefore the residuals will probably be largest there, this does not
    necessarily mean that there is a problem with the shape of the cloud.

    \begin{figure}
    \begin{center}
    \includegraphics[width=7in]{residuals}
    \caption{Residuals of the fit (left) and the data and fit plotted on a log
    scale (right).}
    \label{fig:residuals}
    \end{center}
    \end{figure}

    \pagebreak
    Figures~\ref{fig:several_temps} and~\ref{fig:several_temps_zoomed} show
    fits to the data of the ideal Fermi gas distribution with fixed
    temperatures. This should give a good indication of whether the fit result
    makes sense and if the result is actually sensitive to the temperature or
    not.

    \begin{figure}
    \begin{center}
    \includegraphics[width=4.5in]{several_temps}
    \caption{The data fitted several times with certain fixed temperatures.}
    \label{fig:several_temps}
    \end{center}
    \end{figure}

    \begin{figure}
    \begin{center}
    \includegraphics[width=4.5in]{several_temps_zoomed}
    \caption{The data fitted several times with certain fixed temperatures,
    zoomed in on the part of the data that is most sensitive to $T/T_F$.}
    \label{fig:several_temps_zoomed}
    \end{center}
    \end{figure}

    \pagebreak
    The ellipticity of the image, as found by the optimization routine in the
    function \textit{find\_ellipticity}, is /ellip. To see if this result is
    correct, we plot the sum of residuals of the fit along the radial direction
    for each angle $\phi$ in figure~\ref{fig:ellip}. If any structure is
    visible, this may mean that either there are fringes or other imperfections
    in the image, or the determination of ellipticity or center of mass was
    flawed. A good image has typically a sum of residuals of 1 - 2.5, if there
    was a problem this number will be larger.

    \begin{figure}
    \begin{center}
    \includegraphics[width=4.5in]{/ellfig}
    \caption{The sum of fit residuals of the radial line profiles.}
    \label{fig:ellip}
    \end{center}
    \end{figure}

    \end{document}
    """

    title = "Image test report for %s" %os.path.split(img_name)[1]

    tex_main = re.sub(r"/title", title, tex_main)
    tex_main = re.sub(r"/imagename", img_name, tex_main)
    tex_main = re.sub(r"/ellip", str(ellip)[:5], tex_main)
    tex_main = re.sub(r"/ellfig", ellip_figname, tex_main)

    tex_main = re.sub(r"/tovertf", str(fitresults[0])[:5], tex_main)
    tex_main = re.sub(r"/number", str(fitresults[1]*1e-6)[:3], tex_main)
    tex_main = re.sub(r"/fugacity", str(fitresults[2])[:4], tex_main)
    tex_main = re.sub(r"/bprime", str(fitresults[3])[:4], tex_main)

    texstr = ''.join([LaTeXpreamble, tex_main])
    # Write the tex file
    texfile = open('%s.tex' %os.path.splitext(texname)[0], "w")
    texfile.write(texstr)
    texfile.close()

    return


def generate_report(rawframes, transimg, img_name, pixcal, showpdf=True):
    """Generate a report with several image diagnostics

    The report comes in the form of a pdf file that has the name
    ``img_name``.pdf and is put in the same directory as the image.

    **Inputs**

      * rawframes: 3D array, containing the three raw frames
      * transimg: 2D array, containing the transmission image (properly ROIed)
      * img_name: string, the name of the image
      * pixcal: float, pixel size calibration in m/pix.
      * showpdf: bool, if True Acrobat Reader is launched to view the report

    """

    odimg = trans2od(transimg)
    com = center_of_mass(odimg)

    rawfig = show_rawframes(rawframes)
    savefig('trans_rawframes.jpg')
    close()

    ellip = find_ellipticity(transimg)
    ellip_figname = 'ellipfit'

    # figure out how good the ellipticity determination is and create polar plot
    rcoord, rad_profile, rprofiles, angles = radial_interpolate(odimg, com,\
                                    0.3, elliptic=(ellip, 0), full_output=True)
    od_cutoff = find_fitrange(rad_profile)
    av_err = radialprofile_errors(rprofiles, angles, rad_profile, od_cutoff, \
                        showfig=True, savefig_name=ellip_figname, report=False)

    # fit the image
    ToverTF, N, com, ans, rcoord, od_prof, fit_prof = fit_img(transimg, \
            showfig=False, elliptic=(ellip, 0), full_output='odysseus')
    # save the fit figure
    show_fitresult(rcoord, od_prof, fit_prof, ToverTF, N, figname='fitresult')

    # plot the residuals
    show_residuals(rcoord, od_prof, fit_prof, figname='residuals')
    fitresults = (ToverTF[0], N, ans[1], ans[2])

    # fit with several fixed temperatures
    ans_gaussian, ans2, temps = fit_several_fixedT(rcoord, od_prof, od_cutoff,
                                                   ans, ToverTF, pixcal)
    fig = plot_several_temp(rcoord, od_prof, fit_prof, ans, ans_gaussian, ans2,
                            pixcal)
    fig.savefig('several_temps.png')
    close(fig)

    # save a figure zoomed in around the wing of the distribution
    ind = round(ans2[0][2])
    istep = round(1./(rcoord[1]-rcoord[0]))*15
    ind = mpl.mlab.find(rcoord>ind).min()
    fig2 = plot_several_temp(rcoord[ind-istep:ind+istep], od_prof[ind-istep:ind+istep], \
                            fit_prof[ind-istep:ind+istep], ans, ans_gaussian,
                            ans2, pixcal)
    fig2.savefig('several_temps_zoomed.png')
    close(fig2)

    # create the report
    write_TeXreport('imgreport', img_name, ellip, ellip_figname, fitresults)
    print 'written TeX'
    pdfname = os.path.splitext(img_name)[0]
    TeX2pdf('imgreport', pdfname)
    print 'written pdf'

    # clean up image files
    pngfiles = ['ellipfit', 'fitresult', 'residuals', 'several_temps', \
                'several_temps_zoomed']
    for pngfile in pngfiles:
        try:
            os.unlink(''.join([pngfile, '.png']))
        except OSError:
            print "file %s.png does not exist, so can't clean it up" %pngfile

    jpgfiles = ['trans_rawframes']
    for jpgfile in jpgfiles:
        try:
            os.unlink(''.join([jpgfile, '.jpg']))
        except OSError:
            print "file %s.jpg does not exist, so can't clean it up" %jpgfile

    if showpdf:
        # launch acrobat reader with the report
        acrocmd = r"acroread %s.pdf" %re.sub(r" ", r"\ ", pdfname)
        acrocmd = re.sub(r";", r"\;", acrocmd)

        if platform.system()=='Windows':
            os.system(acrocmd)
        else:
            acrocmd = re.sub(r"acroread", r"xdg-open", acrocmd)
            os.system(acrocmd)

    return


def fit_several_fixedT(rcoord, od_prof, od_cutoff, guess, ToverTF, pixcal):
    """Fits the image with 7 fixed temperatures and with a Gaussian

    **Inputs**

      * rcoord: 1d array, containing the radial coordinate
      * od_prof: 1d array, containing the radially averaged optical density
        profile
      * od_cutoff: int, the index of rcoord at which the fit starts
      * guess: tuple, containing n0, a, bprime as initial guess for the fit
      * ToverTF: float, the temperature from the fit where T was not constrained
      * pixcal: float, pixel size calibration in m/pix.

    **Outputs**

      * ans_gaussian: tuple, the result of fitting with a Gaussian distribution
      * ans2: list of tuples, each tuple in the list is the result of fitting
        with the ideal Fermi gas distribution where the temperature is held
        fixed.
      * temps: 1D array, the temperatures with which the data was fit

    """

    u, uu, ans_gaussian = do_fit(rcoord, od_prof, od_cutoff, guess, pixcal,
                                 fitfunc='gaussian')
    ans2 = []
    temps = np.linspace(0.01, 2, 7)*ToverTF
    for temp in temps:
        u, uu, ans2_temp = do_fit(rcoord, od_prof, od_cutoff, guess, pixcal,
                                  fitfunc='idealfermi_fixedT', T=temp)
        ans2.append(ans2_temp)
    return (ans_gaussian, ans2, temps)


def plot_several_temp(rcoord, od_prof, fit_prof, ans, ans_gaussian, ans2, pixcal=None):
    """A figure is generated of the OD profile and fits to it with fixed T

    **Inputs**

      * rcoord: 1d array, containing the radial coordinate
      * od_prof: 1d array, containing the radially averaged optical density
        profile
      * fit_prof: 1d array, containing the fit to the optical density
      * ans: tuple, the result of fitting with the ideal Fermi gas distribution
      * ans_gaussian: tuple, the result of fitting with a Gaussian distribution
      * ans2: list of tuples, each tuple in the list is the result of fitting
        with the ideal Fermi gas distribution where the temperature is held
        fixed.
      * pixcal: float, pixel size calibration in m/pix. If None no result for
                N, T is printed in the figure.

    **Outputs**

      * fig: the generated figure instance

    """

    fig = pylab.figure()
    ax2 = fig.add_subplot(111)
    ax2.plot(rcoord, od_prof, c=(0.5,0.5,0.5), lw=3, label=r'data')
    ax2.plot(rcoord, fit_prof, c=(0.5,0.5,0.5), lw=1.5, ls='--', \
             label=r'$n_{2D}(r)$ fit')
    ax2.plot(rcoord, gaussian(rcoord, *ans_gaussian), label=r'gaussian fit')
    for temp in ans2:
        if pixcal:
            T2, N2 = ideal_fermi_numbers(temp, pixcal)
            ax2.plot(rcoord, ideal_fermi_radial(rcoord, *temp), \
                     label=r'$n_{2D}(r)$ fit, $T/T_F=%1.2f$'%T2)

    ax2.set_xlabel(r'$r$ [pix]')
    ax2.set_ylabel(r'$OD$')
    ax2.legend()

    return fig


def TeX2pdf(texname, pdfname=None):
    """ Compiles a TeX file with pdfLaTeX and cleans up the mess afterwards

    From pyreport (Gael Varoquaux), with GPL license.

    """

    print "Compiling document to pdf"
    texname = os.path.splitext(texname)[0]
    texcmd = "pdflatex --interaction scrollmode %s.tex" %texname
    os.system(texcmd)
    (err_out, stdin) = popen2.popen4(texcmd)
    output = []
    while True:
        line = err_out.readline()
        if not line:
            break
        output.append(line)
    print "Cleaning up"
    os.unlink(texname+".tex")
    os.unlink(texname+".log")
    os.unlink(texname+".aux")
    if pdfname:
        os.rename(texname+".pdf", pdfname+".pdf")