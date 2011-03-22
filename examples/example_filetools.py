import odysseus.filetools as filetools


dirname = 'datafiles'

# get all the names of files with extension .TIF, by default sorted by date
imgnames = filetools.get_files_in_dir(dirname)
print imgnames

# get all the names of python files
pythonnames = filetools.get_files_in_dir('..', globexpr='*.py', sort=False)
# sort files by date, newest first
pythonnames_sorted = filetools.sort_files_by_date(pythonnames, newestfirst=True)

for pyname in pythonnames_sorted:
    print pyname




