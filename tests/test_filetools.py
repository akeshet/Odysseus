import os

from nose import SkipTest

from odysseus import filetools


class TestSortFilesByDate:
    def test_sort_files_by_date_emptylist(self):
        sortedlist = filetools.sort_files_by_date([])
        assert not sortedlist

    # not sure how best to test for correct sorting without assuming anything
    # about actual files on disc.


class TestGetFilesInDir:
    def test_get_files_in_dir_returntype(self):
        curdirlist = filetools.get_files_in_dir(os.curdir)
        assert isinstance(curdirlist, list)

    def test_get_files_in_dir_args(self):
        curdirlist = filetools.get_files_in_dir(os.curdir, ext='py',
                                                globexpr='*.py', sort=False)
        assert isinstance(curdirlist, list)