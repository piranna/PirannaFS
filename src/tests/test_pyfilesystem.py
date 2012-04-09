from os       import remove
from os.path  import abspath, dirname, join
from unittest import TestCase

from fs.filelike import StringIO
from fs.tests    import FSTestCases, ThreadingTestCases

from plugins import Manager

from pirannafs.backends.pyfilesystem import Filesystem


class PyFilesystem(TestCase, FSTestCases):
#class PyFilesystem(TestCase, FSTestCases, ThreadingTestCases):

    test_id = 1

    def setUp(self):
        file_path = dirname(abspath(__file__))

        # Load plugins
        Manager(join(file_path, '..', 'plugins'))

        test_name = self.__class__.__name__ + '_' + str(self.test_id)

        self.db_file = join(file_path, '../..', test_name + '.sqlite')
#        self.db_file = ':memory:'

        self.ll_file = join(file_path, '../..', test_name + '.img')
        drive = open(self.ll_file, 'w+')
#        drive = StringIO()

        drive.write("\0" * 3 * 1024 * 1024)

        self.fs = Filesystem(self.db_file, drive)

    def tearDown(self):
        self.fs.close()

        if self.db_file != ':memory:':
            remove(self.db_file)
        if not isinstance(self.ll_file, StringIO):
            remove(self.ll_file)

        self.__class__.test_id += 1


if __name__ == '__main__':
    from unittest import main

    main()
