import os
import sqlite3
import unittest

from fs.filelike import StringIO
from fs.tests import FSTestCases, ThreadingTestCases

import plugins

from PirannaFS.pyfilesystem import Filesystem


class TestPirannaFS(unittest.TestCase, FSTestCases):
#class TestPirannaFS(unittest.TestCase, ThreadingTestCases):
#class TestPirannaFS(unittest.TestCase, FSTestCases, ThreadingTestCases):

    test_id = 1

    def setUp(self):
        test_name = self.__class__.__name__ + '_' + str(self.test_id)

        self.db_file = '../../../' + test_name + '.sqlite'
#        self.db_file = ':memory:'

        self.ll_file = '../../../' + test_name + '.img'
        drive = open(self.ll_file, 'w+')
#        drive = StringIO()

        drive.write("\0" * 3 * 1024 * 1024)

        pm = plugins.Manager()
        pm.Load_Dir("../../plugins")

#        db = sqlite3.connect(self.db_file)
        db = sqlite3.connect(self.db_file, check_same_thread=False)

        sector_size = 512

        self.fs = Filesystem(db, drive, sector_size)

    def tearDown(self):
        self.fs.close()

        if self.db_file != ':memory:':
            os.remove(self.db_file)
        if not isinstance(self.ll_file, StringIO):
            os.remove(self.ll_file)

        self.__class__.test_id += 1


if __name__ == '__main__':
    unittest.main()