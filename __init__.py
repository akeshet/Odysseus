"""This is the top level package for Odysseus.

Odysseus contains functionality to handle images containing data from cold
atom experiments. It also contains a graphical user interface (GUI) with
automatic data fitting capabilities.

"""


import imageio
import imageprocess
import filetools
import fitfermions
import fitfuncs
import centerofmass
import refimages
import polylog
import visualize
import lerch
from analysis import *


__all__ = ["imageio", "imageprocess", "filetools", "fitfermions", "fitfuncs",
           "centerofmass", "lerch", "polylog", "refimages", "texreport",
           "visualize", "analysis"]