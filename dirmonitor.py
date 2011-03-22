#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.


"""A directory monitoring daemon class.

Pass in a directory, it will monitor this for incoming image files. If it
detects any changes it emits a "changed" signal, which can be used by the
main program to react to the change.

This daemon is adapted from `dirmon`, which can be found on PyPi.

"""


import os
import re
import sys
import fnmatch
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Walker(QThread):

    def __init__(self, lock, parent=None):
        super(Walker, self).__init__(parent)
        self.lock = lock
        self.waiting = False
        self.stop = False
        self.mutex = QMutex()
        self.path = None
        self.mtimes = {}


    def setPath(self, path):
        try:
            self.mutex.lock()
            self.path = path
        finally:
            self.mutex.unlock()


    def getPath(self):
        try:
            self.mutex.lock()
            return self.path
        finally:
            self.mutex.unlock()


    def setWaiting(self, waiting):
        try:
            self.mutex.lock()
            self.waiting = waiting
        finally:
            self.mutex.unlock()


    def isWaiting(self):
        try:
            self.mutex.lock()
            return self.waiting
        finally:
            self.mutex.unlock()


    def setStopped(self):
        try:
            self.mutex.lock()
            self.stop = True
        finally:
            self.mutex.unlock()


    def run(self):
        """Is called by QThread.start(), when returning stops complete thread"""

        while not self.stop:
            if not self.waiting:
                print 'starting'
                self.processFiles(self.getPath())
                print 'halted'
            self.msleep(100)


    def changed(self, filename):
        """`filename` needs to be a list."""
        self.emit(SIGNAL("changed"), filename)


    def processFiles(self, path):
        """Note: only .TIF files are monitored"""

        # create initial list of filenames and creation times
        filenames = fnmatch.filter(os.listdir(path), '*.TIF')
        for filename in filenames:
            filename = os.path.join(path, filename)
            self.mtimes[filename] = os.path.getmtime(filename)

        while True:
            if self.isWaiting():
                return
            previous_mtimes = dict(self.mtimes)
            created = {}
            checked = {}

            # check for any changes to .TIF files
            filenames = fnmatch.filter(os.listdir(path), '*.TIF')
            for filename in filenames:
                if self.isWaiting():
                    return
                filename = os.path.join(path, filename)
                try:
                    new_mtime = os.path.getmtime(filename)
                    checked[filename] = new_mtime
                    if filename not in self.mtimes:
                        created[filename] = new_mtime
                    elif new_mtime - self.mtimes[filename] > 2:
                        # really new data, not just detected twice while writing
                        self.msleep(300) # wait to be sure writing is done
                        self.changed([filename])
                    self.mtimes[filename] = new_mtime
                except OSError:
                    # file was removed after creating filelist
                    pass

            # handle files that were removed, do not call changed()
            removed = set(previous_mtimes.items()) - set(checked.items())
            if removed:
                if created:
                    created_reversed = dict([(mtime, fn) for fn, mtime in \
                                             created.iteritems()])
                    for old_fn, old_mtime in removed:
                        if old_mtime in created_reversed:
                            del created[created_reversed[old_mtime]]
                        else:
                            pass
                        del self.mtimes[old_fn]
                else:
                    for fn, mtime in removed:
                        del self.mtimes[fn]

            # call changed() for new/modified file(s) so display gets updates
            if created:
                #send list of new files
                self.changed(list(created))
            self.msleep(300)