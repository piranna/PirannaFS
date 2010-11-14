#!/usr/bin/python
# http://www.opengroup.org/onlinepubs/009695399/functions/ftruncate.html


import error
import subprocess
import unittest

from PirannaFS import FileSystem



class Test_ftruncate(unittest.TestCase):
    def test_1(self):
        '''
        If fildes is not a valid file descriptor open for writing, the
        ftruncate() function shall fail.
        '''
        pass


    def test_2(self):
        '''
        If fildes refers to a regular file, the ftruncate() function shall cause
        the size of the file to be truncated to length.
        '''
        pass


    def test_3(self):
        '''
        If the size of the file previously exceeded length, the extra data shall
        no longer be available to reads on the file.
        '''
        pass


    def test_4(self):
        '''
        If the file previously was smaller than this size, ftruncate() shall
        either increase the size of the file or fail.
        XSI-conformant systems shall increase the size of the file.
        '''
        pass


    def test_5_1(self):
        '''
        If the file size is increased, the extended area shall appear as if it
        were zero-filled.
        '''
        # Create empty file
        # Increase size
        
        # Get data from increased size
        data = 

        # Check all data are zeroes
        self.assertEqual(data,'\0'*5)


    def test_5_2(self):
        '''
        If the file size is increased, the extended area shall appear as if it
        were zero-filled.
        '''
        # Create file with random data
        # Increase size
        
        # Get data from increased size
        data = 

        # Check all data are zeroes
        self.assertEqual(data,'\0'*5)


    def test_6(self):
        '''
        The value of the seek pointer shall not be modified by a call to
        ftruncate().
        '''
        # Get current seek position
        #


    def test_7_st_ctime(self):
        '''
        Upon successful completion, if fildes refers to a regular file, the
        ftruncate() function shall mark for update the st_ctime and st_mtime
        fields of the file and the S_ISUID and S_ISGID bits of the file mode
        may be cleared.
        '''
        # Get st_ctime
        # truncate file
        # Get st_ctime
        # Compare data


    def test_7_st_mtime(self):
        '''
        Upon successful completion, if fildes refers to a regular file, the
        ftruncate() function shall mark for update the st_ctime and st_mtime
        fields of the file and the S_ISUID and S_ISGID bits of the file mode
        may be cleared.
        '''
        # Get st_mtime
        # truncate file
        # Get st_mtime
        # Compare data


    def test_7_S_ISUID(self):
        '''
        Upon successful completion, if fildes refers to a regular file, the
        ftruncate() function shall mark for update the st_ctime and st_mtime
        fields of the file and the S_ISUID and S_ISGID bits of the file mode
        may be cleared.
        '''
        # Get S_ISUID
        # truncate file
        # Get S_ISUID
        # Compare data


    def test_7_S_ISGID(self):
        '''
        Upon successful completion, if fildes refers to a regular file, the
        ftruncate() function shall mark for update the st_ctime and st_mtime
        fields of the file and the S_ISUID and S_ISGID bits of the file mode
        may be cleared.
        '''
        # Get S_ISGID
        # truncate file
        # Get S_ISGID
        # Compare data



    def test_8(self):
        '''
        If the ftruncate() function is unsuccessful, the file is unaffected.
        '''
        # Get old file
        # truncate
        # Get new file
        # Compare


    def test_9(self):
        '''
        If the request would cause the file size to exceed the soft file size
        limit for the process, the request shall fail and the implementation
        shall generate the SIGXFSZ signal for the thread.
        '''
        pass


    def test_10(self):                                                          # OK
        '''
        If fildes refers to a directory, ftruncate() shall fail.
        '''
        # Create directory
        self.fs.mkdir('/test_10',0)
        # truncate
        self.assertEqual(file.ftruncate(0), -errno.EISDIR)


    def test_11(self):
        '''
        If fildes refers to any other file type, except a shared memory object,
        the result is unspecified.
        '''
        pass


    def test_12(self):
        '''
        If fildes refers to a shared memory object, ftruncate() shall set the
        size of the shared memory object to length.
        '''
        pass


    def test_13(self):
        '''
        If the effect of ftruncate() is to decrease the size of a shared memory
        object or memory mapped file and whole pages beyond the new end were
        previously mapped, then the whole pages beyond the new end shall be
        discarded.
        '''
        pass


    def test_14(self):
        '''
        If the Memory Protection option is supported, references to discarded
        pages shall result in the generation of a SIGBUS signal; otherwise, the
        result of such references is undefined.
        '''
        pass


    def test_15(self):
        '''
        If the effect of ftruncate() is to increase the size of a shared memory
        object, it is unspecified whether the contents of any mapped pages
        between the old end-of-file and the new are flushed to the underlying
        object.
        '''
        pass


    def test_16(self):
        '''
        Upon successful completion, ftruncate() shall return 0.
        '''
        pass


    def test_17(self):
        '''
        Otherwise, -errno shall be returned to indicate the error.
        '''
        pass


    def test_EINTR(self):
        '''
        A signal was caught during execution.
        '''
        pass


    def test_EINVAL(self):
        '''
        The length argument was less than 0.
        '''
        self.assertEqual(file.ftruncate(-1), -errno.EINVAL)


    def test_EFBIG_or_EINVAL(self):
        '''
        The length argument was greater than the maximum file size.
        '''
#        self.assertEqual(file.ftruncate(-1), -errno.EFBIG)


    def test_EFBIG(self):
        '''
        The file is a regular file and length is greater than the offset maximum
        established in the open file description associated with fildes.
        '''
        pass


    def test_EIO_1(self):
        '''
        An I/O error occurred while reading from the file system.
        '''
        pass


    def test_EIO_2(self):
        '''
        An I/O error occurred while writing to the file system.
        '''
        pass


    def test_EBADF(self):
        '''
        The fildes argument is not a file descriptor open for writing.
        '''
        pass


    def test_EINVAL(self):
        '''
        The fildes argument references a file that was opened without write
        permission.
        '''
        pass


    def test_EROFS(self):
        '''
        The named file resides on a read-only file system.
        '''
        pass


    def test_truncate(self):
        '''
        Truncate the file
        Check the new file size
        Check the freed space
        '''
        pass


    def test_enlarge(self):
        '''
        Enlarge the file
        Check the new file size
        Check the freed space
        '''
        pass


    def test_truncateToZero(self):
        '''
        Truncate the file size to zero
        Check the new file size
        Check the freed space
        '''
        pass



unittest.main()