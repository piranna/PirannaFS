from os.path import abspath, dirname, join, sep
from stat    import S_IFDIR

import plugins

from pirannafs.base.fs import initDB
from pirannafs.errors  import FileNotFoundError
from pirannafs.errors  import ParentDirectoryMissing, ParentNotADirectoryError

from pydispatch.dispatcher import connections, getAllReceivers

import backends.fuse
import backends.pyfilesystem

from base import BaseDir


class DirPlugin(plugins.Plugin):
    def __init__(self):
        self.db = None

        plugins.connect(self.FS__init__, "FS.__init__")

    def FS__init__(self, sender, db_file):
        self.db = initDB(db_file, join(dirname(abspath(__file__)), '..', '..',
                                  'pirannafs', 'sql'))
        self.db.parse_dir(join(dirname(abspath(__file__)), 'sql'), False, True)
        self.db.create(type=S_IFDIR)

        # Set the Dir objects to use the plugin database instance instead of
        # the filesystem main one
        BaseDir.db = self.db

        plugins.connect(self.link, "FS.link")
        plugins.connect(self.rename, "FS.rename")
        plugins.connect(self.unlink, "FS.unlink")

        plugins.connect(self._Get_Inode, "Dir._Get_Inode")

        module = sender.__class__.__module__
        if module == 'pirannafs.backends.fuse':
            return backends.fuse.Dir
        if module == 'pirannafs.backends.pyfilesystem':
            return backends.pyfilesystem.Dir

    def link(self, parent_dir, name, child_entry):
        self.db.link(parent_dir=parent_dir, name=name, child_entry=child_entry)

    def rename(self, parent_old, name_old, parent_new, name_new):
        self.db.rename(parent_old=parent_old, name_old=name_old,
                       parent_new=parent_new, name_new=name_new)

    def unlink(self, parent_dir, name):
        self.db.unlink(parent_dir=parent_dir, name=name)

    def _Get_Inode(self, path, inode=0):                                   # OK
        '''
        Get the inode of a path
        '''
#        print >> sys.stderr, '*** _Get_Inode', repr(path),inode

        # If there are path elements
        # get their inodes
        if path:
            parent, _, path = path.partition(sep)

            # Get inode of the dir entry
            inode = self.db.Get_Inode(parent_dir=inode, name=parent)

            # If there's no such dir entry, raise the adecuate exception
            # depending of it's related to the resource we are looking for
            # or to one of it's parents
            if inode == None:
                if path:
                    raise ParentDirectoryMissing(parent)
                raise FileNotFoundError(parent)

            # If the dir entry is a directory
            # get child inode
            if self.db.Get_Mode(inode=inode) == S_IFDIR:
                return self._Get_Inode(path, inode)

            # If inode is not a directory and is not the last path element
            # return error
            if path:
                raise ParentNotADirectoryError(path)

        # Path is empty, so
        # * it's the root path
        # * or we consumed it
        # * or it's not a directory and it's the last path element
        # so return computed inode
        return inode
