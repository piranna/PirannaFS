from os.path import abspath, dirname, join

import plugins

from pirannafs.base.fs import initDB

import backends.fuse
import backends.pyfilesystem

from base import BaseFile
from LL   import LL


class FilePlugin(plugins.Plugin):
    def __init__(self):
        self.db = None
        self.ll = None

        plugins.connect(self.FS__init__, "FS.__init__")

    def FS__init__(self, sender, db_file, drive_file, sector_size):
        self.ll = LL(drive_file, sector_size)

        self.db = initDB(db_file, join(dirname(abspath(__file__)), '..', '..',
                                  'pirannafs', 'sql'))
        self.db.parse_dir(join(dirname(abspath(__file__)), 'sql'), False, True)

        # http://stackoverflow.com/questions/283707/size-of-an-open-file-object
        drive = self.ll._file

        def Get_NumSectors():
            drive.seek(0, 2)
            end = drive.tell()
            drive.seek(0)
            return (end - 1) // sector_size

        self.db.create(length=Get_NumSectors(), sector=0)

        # Set the Dir objects to use the plugin database and low-level file
        # instances instead of the filesystem main ones
        BaseFile.db = self.db
        BaseFile.ll = self.ll

        module = sender.__class__.__module__
        if module == 'pirannafs.backends.fuse':
            return backends.fuse.File
        if module == 'pirannafs.backends.pyfilesystem':
            return backends.pyfilesystem.File
