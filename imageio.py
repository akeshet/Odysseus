#!/usr/bin/env python
"""I/O functions for several image formats.

The relevant formats are TIF, hdf5 and ascii. For ascii and binary numpy formats
no separate functions are provided for saving an image. This is because saving
in these formats requires just a single command:
ascii: np.savetxt('filename', img)
binary (.npy): np.save('filename', img)

"""

import os

import numpy as np
import scipy as sp
# if available, use Zach Pincus' pil_lite which has correct 16-bit TIFF loading
try:
    import pil_lite.pil_core.Image as Image
except ImportError:
    import Image
#import tables


def list_of_frames(img_name):
    """Return the list of frames for an image file.

    Details are as described in the imgimport_intelligent docstring.

    """

    img = Image.open(img_name)
    imglist = []

    try:
        for i in xrange(8):
            if img.mode == 'I':
                imdata = np.asarray(img, dtype=np.int16)
            else:
                imdata = np.asarray(img, dtype=np.float32)
            # fix 3-channel TIFF images
            if np.rank(imdata)==3:
                imdata = imdata[:,:,0] + 256*imdata[:,:,1] + 65536*imdata[:,:,2]
            imglist.append(imdata)
            img.seek(i+1) # next frame
    except EOFError:
        pass

    if not imglist:
        raise ImportError, 'No frames detected in file %s' %img_name
    else:
        return imglist


def full_directory_import(directory_name, import_function):
    """Using imgimport_intelligent(img_name)
    imports every image in the specified directory
    
    **Inputs**
      * directory_name: string containing the directory 
      from which to open images
      
      * function with which to load the image
      
    **Outputs**
      (imgs, fnames)
      
      * imgs: a list containing all the image data arrays
      * fnames: a list containing file names corresponding to image data
      
      """
    
    names_list = os.listdir(directory_name);
    fnames = [os.path.join(directory_name,fname) for fname in names_list]
    fnames = [fname for fname in fnames if (os.path.isfile(fname) \
       and fname.upper().endswith(".TIF"))]
    
    imgs = []
    
    print("Importing {0} image(s)...".format(len(fnames)))
    
    for fname in fnames:
        im = import_function(fname)
        imgs.append(im)
    
    print("...done")
    
    return (imgs,fnames)
    
    
def full_directory_imgimport_intelligent(directory_name):
    """Using imgimport_intelligent(img_name)
    imports every image in the specified directory
    
    **Inputs**
      * directory_name: string containing the directory 
      from which to open images
      
      
    **Outputs**
      (imgs, fnames)
      
      * imgs: a list containing all the image data arrays
      * fnames: a list containing file names corresponding to image data
      
      """
    
    return full_directory_import(directory_name, imgimport_intelligent)



def imgimport_intelligent(img_name):
    """Opens an image file containing one or more frames

    The number of frames in the image is automatically detected. If it is a
    single frame, it is assumed to be a transmission image. If there are three
    frames, the first one is assumed to be probe with atoms (pwa), the second
    one probe without atoms (pwoa) and the third one a dark field (df).
    For four frames, it is assumed to be (pwoa, pwa, df1, df2).
    For six frames, the first two are discarded (they are for clearing the
    CCD charge on the Coolsnap camera), three to six are (pwoa, pwa, df1, df2)
    
    **Inputs**

      * img_name: string containing the full path to an image

    **Outputs**

      * img_array: 3D array, containing the three or four frames of the image,
                   in the  order (pwa, pwoa, df, df2).

    **Notes**

    The datatype has to be set to float in Winview, otherwise there is a
    strange problem reading the frames; support for 16-bit tif files is
    lacking a bit in PIL. Note: when pil_lite is available this does work.

    The same support is lacking in MS .Net apparently, hence the weird check
    for 3-channel TIFFs. What happens here is that XCamera can output multipage
    8-bit RGB TIFFs. Each page is of shape (M,N,3), where the 8-bit color
    channels combine to output 24-bit B/W data.

    """

    
    
    imglist = list_of_frames(img_name)

    if len(imglist)==1:
        return imglist[0]
    elif len(imglist) in [3, 4]:
        # make an array from the list of frames, with shape (img[0], img[1], 3)
        img_array = np.dstack(imglist)
    elif len(imglist)==6:
        # get rid of first two frames, they're junk. then swap pwoa, pwa.
        img_array = np.dstack([imglist[3], imglist[2], imglist[5], imglist[4]])
    elif len(imglist)==8:
        # get rid of first two frames, then 2x PWA, 2x DF, 2x PWOA (swap DF, PWOA)
        img_array = np.dstack([imglist[2], imglist[3], imglist[6], imglist[7],
                               imglist[4], imglist[5]])
    else:
        raise ImportError, 'Number of frames is %s' %(len(imglist))

    return img_array


