'''
Created on 14/08/2010

@author: piranna
'''

import sys

import errno

from os.path import split
from stat    import S_IFDIR

from pirannafs.base.file import BaseFile
from pirannafs.errors    import IsADirectoryError, ParentDirectoryMissing
from pirannafs.errors    import ResourceNotFound, StorageSpace


class File(BaseFile):
    '''
    classdocs
    '''

    def __init__(self, fs, path, flags, mode=None):                        # OK
        '''
        Constructor
        '''
        self.path = path[1:]
        self.parent, self.name = split(path)

        # Get the inode of the parent or raise ParentDirectoryMissing exception
        try:
            self.parent = fs._Get_Inode(self.parent)
            inode = fs._Get_Inode(self.name, self.parent)
        except (ParentDirectoryMissing, ResourceNotFound):
            inode = None

        # If inode is a dir, raise error
        if inode and fs.db.Get_Mode(inode=inode) == S_IFDIR:
            raise IsADirectoryError(self.name)
#            raise IsADirectoryError(path)

        BaseFile.__init__(self, fs, inode)

        # File mode
        self._CalcMode(mode)


    # Undocumented

    # I have been not be able to found documentation for this functions,
    # but it seems they are required to work using a file class in fuse-python
    # since a patch done in 2008 to allow direct access to hardware instead
    # of data been cached in kernel space before been sended to user space.
    # Now you know the same as me, or probably more. If so, don't doubt in
    # tell me it :-)
    def direct_io(self, *args, **kwargs):
        print >> sys.stderr, '*** direct_io', args, kwargs
        return -errno.ENOSYS

    def keep_cache(self, *args, **kwargs):
        print >> sys.stderr, '*** keep_cache', args, kwargs
        return -errno.ENOSYS


    # Overloaded

    def create(self):
        print >> sys.stderr, '*** create'
        return -errno.ENOSYS


    def fgetattr(self):
        print >> sys.stderr, '*** fgetattr'
        return -errno.ENOSYS


    def flush(self):
        print >> sys.stderr, '*** flush'
        return -errno.ENOSYS


    def fsync(self, isSyncFile):
        print >> sys.stderr, '*** fsync', isSyncFile
        return -errno.ENOSYS


    def ftruncate(self, size):
        if size < 0:
            return -errno.EINVAL

        self._truncate(size)

        return 0


    def lock(self, cmd, owner, **kw):
        print >> sys.stderr, '*** lock', cmd, owner
        return -errno.ENOSYS


    def open(self):
        print >> sys.stderr, '*** open'
        return -errno.ENOSYS


    def read(self, length, offset):                                              # OK
        if offset < 0:
            return -errno.EINVAL

        self._offset = offset

        return BaseFile.read(self, length)


    def release(self, flags):
        print >> sys.stderr, '*** release', flags
        return -errno.ENOSYS


    def write(self, data, offset):                                          # OK
        if offset < 0:
            return -errno.EINVAL
        self._offset = offset

        try:
            self._write(data)
        except StorageSpace, e:
            return -errno.ENOSPC

        # Return size of the written data
        return len(data)