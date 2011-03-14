'''
Created on 15/08/2010

@author: piranna
'''

import os
import stat

from fs.errors import *

import plugins


class Dir:
    '''
    classdocs
    '''

    def __init__(self, fs, path):                                              # OK
        '''
        Constructor
        '''
        try:
            self.__inode = fs.Get_Inode(path[1:])
        except ResourceError:
            self.__inode = None
        else:
            # Inode is not from a dir
            if fs.db.Get_Mode(self.__inode) != stat.S_IFDIR:
                raise ResourceInvalidError(path)

        self.fs = fs
        self.path = path

    def isempty(self):
        return self.fs.db.readdir(self.__inode, 1)

    def make(self, recursive=False, allow_recreate=False):
        # Check if dir_entry exist and we can recreate it if so happens
        if self.__inode and not allow_recreate:
            raise DestinationExistsError(self.path)

        # Get parent dir
        try:
            parent_dir_inode, name = self.fs.Path2InodeName(self.path)

        except ParentDirectoryMissingError:
            if not recursive:
                raise

            # Parents doesn't exist, they are the Three Wise men ;-)
            # but we want to create them anyway to get their inode
            path, _, name = self.path.rpartition(os.sep)
            d = Dir(self.fs, path)
            d.make(path, recursive)
            parent_dir_inode = d.__inode

        # Make directory
        self.__inode = self.db.mkdir()
        self.db.link(parent_dir_inode, name, self.__inode)

    def read(self):                                                          # OK
        plugins.send("Dir.read start")

#        yield unicode('.')
#        yield unicode('..')

        for dir_entry in self.fs.db.readdir(self.__inode):
            if dir_entry['name']:
                yield unicode(dir_entry['name'])

        plugins.send("Dir.read end")

    def remove(self, recursive=False, force=False):
        # Force dir deletion
        if force:
            for dir_entry in self.fs.db.readdir(self.__inode):
                path = os.path.join(self.path, dir_entry)
                inode = self.fs.Get_Inode(path)

                if self.fs.db.Get_Mode(inode) == stat.S_IFDIR:
                    d = Dir(self.fs, path)
                    d.remove(force=True)
                else:
                    self.fs.remove(path)

        # If dir is not empty raise error
        if self.fs.db.readdir(self.__inode):
            raise DirectoryNotEmptyError(self.path)

        # Removed directory
        parent_dir_inode, name = self.fs.Path2InodeName(self.path)
        self.fs.db.unlink(parent_dir_inode, name)
        self.__inode = None

        # Delete parent dirs recursively if empty
        if recursive:
            path = self.path.rpartition(os.sep)[0]
            d = Dir(self.fs, path)
            try:
                d.remove(True)
            except DirectoryNotEmptyError:
                pass