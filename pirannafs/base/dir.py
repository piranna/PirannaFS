'''
Created on 02/04/2011

@author: piranna
'''

from stat import S_IFDIR

from pirannafs.errors import DirNotFoundError, NotADirectoryError

from direntry import DirEntry

import plugins


class BaseDir(DirEntry):
    '''
    classdocs
    '''

    def __init__(self, fs, path):
        '''
        Constructor
        '''
        # Get the inode of the parent or raise ParentDirectoryMissing exception
        DirEntry.__init__(self, fs, path)

        # If inode is not a dir, raise error
        if self._inode and fs.db.Get_Mode(inode=self._inode) != S_IFDIR:
            raise NotADirectoryError(path)

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

        for direntry in self.db.readdir(parent_dir=self._inode, limit= -1):
            if direntry.name:
                yield unicode(direntry.name)

        plugins.send("Dir.list end")


    #
    # File-like interface
    #

    def close(self):
        pass

    readline = _list

    def readlines(self):
        """Return a list of all lines in the file."""
        return list(self._list())
