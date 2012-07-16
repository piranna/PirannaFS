from os.path import abspath, dirname, join

from plugins import connect, Plugin

from pirannafs.base.fs import initDB

import backends.fuse
import backends.pyfilesystem

from base import BaseFile
from LL   import LL


class FilePlugin(Plugin):
    def __init__(self):
        self.db = None
        self.ll = None

        connect(self.FS__init__, "FS.__init__")

    def FS__init__(self, sender, db_file, drive_file):
        self.ll = LL(drive_file)

        pwd = dirname(abspath(__file__))
        self.db = initDB(db_file, join(pwd, '..', '..', 'pirannafs', 'sql'))
        self.db.parse_dir(join(pwd, 'sql'), False, True)

        self.db.create(length=self.ll.Get_NumSectors(), sector=0)

        # Set the Dir objects to use the plugin database and low-level file
        # instances instead of the filesystem main ones
        BaseFile.db = self.db
        BaseFile.ll = self.ll

        module = sender.__class__.__module__
        if module == 'pirannafs.backends.fuse':
            return backends.fuse.File
        if module == 'pirannafs.backends.pyfilesystem':
            return backends.pyfilesystem.File
