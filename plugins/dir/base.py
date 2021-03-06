'''
Created on 08/07/2012

@author: piranna
'''
from os.path import split
from stat    import S_IFDIR

import plugins

from pirannafs.base.inode import Inode
from pirannafs.errors     import FileNotFoundError, NotADirectoryError
from pirannafs.errors     import ParentDirectoryMissing

from plugins import send


class BaseDir(Inode):
    db = None

    def __init__(self, fs, path):
        self.path = path
        self.parent, self.name = split(path)

        self.fs = fs

        # Get the inode of the parent or raise ParentDirectoryMissing exception
        try:
            self.parent = send('Dir._Get_Inode', path=self.parent)[0][1]
            inode = send('Dir._Get_Inode', path=self.name,
                                           inode=self.parent)[0][1]
        except (FileNotFoundError, ParentDirectoryMissing):
            inode = None

        Inode.__init__(self, inode)

        # If inode is not a dir, raise error
        if inode and fs.db.Get_Mode(inode=inode) != S_IFDIR:
            raise NotADirectoryError(path)

    def _list(self):
        """Lists the files and directories under a given path.
        The directory contents are returned as a generator of unicode paths.

        @rtype: generator of paths

        @raise DirNotFoundError: directory doesn't exists
        """
        if self._inode == None:
            raise FileNotFoundError(self.path)

        plugins.send("Dir.list begin")

#        yield unicode('.')
#        yield unicode('..')

        for direntry in self.db.read(parent_dir=self._inode, limit= -1):
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
