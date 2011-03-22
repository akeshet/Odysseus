Odysseus development
====================

This section describes the development of Odysseus itself. If all you want to do is use Odysseus to fit your data, you can skip this section.

Organization of the code
------------------------

The way the code is organized is pretty much clear from the way the files are named. All functions used to fit optical density distributions live in :mod:`fitfuncs`. All code related to handling images - this includes reading/writing images, normalizing, smoothing, etc. - lives in the modules :mod:`imageio` and :mod:`imageprocess`. The main user interface, i.e. high-level functions like :func:`fitfermions.fit_img`, is :mod:`fitfermions`. These files form the core of Odysseus, further there are some files to generate images and do consistency checks on the results. The user documentation is written in reStructuredText (reST), the source files live in the `docs` directory and the html and pdf docs live under the .build directory.

Here is a visual representation of the source code. Higher levels depend on lower levels but not the other way around, i.e. blue modules have no dependencies on other Odysseus code.

.. image:: .images/dependency_graph.png
   :width: 500pt
   :target: _images/dependency_graph.png

Documentation
-------------

New code should be well-documented, no exceptions. All functions require docstrings in the following form

.. code-block:: python
   :linenos:

   def function_name(in1, in2, in3=None):
       """A one-line summary of what the function does, without func name in it

       A paragraph with a more detailed explanation ...

       **Inputs**

         * in1: type(in1), is the independent variable
         * in2: type(in2), is fit parameter with values between a and b

       **Outputs**

        * out1: etc
        * out2: ...

       **Optional inputs**

        * in3: type(in3), this does ...

       **References**

       [1] Title, author, publication, year

       """

The one-line summary and lists of inputs/outputs are mandatory, the rest is optional. If significant new features are added, they should also be described in this documentation, which is generated with `Sphinx <http://sphinx.pocoo.org>`_.

The documentation can be built with the Makefile in the source directory. For generating html use the command ``make html`` in that directory, for pdf use ``make latex`` in the source directory followed by ``make all-pdf`` in the directory ``.build/latex/``.

Tests
-----

The test coverage is not yet very good, but all new code should be covered by tests. Unit testing is done with the `nose <http://somethingaboutorange.com/mrl/projects/nose/>`_ testing framework. This should take care of low-level testing, i.e. if functions give the correct result for known inputs, and if they take the right parameters. All unit tests can be run by use of the command

.. code-block:: none

  $ nosetests

in the base directory of the code. For new code, a convenient way to stub out all the required unit tests is to run `Pythoscope <http://pythoscope.org/>`_.

High level testing is done by running all the examples, with the ``run_examples.py`` script.

To see which lines of a particular module are exercised by the tests, we can run `nose` with the `coverage.py <http://somethingaboutorange.com/mrl/projects/nose/>`_ tool enabled:

.. code-block:: none

  $ nosetests --with-coverage --cover-package=polylog

This will typically result in output like this:

.. code-block:: none

  Name      Stmts   Exec  Cover   Missing
  ---------------------------------------
  polylog     107     45    42%   81-108, 161-184, 190-193, 201-210, 216-225
  ----------------------------------------------------------------------

Version control with Mercurial
------------------------------

We use the distributed version control system `Mercurial <http://www.selenic.com/mercurial/wiki/>`_ for developing Odysseus. The basic idea is that each developer has his own brach(es) on his own computer, and when he/she completes a feature *(that means including docstrings, documentation and ideally tests)* it is pushed to the central repository on Naboo. If it is something significant, please tell the other developers.

The basic workflow can look like this:

.. code-block:: none

   $ hg clone //naboo/personal/ralf/odysseus local_repo

This gives you a local copy of the main repo. It is important to understand what effect the commands you use will have, therefore remember that ``hg help`` is your friend. To inspect the status of your files use the following commands on the command line

.. code-block:: none

   $ hg log
   changeset:   43:7abaa4075238
   tag:         tip
   user:        Ralf Gommers <ralf.gommers@googlemail.com>
   date:        Tue Jun 10 02:39:48 2008 -0400
   summary:     Finished up normalization and checks of radial profiles, including docstrings.
   ...

   $ hg status
   M fitfuncs.py
   M image_treatment.py
   M index.rst
   M introduction.rst
   ? development.rst

   $ hg incoming
   comparing with /home/ralf/smb4k/NABOO/PERSONAL/ralf/odysseus
   searching for changes
   no changes found

If there are changes in the main repo you can pull them into your local repo, and then merge those changes with the ones you made locally

.. code-block:: none

   $ hg pull //naboo/personal/ralf/odysseus
   $ hg merge

Then when all seems happy, commit your changes (with a good commit message describing what the hell everything does!) and push them to the main repo

.. code-block:: none

   $ hg commit
   $ hg push //naboo/personal/ralf/odysseus

For more details, please have a look at this `tutorial <http://www.selenic.com/mercurial/wiki/index.cgi/Tutorial>`_ and the rest on the information on the Mercurial site. Also, play with Mercurial a bit on your own computer before you try to push to the central repository!

Debugging
---------

When there is a problem in a script, running it with IPython gives nicely color-coded tracebacks. These are usually good enough to tell you what the problem is. The Odysseus GUI catches a lot of exceptions to make sure that the whole program does not crash when for example a fit fails. Any exceptions that are not explicitly caught in the code generate a html log file in the directory ``logs`` in the source tree. These can be viewed with any browser.