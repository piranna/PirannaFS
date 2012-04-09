#!/usr/bin/python
# http://www.opengroup.org/onlinepubs/009695399/functions/mkdir.html


import errno
import os
import subprocess
import unittest

from stat import ST_ATIME


class Test_readdir(unittest.TestCase):
    def test_1(self):
        '''
        The readdir() function shall not return directory entries containing
        empty names.
        '''
        pass


    def test_2_1(self):
        '''
        If entries for dot or dot-dot exist, one entry shall be returned for dot
        and one entry shall be returned for dot-dot.
        '''
        pass


    def test_2_2(self):
        '''
        Otherwise, they shall not be returned.
        '''
        pass


    def test_3(self):                                                           # OK
        '''
        readdir() shall mark for update the st_atime field of the directory each
        time the directory is actually read.
        '''
        st_atime = os.stat('test_3')[ST_ATIME]
        os.listdir('test_3')

        self.assertLess(st_atime, os.stat('test_3')[ST_ATIME])


    def test_4(self):
        '''
        If the entry names a symbolic link, the value of the d_ino member is
        unspecified.
        '''
        pass


#    def test_5(self):
#        '''
#        If successful, the readdir_r() function shall return zero
#        '''
#        pass


    def test_6(self):
        '''
        Otherwise, an error number shall be returned to indicate the error.
        '''
        pass


    def test_EOVERFLOW(self):
        '''
        One of the values in the structure to be returned cannot be represented
        correctly.
        '''
        pass


    def test_EBADF(self):
        '''
        The dirp argument does not refer to an open directory stream.
        '''
        pass


    def test_ENOENT(self):
        '''
        The current position of the directory stream is invalid.
        '''
        pass


if __name__ == '__main__':
    unittest.main()
