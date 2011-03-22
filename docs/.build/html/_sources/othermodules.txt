Other modules
=============

The smaller modules that are part of Odysseus and do not warrant a more extensive description (yet) are documented in this section.

filetools
---------

This module contains a few convenience functions to work with the file system. String handling and interaction with the operating system is easy to do in Python, and processing directories of files (or selections out of them) can be done with the help of this module.

.. automodule:: odysseus.filetools
   :members:

polylog
-------

Polylog contains approximate algorithms for the polylog functions Li_2, Li_{5/2} and Li_3, as well as their bosonic equivalents. They were originally written by Martin Zwierlein for the Igor data analysis software.

.. automodule:: odysseus.polylog
   :members: fermi_poly3, fermi_poly2

lerch
-----

Lerch contains a correct implementation of the polylog function *Li(s,z)* for arbitrary *s* and *z*. It is quite slow and therefore not used in Odysseus' fitting routines, but nevertheless important to check the correctness of the approximate algorithm.