def import_kinetics_mode_image(img_name, with_top=128, without_top=256,\
    im_height=63):
        
    """Opens an image file which was taken using a kinetix mode camera,
    returning an array which contains the (pwa, pwoa, df, df2)
    
    Assumptions:
    The first subframe is assumed to be a junk throwaway frame.
    The second subframe contains the images with atoms.
    The third subframe contains the dark fields.
    
    
        **Inputs**

      * img_name: string containing the full path to an image
      * with_top: location of the top of the pwa section of the subframe
      * without_top: location of the top of the pwoa section of the subframe
      * im_height: height of the pwa and pwoa (and df, df2) sections

    **Outputs**

      * img_array: 3D array, containing the three or four frames of the image,
                   in the  order (pwa, pwoa, df, df2).
                   
    """
    
    # first of all use img_import_intelligent to load the file
    imraw = imgimport_intelligent(img_name)
    
    pwa = imraw[with_top:with_top+im_height, :, 1]
    df  = imraw[with_top:with_top+im_height, :, 2]
    pwoa = imraw[without_top:without_top+im_height, :, 1]
    df2 = imraw[without_top:without_top+im_height, :, 2]
    
    return np.dstack([pwa, pwoa, df, df2])

def import_rawframes(img_name):
    """Opens an image file containing three frames

    The datatype has to be set to float in Winview, otherwise there is a
    strange problem reading the frames; support for 16-bit tif files is
    lacking a bit in PIL.

    **Inputs**

      * img_name: string containing the full path to an image

    **Outputs**

      * img_array: 3D array, containing the three frames of the image

    """

    img = Image.open(img_name)
    # note the reversed order because Image and asarray have reversed order
    img_array = np.zeros((img.size[1], img.size[0], 3), dtype=np.float32)

    img_array[:, :, 0] = np.asarray(img, dtype=np.float32)
    try:
        img.seek(1) # next frame
        img_array[:, :, 1] = np.asarray(img, dtype=np.float32)
        img.seek(2) # next frame
        img_array[:, :, 2] = np.asarray(img, dtype=np.float32)
    except EOFError:
        print 'This image contains less than 3 frames'
        return None

    return img_array


def import_rawimage(img_name):
    """Opens an image file and returns it as an array."""

    im = Image.open(img_name)

    return np.asarray(im)


def import_xcamera(img_name, ext='xraw'):
    """Load the three .xraw files from XCamera

    It is assumed that the file with extension .xraw0 contains the probe
    with atoms (pwa), the one with extension .xraw1 the probe without atoms
    (pwoa), and the one with extension .xraw2 the dark field (df).

    **Inputs**

      * img_name: str, name of the image with or without extension
                  (the extension is stripped and replaced by `ext`.
      * ext: str, the extension of the XCamera file. Normally xraw or xroi.

    **Outputs**

      * raw_array: 3D array, containing the three raw frames (pwa, pwoa, df)

    """

    if ext=='xraw':
        rawext = ['.xraw0', '.xraw1', '.xraw2']
    elif ext=='xroi':
        rawext = ['.xroi0', '.xroi1', '.xroi2']
    else:
        raise ValueError, 'Unknown extension for XCamera file'

    basename = os.path.splitext(img_name)[0]
    try:
        pwa = np.loadtxt(''.join([basename, rawext[0]]), dtype=np.int16)
        pwoa = np.loadtxt(''.join([basename, rawext[1]]), dtype=np.int16)
        df = np.loadtxt(''.join([basename, rawext[2]]), dtype=np.int16)
    except IOError, e:
        print e
        return None

    raw_array = np.dstack([pwa, pwoa, df])

    return raw_array


