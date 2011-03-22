.. _writing-plugins:

The GUI plugin system
=====================

Odysseus contains a very straightforward plugin system that allows users to add
their own data analysis functionality. Basically, what is needed is a plain text
file to register the plugin and a python file with the analysis code.
Users can then right-click on images in the image grid at the bottom of the GUI,
and select the plugin from a popup list. The image will be passed to the plugin,
where the results of the data analysis can be easily plotted in a popup window.

The plugin system is based on `Yapsy <http://yapsy.sourceforge.net/>`_, for the
details of the design please check the documentation on the Yapsy wesite.


Plugin info file format
-----------------------

The plugin info file gathers, as its name suggests, some basic
information about the plugin. On one hand it gives crucial information
needed to be able to load the plugin. On the other hand it provided
some documentation like information like the plugin author's name and
a short description fo the plugin functionality. The info file
should have the extension `.odysseus-plugin`.

Here is an example of what such a file should contain::

 [Core]
 Name = Demo Plugin
 Module = demo_plugin

 [Documentation]
 Author = Ralf
 Version = 0.1
 Website = None
 Description = A simple plugin useful for basic testing


Plugin Python file
------------------

The plugin should have extension `.py` and contain a class that
is a subclass of DialogPlugin. The
`main()` method of this class is executed when the plugin is used from the
GUI. Inside the `main()` function a matplotlib figure and axes instance are
available as `self.fig` and `self.ax` respectively.

The following is an example of a basic plugin:

.. code-block:: python
   :linenos:

   import numpy as np
   from plugins import DialogPlugin

   class DemoPlugin(DialogPlugin):
       """Demonstrates the basics of the plugin system"""

       def main(self, img):
           """Plot the average pixel intensity in each image row"""

           x = np.arange(img.shape[0])
           y = img.mean(axis=1)

           self.ax.plot(x, y)


The easiest thing to do is to copy the code above and simply change the contents
of the `main()` function to something more useful.

