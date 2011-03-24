import sqlite3
import unittest

from fs.filelike import StringIO
from fs.tests import FSTestCases, ThreadingTestCases

from PirannaFS.pyfilesystem import FileSystem


#class TestPirannaFS(unittest.TestCase, FSTestCases):
class TestPirannaFS(unittest.TestCase, FSTestCases, ThreadingTestCases):

    def setUp(self):
#        db = sqlite3.connect('../../../test/db.sqlite')
#        drive = '../../../test/disk_part.img'
        db = sqlite3.connect(':memory:', check_same_thread=False)
#        db = sqlite3.connect(':memory:')
        drive = StringIO("\0" * 3 * 1024 * 1024)
        sector_size = 512

        self.fs = FileSystem(db, drive, sector_size)


if __name__ == '__main__':
    unittest.main()