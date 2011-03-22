#!/usr/bin/env python
"""Run all examples in the example directory

If an example fails, an error is raised. This is useful when checking if
everything still works the way it is supposed to.

"""

import subprocess

import odysseus.filetools as filetools


dirname = '.'

# get all the names of python files
examples = filetools.get_files_in_dir('.', globexpr='example_*.py')

for example in examples:
    print '\n', 'running ', example
    retcode = subprocess.call(['python', example])

    if retcode:
        print '\n', 'An error occurred while running: '.upper(), example, '\n'
        raise RuntimeError





