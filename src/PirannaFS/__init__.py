'''
Created on 02/04/2011

@author: piranna
'''

import os
import stat

from os.path import split

# Errors are imported from PyFilesystem doing it system dependent
# maybe in the future i use my own implementation
from fs.errors import *

from DB import DB
from LL import LL


class BaseFS(object):
    '''
    classdocs
    '''

    def __init__(self, db, drive, sector_size=512):
        self.ll = LL(drive, sector_size)
        self.db = DB(db, self.ll._file, sector_size)

        self._freeSpace = None
        self.__sector_size = sector_size


    def _FreeSpace(self):
        if self._freeSpace == None:
            self._freeSpace = self.db.Get_FreeSpace()*self.__sector_size

        return self._freeSpace


    def _Get_Inode(self, path, inode=0):                                     # OK
        '''
        Get the inode of a path
        '''
#        print >> sys.stderr, '*** _Get_Inode', repr(path),inode

        # If there are path elements
        # get their inodes
        if path:
            parent, _, path = path.partition(os.sep)

            # Get inode of the dir entry
            inode = self.db.Get_Inode(parent_dir=inode, name=parent)

            # If there's no such dir entry, raise the adecuate exception
            # depending of it's related to the resource we are looking for
            # or to one of it's parents
            if inode == None:
                if path:
                    raise ParentDirectoryMissingError(parent)
                else:
                    raise ResourceNotFoundError(parent)

            # If the dir entry is a directory
            # get child inode
            if self.db.Get_Mode(inode=inode) == stat.S_IFDIR:
                return self._Get_Inode(path, inode)

            # If is not a directory and is not the last path element
            # return error
            if path:
                raise ResourceInvalidError(path)

        # Path is empty, so
        # * it's the root path
        # * or we consumed it
        # * or it's not a directory and it's the last path element
        # so return computed inode
        return inode

    def _Path2InodeName(self, path):                                         # OK
        '''
        Get the parent dir inode and the name of a dir entry defined by path
        '''
#        print >> sys.stderr, '*** _Path2InodeName', repr(path)
        path, name = split(path)
        try:
            inode = self._Get_Inode(path)
        except ResourceNotFoundError:
            raise ParentDirectoryMissingError(path)

        return inode, name