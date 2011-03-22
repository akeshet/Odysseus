Image handling
==============

All I/O related code, i.e. loading and saving, images lives in the :mod:`imageio` module. The code for processing images lives in :mod:`imageprocess`. Some functionality is independent of the type of image, for example smoothing, thresholding and interpolation. Other functionality is specific to cold atom experiments, for example calculating optical density and transmission for absorption images.

.. automodule:: odysseus.imageio
   :members:
   
.. automodule:: odysseus.imageprocess
   :members: