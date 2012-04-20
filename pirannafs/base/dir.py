'''
Created on 02/04/2011

@author: piranna
'''

from os.path import split
from stat    import S_IFDIR

from pirannafs.errors import DirNotFoundError, NotADirectoryError
from pirannafs.errors import ParentDirectoryMissing, ResourceError
from pirannafs.errors import ResourceNotFound

import plugins


class BaseDir(object):
    '''
    classdocs
    '''

    def __init__(self, fs, path):
        '''
        Constructor
        '''
        # Get the inode of the parent or raise ParentDirectoryMissing exception
        parent_path, self.name = split(path)

        try:
            self.parent = fs._Get_Inode(parent_path)

        except (ParentDirectoryMissing, ResourceNotFound):
            self.parent = parent_path
            self._inode = None

        else:
            try:
                self._inode = fs._Get_Inode(self.name, self.parent)

            except (ResourceError, ResourceNotFound):
                self._inode = None

            else:
                # If inode is not a dir, raise error
                if fs.db.Get_Mode(inode=self._inode) != S_IFDIR:
                    raise NotADirectoryError(path)

        self.fs = fs
        self.db = fs.db

        self.path = path

    def _list(self):
        """Lists the files and directories under a given path.
        The directory contents are returned as a list of unicode paths.

        @rtype: iterable of paths

        @raise ResourceNotFound: directory doesn't exists
        """
        if self._inode == None:
            raise DirNotFoundError(self.path)

        plugins.send("Dir.list begin")

#        yield unicode('.')
#        yield unicode('..')

        for dir_entry in self.db.readdir(parent_dir=self._inode, limit= -1):
            if dir_entry.name:
                yield unicode(dir_entry.name)

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