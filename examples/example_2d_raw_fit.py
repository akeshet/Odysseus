import os

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

from odysseus import imageio, imageprocess, fitfuncs2D, fitfermions


pixcal = 1e-5  # 20 um pixels, magnification of 2.

dirname = os.path.join(r'C:\autosave')
fname = '11-20-2009_124322.TIF'
img_name = os.path.join(dirname, fname)
rawframes = imageio.import_rawframes(img_name)

rawframesc=rawframes[98:374, 158:372, :]

pwa = rawframesc[:,:,0]
pwoa = rawframesc[:,:,1]
df = rawframesc[:,:,2]

# calculate the transmission and OD images
transimg, odimg = imageprocess.calc_absimage(rawframes)
# set the ROI
transimg = transimg[98:374, 158:372]
# normalized the image
transimg, odimg, com, n0, q, bprime = fitfermions.norm_and_guess(transimg)

# choose starting values for fit
x, y, width_x, width_y = fitfuncs2D.gaussian_moments_2D(odimg)
guess = np.zeros(10.)
guess[0:4] = [com[0], com[1], width_x, width_y]
guess[4] = n0
guess[5:] = [q, 0., 0., 0., 0.]

# do the fit, and find temperature and number of atoms
ans = fitfuncs2D.fit2dfuncraw(fitfuncs2D.idealfermi_2D_angled, pwa, pwoa, df, guess, tol=1e-10)
ToverTF, N = fitfuncs2D.ideal_fermi_numbers_2D(ans, pixcal)

print ans
print 'T/TF = ', ToverTF[0]
print 'N = %1.2f million'%(N * 1e-6)

# show the fit residuals
# residuals = fitfuncs2D.residuals_2D(odimg, ans, smooth=4, showfig=True)


