from os.path import abspath, dirname, join

import plugins

from pirannafs.base.fs import initDB

import backends.fuse
import backends.pyfilesystem

from base import BaseFile


class FilePlugin(plugins.Plugin):
    def __init__(self):
        self.db = None

        plugins.connect(self.FS__init__, "FS.__init__")
        plugins.connect(self.open, "File.open")

    def FS__init__(self, sender, db_file):
        self.db = initDB(db_file, join(dirname(abspath(__file__)), '..', '..',
                                  'pirannafs', 'sql'))
        self.db.parse_dir(join(dirname(abspath(__file__)), 'sql'), False, True)
        self.db.create(length=3071, sector=0)

        # Set the Dir objects to use the plugin database instance instead of
        # the filesystem main one
        BaseFile.db = self.db

        module = sender.__class__.__module__
        if module == 'pirannafs.backends.fuse':
            return backends.fuse.File
        if module == 'pirannafs.backends.pyfilesystem':
            return backends.pyfilesystem.File

    def open(self, mode="r", **kwargs):
        pass
