'''
Created on 14/08/2010

@author: piranna
'''

from os      import SEEK_SET, SEEK_CUR, SEEK_END
from os.path import split
from stat    import S_IFDIR

from fs.errors import ParentDirectoryMissingError, ResourceInvalidError
from fs.errors import ResourceNotFoundError, StorageSpaceError

from pirannafs.base.file import BaseFile
from pirannafs.errors    import FileNotFoundError, IsADirectoryError
from pirannafs.errors    import ParentDirectoryMissing
from pirannafs.errors    import ParentNotADirectoryError, ResourceNotFound
from pirannafs.errors    import StorageSpace


class File(BaseFile):
    '''
    classdocs
    '''
    def __init__(self, fs, path):
        """Constructor

        @raise ParentDirectoryMissingError:
        @raise ResourceInvalidError:
        """
        self.path = path
        self.parent, self.name = split(path)

        try:
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

        except (IsADirectoryError, ParentNotADirectoryError), e:
            raise ResourceInvalidError(e)

        except ParentDirectoryMissing, e:
            raise ParentDirectoryMissingError(e)

        # File mode
        self._mode = frozenset()

#    def contents(self):
#        pass
#
#    def copy(self):
#        pass
#
#    def move(self):
#        pass

    def open(self, mode="r", **kwargs):
        try:
            self._CalcMode(mode)
        except FileNotFoundError, e:
            raise ResourceNotFoundError(e)

        return self

    def remove(self):
        """Remove a file from the filesystem.

        :raises ParentDirectoryMissingError: if a containing directory is
            missing and recursive is False
        :raises ResourceInvalidError: if the path is a directory or a parent
            path is an file
        :raises ResourceNotFoundError: if the path is not found
        """
#        # Get inode and name from path

        if self._inode == None:
            raise ResourceNotFoundError(self.path)

        # Unlink dir entry
        self.db.unlink(parent_dir=self.parent, name=self.name)

        self._inode = None
        self._offset = 0

#    def safeopen(self):
#        pass

    def size(self):
        """Returns the size (in bytes) of a resource.

        :rtype: integer
        :returns: the size of the file
        """
        if self._inode != None:
            return self.db.Get_Size(inode=self._inode)
        return 0

    #
    # File-like interface
    #

    def seek(self, offset, whence=SEEK_SET):
        """
        """
        # Set whence
        if   whence == SEEK_SET: whence = 0
        elif whence == SEEK_CUR: whence = self._offset
        elif whence == SEEK_END: whence = self.db.Get_Size(inode=self._inode)
        else:                    raise ResourceInvalidError(self.path)

        # Readjust offset
        self._offset = whence + offset

    def truncate(self, size=0):
        size += self._offset

        if size < 0:
            raise ResourceInvalidError(msg="truncate under zero")

        self._truncate(size)

    def write(self, data):
        try:
            self._write(data)
        except StorageSpace, e:
            raise StorageSpaceError(e)

    def writelines(self, sequence):
        data = ""
        for line in sequence:
            data += line
        self.write(data)