def save_tifimage(imgarray, fname, dirname=None):
    """Save a single image in TIF format

    **Inputs**

      * imgarray: 2D array, containing a single frame image
      * fname: str, filename of the file to save, optionally including
               the full path to the directory
      * dirname: str, if not None, fname will be appended to dirname to
                 obtain the full path of the file to save.

    **Notes**

    Multiple frame tif images are not supported. For such data hdf5 is the
    recommended format.

    """

    if dirname:
        fname = os.path.join(dirname, fname)
    fname = ''.join([os.path.splitext(fname)[0], '.tif'])

    im = sp.misc.toimage(imgarray, mode='F')
    im.save(fname, mode='F')


def save_hdfimage(imgarray, fname, dirname=None):
    """Save an image to an hdf5 file

    **Inputs**

      * imgarray: ndarray, containing the image data. If the array is 2D,
                  it is assumed that this is a single frame image. If it is
                  3D, the frames will be saved as separate arrays:
                  ('pwa', 'pwoa', 'df'), and if there is a fourth frame this
                  is df2.
      * fname: str, filename of the file to save, optionally including
               the full path to the directory
      * dirname: str, if not None, fname will be appended to dirname to
                 obtain the full path of the file to save.

    """

    if dirname:
        fname = os.path.join(dirname, fname)
    fname = ''.join([os.path.splitext(fname)[0], '.h5'])

    # Open a new empty HDF5 file
    h5file = tables.openFile(fname, mode='w')

    if len(imgarray.shape)==2:
        # Get the root group
        root = h5file.root
        # Save image in the HDF5 file
        h5file.createArray(root, 'img', imgarray, title='Transmission image')

    elif len(imgarray.shape)==3:
        # image frames to be saved
        pwa = imgarray[:, :, 0]
        pwoa = imgarray[:, :, 1]
        df = imgarray[:, :, 2]
        # Get the root group
        root = h5file.createGroup("/", 'rawframes', 'The raw image frames')
        # Save image in the HDF5 file
        h5file.createArray(root, 'pwa', pwa, title='Probe with atoms')
        h5file.createArray(root, 'pwoa', pwoa, title='Probe without atoms')
        h5file.createArray(root, 'df', df, title='Dark field')

        if imgarray.shape[2] > 3:
            df2 = imgarray[:, :, 3]
            h5file.createArray(root, 'df2', df2, title='Dark field 2')

    else:
        print 'imgarray does not have the right dimensions, shape is: ', \
              imgarray.shape

    h5file.close()


def load_hdfimage(fname, dirname=None, ext_replace=True):
    """Load an image from an hdf5 file

    **Inputs**

      * fname: str, filename of the file to save, optionally including
               the full path to the directory
      * dirname: str, if not None, fname will be appended to dirname to
                 obtain the full path of the file to save.
      * ext_replace: bool, if True replaces the extension of fname with `.h5`

    **Outputs**

      * transimg: ndarray, the image data

    """

    if dirname:
        fname = os.path.join(dirname, fname)
    if ext_replace:
        fname = ''.join([os.path.splitext(fname)[0], '.h5'])

    h5file = tables.openFile(fname, mode='r')

    try:
        transimg = np.asarray(h5file.root.img)
        return transimg

    except tables.NoSuchNodeError:
        pwa = np.asarray(h5file.root.rawframes.pwa)
        pwoa = np.asarray(h5file.root.rawframes.pwoa)
        df = np.asarray(h5file.root.rawframes.df)
        imgarray = np.dstack([pwa, pwoa, df])
        return imgarray

    finally:
        h5file.close()


def convert_xcamera_to_hdf5(imglist, ext='xraw'):
    """Convert every file in imglist to an hdf5 file.

    The raw files are saved in the hdf5 file as
    `root.rawframes.pwa`, `root.rawframes.pwoa`, `root.rawframes.df`.
    Their dtype is uint16, which results in files of a third smaller than
    the xcamera text files.

    **Inputs**

      * imglist: list of str, paths to .xraw0 files
      * ext: str, the extension of the XCamera file. Normally xraw or xroi.

    """

    for img in imglist:
        imgarray = import_xcamera(img, ext=ext)
        save_hdfimage(imgarray, img)