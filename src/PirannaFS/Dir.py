'''
Created on 02/04/2011

@author: piranna
'''

from os.path import split

from fs.errors import ParentDirectoryMissingError, ResourceNotFoundError

import plugins


class BaseDir(object):
    '''
    classdocs
    '''


    def __init__(self, fs, path):
        '''
        Constructor
        '''
        self.fs = fs
        self.db = fs.db

        self.path = path
        path, self.name = split(path)

        try:
            self.parent = fs.Get_Inode(path)
        except (ParentDirectoryMissingError, ResourceNotFoundError):
            self.parent = path


    def isempty(self):
        """Check if a directory is empty (contains no files or sub-directories)

        @rtype: bool
        """
#        print "BaseDir.isempty"
        return self.db.readdir(parent_dir=self._inode, limit=1)


    def _list(self):
        """Lists the files and directories under a given path.
        The directory contents are returned as a list of unicode paths.

        @rtype: iterable of paths

        @raise ResourceNotFoundError: directory doesn't exists
        """
        if self._inode == None:
            raise ResourceNotFoundError(self.path)

        plugins.send("Dir.list begin")

#        yield unicode('.')
#        yield unicode('..')

        for dir_entry in self.db.readdir(parent_dir=self._inode, limit= -1):
            if dir_entry['name']:
                yield unicode(dir_entry['name'])

        plugins.send("Dir.list end")


    #
    # File-like interface
    #

    def close(self):
        pass

    def next(self):
        data = self.readline()
        if data:
            return data
        raise StopIteration


    readline = _list

    def readlines(self):
        """Return a list of all lines in the file."""
        return list(self._list())


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __iter__(self):
        return self