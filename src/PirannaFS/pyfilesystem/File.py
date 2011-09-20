'''
Created on 14/08/2010

@author: piranna
'''

from fs.errors import DestinationExistsError, ResourceInvalidError

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


    def make(self):
        # Check if dir_entry
        if self._inode != None:
            raise DestinationExistsError(self.path)

        # Make file
        self._make()


    def open(self, mode="r", **kwargs):
        self._CalcMode(mode)

        return self


    def truncate(self, size=0):
        size += self._offset

        if size < 0:
            raise ResourceInvalidError(msg="truncate under zero")

        self._truncate(size)