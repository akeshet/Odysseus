import os

from odysseus import imageio, imageprocess
from odysseus.fitfermions import fit_img, find_ellipticity


dirname = 'datafiles'
#dirname = 'c:\\Data\\2008-12-12' # double backslashes on windows

# import a single image (for finding each TIF file in a directory,
# see example_filetools.py)
fname = 'raw9.11.2008 7;35;23 PM.TIF'
img_name = os.path.join(dirname, fname)
rawframes = imageio.import_rawframes(img_name)

#calculate the transmission and OD images
transimg, odimg = imageprocess.calc_absimage(rawframes)
# set the ROI
transimg = transimg[120:350, 50:275]

# find the ellipticity if the expansion is not spherically symmetric
ellip = find_ellipticity(transimg)
# do the fit (this pops up an image, unless you set showfig=False)
ToverTF, N, ans = fit_img(transimg, elliptic=(ellip, 0), showfig=True)