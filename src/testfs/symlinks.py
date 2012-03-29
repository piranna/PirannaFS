#!/usr/bin/python

import sys
sys.stderr = open('../test/error.log', 'w')

import errno
import subprocess

from unittest import TestCase


class readlink(TestCase):
    '''
    http://www.opengroup.org/onlinepubs/009695399/functions/readlink.html

    Note: I have to convert the return value of fs.readlink() explicitly to int
    to check them since Python-FUSE return always a string on success and error.
    '''


    def test_1(self):                                                           # OK
        '''
        The readlink() function shall return the contents of the symbolic link
        referred to by path.
        '''
        fs.symlink("/", "/test_1")
        self.assertEqual(fs.readlink("/test_1"), "/")
#        fs.rmdir("/test_1")


    def test_EACCES_1(self):
        '''
        Search permission is denied for a component of the path prefix of path.
        '''
        pass


    def test_EACCESS_2(self):
        '''
        Read permission is denied for the directory.
        '''
        pass


    def test_EINVAL(self):                                                      # OK
        '''
        The path argument names a file that is not a symbolic link.
        '''
        fs.mkdir("/test_EINVAL", 0)
        self.assertEqual(int(fs.readlink("/test_EINVAL")), -errno.EINVAL)
#        fs.rmdir("/test_EINVAL")


    def test_EIO(self):
        '''
        An I/O error occurs while reading from to the file system.
        '''
        pass


    def test_ELOOP_1(self):
        '''
        A loop exists in symbolic links encountered during resolution of the
        path argument.
        '''
        pass


    def test_ELOOP_2(self):
        '''
        More than {SYMLOOP_MAX} symbolic links were encountered during
        resolution of the path argument.
        '''
        pass


    def test_ENAMETOOLONG_1(self):
        '''
        The length of the path argument exceeds {PATH_MAX}.
        '''
        pass


    def test_ENAMETOOLONG_2(self):
        '''
        A pathname component is longer than {NAME_MAX}.
        '''
        pass


    def test_ENAMETOOLONG_3(self):
        '''
        As a result of encountering a symbolic link in resolution of the path
        argument, the length of the substituted pathname string exceeded
        {PATH_MAX}.
        '''
        pass


    def test_ENOENT_1(self):                                                    # OK
        '''
        A component of path does not name an existing file.
        '''
        self.assertEqual(int(fs.readlink("/none/test_ENOENT_1")), -errno.ENOENT)


    def test_ENOENT_2(self):                                                    # OK
        '''
        path is an empty string.
        '''
        self.assertEqual(int(fs.readlink("")), -errno.ENOENT)


#    def test_ENOTDIR(self):                                                     # OK
#        '''
#        A component of the path prefix is not a directory.
#        '''
#        fs.mknod("/file")
#        self.assertEqual(int(fs.readlink("/file/test_ENOTDIR")), -errno.ENOTDIR)


class symlink(TestCase):
    '''
    http://www.opengroup.org/onlinepubs/009695399/functions/symlink.html

    The symlink() function shall create a symbolic link called path2 that
    contains the string pointed to by path1 (path2 is the name of the symbolic
    link created, path1 is the string contained in the symbolic link).

    The string pointed to by path1 shall be treated only as a character string
    and shall not be validated as a pathname.
    '''


#    def test_1(self):
#        '''
#        If the symlink() function fails for any reason other than [EIO], any
#        file named by path2 shall be unaffected.
#        '''
#        pass


    def test_2(self):                                                           # OK
        '''
        Upon successful completion, symlink() shall return 0.
        '''
        self.assertEqual(fs.symlink("/", "/test_2"), 0)
#        fs.rmdir("/test_2")


    def test_EACCES_1(self):
        '''
        Write permission is denied in the directory where the symbolic link is
        being created.
        '''
        pass


    def test_EACCES_2(self):
        '''
        Search permission is denied for a component of the path prefix of path2.
        '''
        pass


#    def test_EEXIST_1(self):
#        '''
#        The path2 argument names an existing file.
#        '''
#        fs.mknod("/test_EEXIST_3")
#        self.assertEqual(fs.symlink("/test_EEXIST_3", "/"), -errno.EEXIST)


    def test_EEXIST_2(self):                                                    # OK
        '''
        The path2 argument names an existing directory.
        '''
        fs.mkdir("/test_EEXIST_2", 0)
        self.assertEqual(fs.symlink("/", "/test_EEXIST_2"), -errno.EEXIST)
        fs.rmdir("/test_EEXIST_2")


    def test_EEXIST_3(self):                                                    # OK
        '''
        The path2 argument names an existing symbolic link.
        '''
        fs.symlink("/", "/test_EEXIST_3")
        self.assertEqual(fs.symlink("/", "/test_EEXIST_3"), -errno.EEXIST)
#        fs.rmdir("/test_EEXIST_3")


    def test_EIO(self):
        '''
        An I/O error occurs while reading from or writing to the file system.
        '''
        pass


#    def test_ELOOP_1(self):
#        '''
#        A loop exists in symbolic links encountered during resolution of the
#        path2 argument.
#        '''
#        pass


#    def test_ELOOP_2(self):
#        '''
#        More than {SYMLOOP_MAX} symbolic links were encountered during
#        resolution of the path2 argument.
#        '''
#        pass


    def test_ENAMETOOLONG_1(self):
        '''
        The length of the path2 argument exceeds {PATH_MAX}.
        '''
        pass


    def test_ENAMETOOLONG_2(self):
        '''
        A pathname component is longer than {NAME_MAX}.
        '''
        pass


    def test_ENAMETOOLONG_3(self):
        '''
        The length of the path1 argument is longer than {SYMLINK_MAX}.
        '''
        pass


#    def test_ENAMETOOLONG_4(self):
#        '''
#        As a result of encountering a symbolic link in resolution of the path2
#        argument, the length of the substituted pathname string exceeded
#        {PATH_MAX} bytes (including the terminating null byte), or the length of
#        the string pointed to by path1 exceeded {SYMLINK_MAX}.
#        '''
#        pass


    def test_ENOENT_1(self):                                                    # OK
        '''
        A component of path2 does not name an existing directory.
        '''
        self.assertEqual(fs.symlink("/", "/none/test_ENOENT_2"), -errno.ENOENT)


    def test_ENOENT_2(self):                                                    # OK
        '''
        path2 is an empty string.
        '''
        self.assertEqual(fs.symlink("/", ""), -errno.ENOENT)


    def test_ENOSPC_1(self):
        '''
        The directory in which the entry for the new symbolic link is being
        placed cannot be extended because no space is left on the file system
        containing the directory.
        '''
        pass


    def test_ENOSPC_2(self):
        '''
        The new symbolic link cannot be created because no space is left on the
        file system which shall contain the link.
        '''
        pass


    def test_ENOSPC_3(self):
        '''
        The file system is out of file-allocation resources.
        '''
        pass


#    def test_ENOTDIR(self):
#        '''
#        A component of the path prefix of path2 is not a directory.
#        '''
#        fs.mknod("/file")
#        self.assertEqual(fs.symlink("/", "/file/test_ENOTDIR"), -errno.ENOTDIR)


    def test_EROFS(self):
        '''
        The new symbolic link would reside on a read-only file system.
        '''
        pass


if __name__ == '__main__':
    from unittest import main

    main()