from os.path import split
from stat    import S_IFDIR

import plugins

from pirannafs.base.inode import Inode
from pirannafs.errors     import DirNotFoundError, NotADirectoryError
from pirannafs.errors     import ParentDirectoryMissing, ResourceNotFound
from pirannafs.PluginDB   import PluginDB


class BaseDir(Inode):
    def __init__(self, fs, path):
        self.path = path
        self.parent, self.name = split(path)

        self.fs = fs
        self.db = fs.db

        # Get the inode of the parent or raise ParentDirectoryMissing exception
        try:
            self.parent = fs._Get_Inode(self.parent)
            inode = fs._Get_Inode(self.name, self.parent)
        except (ParentDirectoryMissing, ResourceNotFound):
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


class DirPlugin(plugins.Plugin):
    def __init__(self):
        print "*************DirPlugin"
        plugins.connect(self.FS__init__, "FS.__init__")
        plugins.connect(self.list, "FS.dir.list")

#    def __del__(self):
#        print "*************DirPlugin"
#        disconnect(self.FS__init__, "FS.__init__")
#        disconnect(self.list, "FS.dir.list")
#        disconnect(self.prueba, "FS.dir.list")

    def FS__init__(self, db):
#        print '*** create', db

        self.db = PluginDB('dir', db)
        self.db.create(type=S_IFDIR)

    def list(self, path):
        print "*************list 1"
        for direntry in self.db.readdir(parent_dir=self._inode, limit= -1):
            if direntry.name:
                yield unicode(direntry.name)
        print "list 2"