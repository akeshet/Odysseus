"""An example showing how to generate images.

Generating images can be very useful for testing fitting routines and for
finding out what an image is supposed to look like for a given set of
parameters.

"""

from odysseus.refimages import *
from odysseus import imageio, visualize


img = generate_image()

# add different types of noise
img1 = add_noise(img, ampl=0.05)
img2 = add_noise(img, noisetype='linear_x', ampl=0.05)
img3 = add_noise(img, noisetype='linear_y', ampl=0.025)
img4 = add_noise(img1, noisetype='linear_x', ampl=0.05)
img5 = add_noise(img4, noisetype='linear_y', ampl=0.02)
fringeargs = (np.pi/3, 0.03, (60, 50), 70)
img5 = add_noise(img5, noisetype='fringes', ampl=0.15, fringeargs=fringeargs)

# set to True to show all images
if False:
    for element in [img, img1, img2, img3, img4, img5]:
        visualize.show_transimg(element)

# set to true to save reference images
if False:
    imageio.save_tifimage(img, 'no_noise', dirname='ref_images')
    imageio.save_tifimage(img1, 'random_noise', dirname='ref_images')
    imageio.save_tifimage(img2, 'linearx_noise', dirname='ref_images')
    imageio.save_tifimage(img3, 'lineary_noise', dirname='ref_images')
    imageio.save_tifimage(img4, 'randompluslinear_noise', dirname='ref_images')
    imageio.save_tifimage(img5, 'allkindsof_noise', dirname='ref_images')

# create another image with different parameters
central_od, a, bprime = idealfermi_fitparams(0.1, 5e6, tof=3e-3)
img6 = generate_image(ODmax=central_od, fugacity=a, cloudradius=bprime)
img6 = add_noise(img6, ampl=0.1, noisetype='random')
img6 = stretch_img(img6, 1.2)

visualize.show_transimg(img6, showfig=True)