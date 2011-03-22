import os

from odysseus import imageio, imageprocess, texreport


pixcal = 10e-6  # 10 um/pix
dirname = 'datafiles'
tifname = 'raw9.11.2008 7;35;23 PM.TIF'
imgname = os.path.join(dirname, tifname)

rawframes = imageio.import_rawframes(imgname)
transimg, odimg = imageprocess.calc_absimage(rawframes)
# set the ROI
transimg = transimg[120:350, 50:275]

texreport.generate_report(rawframes, transimg, imgname, pixcal)
