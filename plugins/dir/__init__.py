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
        plugins.connect(self.link, "FS.link")
        plugins.connect(self.rename, "FS.rename")
        plugins.connect(self.unlink, "FS.unlink")

    def FS__init__(self, sender, db_file):
        self.db = initDB(db_file, join(dirname(abspath(__file__)), '..', '..',
                                  'pirannafs', 'sql'))
        self.db.parse_dir(join(dirname(abspath(__file__)), 'sql'), False, True)
        self.db.create(type=S_IFDIR)

        # Set the Dir objects to use the plugin database instance instead of
        # the filesystem main one
        BaseDir.db = self.db

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
