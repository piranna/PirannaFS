'''
Created on 14/08/2010

@author: piranna
'''

from fs.errors import ResourceInvalidError, ResourceNotFoundError

from ..File import BaseFile


class File(BaseFile):
    '''
    classdocs
    '''
    def __init__(self, fs, path):
        """Constructor

        @raise ParentDirectoryMissingError:
        @raise ResourceNotFoundError:
        @raise ResourceInvalidError:
        """
        BaseFile.__init__(self, fs, path)

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
        self._CalcMode(mode)

        return self

    def remove(self):
        """Remove a file from the filesystem.

        :raises ParentDirectoryMissingError: if a containing directory is missing and recursive is False
        :raises ResourceInvalidError:        if the path is a directory or a parent path is an file
        :raises ResourceNotFoundError:       if the path is not found
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


    # File-like

    def truncate(self, size=0):
        size += self._offset

        if size < 0:
            raise ResourceInvalidError(msg="truncate under zero")

        self._truncate(size)