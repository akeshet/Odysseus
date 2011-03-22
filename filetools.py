#!/usr/bin/env python
"""Functions to easily process file names."""

import os
import glob
import re


def sort_files_by_date(filelist, newestfirst=True):
    """Return a list of files sorted by time, newest first by default"""

    mod_time_file = [(os.lstat(item).st_mtime, item) for item in filelist]

    if newestfirst:
        mod_time_file.sort(reverse=True)
    else:
        mod_time_file.sort()

    return [file[1] for file in mod_time_file]


def get_files_in_dir(dirname, ext='TIF', globexpr=None, sort=True):
    """Return a list of all files in a directory with extension ext

    When ``globexpr`` is given, ``ext`` is ignored and the Python glob module
    is used to search for all files with the given pattern.

    **Inputs**

      * dirname: string, full path to the directory
      * ext: string, extension of the files to process
      * globexpr: string, glob search expression (can contain wildcards)
      * sort: bool, if True the results are sorted by file date/time, newest
        first

    **Outputs**

      * imgs: list of strings, each string in the list is the complete path to
        a file

    """

    if globexpr:
        imgs = glob.glob(os.path.join(dirname, ''.join(globexpr)))
    else:
        imgs = glob.glob(os.path.join(dirname, ''.join(['*.', ext])))
    if sort:
        imgs = sort_files_by_date(imgs)

    return imgs


def find_imgnames(imglist, startstr, stopstr):
    """Finds names from imglist between startstr and stopstr in time-ordered way

    **Inputs**

      * imglist: list of str, containing paths of images on disc
      * startstr: str, part of the name of the oldest image by date that is
                  wanted
      * stopstr: str, part of the name of the newest image by date that is
                  wanted

    **Outputs**

      * imgs: list of str, containing the found paths to image files

    """

    imgs = sort_files_by_date(imglist, newestfirst=False)
    for img in imgs:
        found_one = re.search(startstr, img)
        if found_one:
            start_idx = imgs.index(img)
            break
    for img in imgs:
        found_one = re.search(stopstr, img)
        if found_one:
            stop_idx = imgs.index(img)
            break

    return imgs[start_idx:stop_idx+1]