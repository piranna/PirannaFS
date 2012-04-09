import os
import unittest

from fs.filelike import StringIO
from fs.tests import FSTestCases, ThreadingTestCases

import plugins

from pirannafs.backends.pyfilesystem import Filesystem


class PyFilesystem(unittest.TestCase, FSTestCases):
#class PyFilesystem(unittest.TestCase, FSTestCases, ThreadingTestCases):

    test_id = 1

    def setUp(self):
        # Load plugins
        pm = plugins.Manager()
        pm.Load_Dir("../plugins")

        test_name = self.__class__.__name__ + '_' + str(self.test_id)

        self.db_file = '../../' + test_name + '.sqlite'
#        self.db_file = ':memory:'

        self.ll_file = '../../' + test_name + '.img'
        drive = open(self.ll_file, 'w+')
#        drive = StringIO()

        drive.write("\0" * 3 * 1024 * 1024)

        self.fs = Filesystem(self.db_file, drive)

    def tearDown(self):
        self.fs.close()

        if self.db_file != ':memory:':
            os.remove(self.db_file)
        if not isinstance(self.ll_file, StringIO):
            os.remove(self.ll_file)

        self.__class__.test_id += 1


if __name__ == '__main__':
    unittest.main()
