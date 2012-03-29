#!/usr/bin/python
# http://www.opengroup.org/onlinepubs/009695399/functions/mkdir.html


import errno
import subprocess
import unittest

from PirannaFS import FileSystem



class Test_ftruncate(unittest.TestCase):
    def test_1(self):
        '''
        The mkdir() function shall create a new directory with name path.
        '''
        pass


    def test_2_1(self):
        '''
        The file permission bits of the new directory shall be initialized from
        mode.
        '''
        pass


    def test_2_2(self):
        '''
        These file permission bits of the mode argument shall be modified
        by the process' file creation mask.
        '''
        pass


    def test_2_3(self):
        '''
        When bits in mode other than the file permission bits are set, the
        meaning of these additional bits is implementation-defined.
        '''
        pass


    def test_3(self):
        '''
        The directory's user ID shall be set to the process' effective user ID.
        '''
        # Create directory
        self.fs.mkdir('/test_3',0)
        # Get UID
        self.assertEqual(uid, uid)


    def test_4(self):
        '''
        The directory's group ID shall be set to the group ID of the parent
        directory or to the effective group ID of the process.

        Implementations shall provide a way to initialize the directory's group
        ID to the group ID of the parent directory.

        Implementations may, but need not, provide an implementation-defined way
        to initialize the directory's group ID to the effective group ID of the
        calling process.
        '''
        pass


    def test_4_1(self):
        '''
        The directory's group ID shall be set to the group ID of the parent
        directory or to the effective group ID of the process.
        '''
        pass


    def test_4_2(self):
        '''
        Implementations shall provide a way to initialize the directory's group
        ID to the group ID of the parent directory.
        '''
        pass


    def test_4_3(self):
        '''
        Implementations may, but need not, provide an implementation-defined way
        to initialize the directory's group ID to the effective group ID of the
        calling process.
        '''
        pass


    def test_5(self):                                                           # OK
        '''
        The newly created directory shall be an empty directory.
        '''
        # Create directory
        self.fs.mkdir('/test_5',0)
        # Read dir
        self.assertItemsEqual(self.fs.readdir('/test_5'), [])


    def test_7_1(self):
        '''
        Upon successful completion, mkdir() shall mark for update the st_atime,
        st_ctime, and st_mtime fields of the directory.
        '''
        pass


    def test_7_2(self):
        '''
        Also, the st_ctime and st_mtime fields of the directory that contains
        the new entry shall be marked for update.
        '''
        pass


    def test_8(self):
        '''
        Upon successful completion, mkdir() shall return 0.
        '''
        pass


    def test_9(self):
        '''
        Otherwise, -1 shall be returned, no directory shall be created, and
        errno shall be set to indicate the error.
        '''
        pass


    def test_EACCES_1(self):
        '''
        Search permission is denied on a component of the path prefix.
        '''
        pass


    def test_EACCES_2(self):
        '''
        Write permission is denied on the parent directory of the directory to
        be created.
        '''
        pass


    def test_EEXIST_1(self):                                                    # OK
        '''
        If path names a symbolic link, mkdir() shall fail.
        '''
        # Create symlink
        self.fs.symlink('/test_6')
        # Make dir
        self.assertEqual(self.fs.mkdir('/test_6',0), -errno.EEXIST)


    def test_EEXIST_1(self):                                                    # OK
        '''
        The named file exists.
        '''
        # Create first directory
        self.fs.mkdir('/test_11',0)
        # Create second directory
        self.assertEqual(self.fs.mkdir('/test_11'), -errno.EEXIST)



    def test_ELOOP(self):
        '''
        A loop exists in symbolic links encountered during resolution of the
        path argument.
        '''
        pass


    def test_EMLINK(self):
        '''
        The link count of the parent directory would exceed {LINK_MAX}.
        '''
        pass


    def test_ENAMETOOLONG(self):
        '''
        The length of the path argument exceeds {PATH_MAX} or a pathname
        component is longer than {NAME_MAX}.
        '''
        pass


    def test_ENOENT_1(self):                                                          # OK
        '''
        A component of the path prefix specified by path does not name an
        existing directory.
        '''
        # Create second directory
        self.assertEqual(self.fs.mkdir('/null/test_15'), -errno.ENOENT)


    def test_ENOENT_2(self):                                                          # OK
        '''
        Path is an empty string.
        '''
        # Create second directory
        self.assertEqual(self.fs.mkdir(''), -errno.ENOENT)


    def test_ENOSPC_1(self):
        '''
        The file system does not contain enough space to hold the contents of
        the new directory.
        '''
        pass


    def test_ENOSPC_2(self):
        '''
        The file system does not contain enough space to extend the parent
        directory of the new directory.
        '''
        pass


    def test_ENOTDIR(self):
        '''
        A component of the path prefix is not a directory.
        '''
        pass


    def test_EROFS(self):
        '''
        The parent directory resides on a read-only file system.
        '''
        pass


    def test_ELOOP(self):
        '''
        More than {SYMLOOP_MAX} symbolic links were encountered during
        resolution of the path argument.
        '''
        pass


    def test_ENAMETOOLONG(self):
        '''
        As a result of encountering a symbolic link in resolution of the path
        argument, the length of the substituted pathname string exceeded
        {PATH_MAX}.
        '''
        pass






unittest.main()