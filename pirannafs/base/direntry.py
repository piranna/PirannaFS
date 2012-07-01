'''
Created on 20/04/2012

@author: piranna
'''

from os.path import split

from pirannafs.errors import ParentDirectoryMissing
from pirannafs.errors import ResourceNotFound


class DirEntry(object):
    '''
    classdocs
    '''

    def __init__(self, fs):
        '''
        Constructor
        '''
        self.fs = fs
        self.db = fs.db

        self.parent, self.name = split(self.path)

        try:
            self.parent = fs._Get_Inode(self.parent)
        except (ParentDirectoryMissing, ResourceNotFound):
            self._inode = None
            return

        try:
            self._inode = fs._Get_Inode(self.name, self.parent)
        except ResourceNotFound:
            self._inode = None

    def next(self):
        data = self.readline()
        if data:
            return data
        raise StopIteration

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __iter__(self):
        return self
