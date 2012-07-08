from os.path import abspath, dirname, join
from stat    import S_IFDIR

import plugins

from pirannafs.base.fs import initDB

from pydispatch.dispatcher import connections, getAllReceivers

import backends.fuse
import backends.pyfilesystem

from base import BaseDir


class DirPlugin(plugins.Plugin):
    def __init__(self):
        self.db = None

        plugins.connect(self.FS__init__, "FS.__init__")
#        plugins.connect(self.list, "FS.dir.list")

    def FS__init__(self, sender, db_file):
        db = initDB(db_file, join(dirname(abspath(__file__)), '..', '..',
                                  'pirannafs', 'sql'))
        db.parse_dir(join(dirname(abspath(__file__)), 'sql'), False, True)
        db.create(type=S_IFDIR)

        # Set the Dir objects to use the plugin database instance instead of
        # the filesystem main one
        BaseDir.db = db

        module = sender.__class__.__module__
        if module == 'pirannafs.backends.fuse':
            return backends.fuse.Dir
        if module == 'pirannafs.backends.pyfilesystem':
            return backends.pyfilesystem.Dir

#    def list(self, path):
#        print "*************list 1"
#        for direntry in self.db.readdir(parent_dir=self._inode, limit= -1):
#            if direntry.name:
#                yield unicode(direntry.name)
#        print "list 2"