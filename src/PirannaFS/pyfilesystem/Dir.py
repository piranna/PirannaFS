'''
Created on 15/08/2010

@author: piranna
'''

import os
import stat

from fs.errors import DestinationExistsError, DirectoryNotEmptyError
from fs.errors import ParentDirectoryMissingError
from fs.errors import ResourceError, ResourceInvalidError, ResourceNotFoundError

import plugins


class Dir:
    '''
    http://pubs.opengroup.org/onlinepubs/007908799/xsh/dirent.h.html
    '''

    def __init__(self, fs, path):                                               # OK
        """Constructor

        @param fs: reference to the filesystem instance
        @param path: path of this dir
        @type path: string

        :raises ParentDirectoryMissingError: if a containing directory is missing
        :raises ResourceInvalidError:        if the path exists, but is not a directory
        :raises ResourceNotFoundError:       if the path is not found
        """
        try:
            self.__inode = fs.Get_Inode(path)
        except ResourceError:
            self.__inode = None
        else:
            # If inode is not a dir, raise error
            if fs.db.Get_Mode(self.__inode) != stat.S_IFDIR:
                raise ResourceInvalidError(path)

        self.fs = fs
        self.path = path


    def close(self):
        pass


    def isempty(self):
        """Check if a directory is empty (contains no files or sub-directories)

        @rtype: bool
        """
        return self.fs.db.readdir(self.__inode, 1)

    def make(self, recursive=False, allow_recreate=False):
        """Make a directory on the filesystem.

        @param recursive: if True, any intermediate directories will also be created
        @type recursive: bool
        @param allow_recreate: if True, re-creating a directory wont be an error
        @type allow_create: bool

        :raises DestinationExistsError: if the path is already a directory, and allow_recreate is False
        """
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
        self.__inode = self.fs.db.mkdir()
        self.fs.db.link(parent_dir_inode, name, self.__inode)

        plugins.send("Dir.make")


    def next(self):
        data = self.readline()
        if data:
            return data
        raise StopIteration


    def readline(self):                                                         # OK
        """Lists the files and directories under a given path.
        The directory contents are returned as a list of unicode paths.

        @rtype: iterable of paths
        """
        plugins.send("Dir.read begin")

#        yield unicode('.')
#        yield unicode('..')

        for dir_entry in self.fs.db.readdir(self.__inode):
            if dir_entry['name']:
                yield unicode(dir_entry['name'])

        plugins.send("Dir.read end")

    def readlines(self):
        """Return a list of all lines in the file."""
        return [ln for ln in self.readline()]

    def remove(self, recursive=False, force=False):
        """Remove a directory from the filesystem

        @param recursive: if True, then empty parent directories will be removed
        @type recursive: bool
        @param force: if True, any directory contents will be removed
        @type force: bool

        @raise DirectoryNotEmptyError: if the directory is not empty and force is False
        @raise ResourceNotFoundError: if the directory not exists
        """
        if not self.__inode:
            raise ResourceNotFoundError(self.path)

        # Force dir deletion
        if force:
            for dir_entry in self.fs.db.readdir(self.__inode):
                path = os.path.join(self.path, dir_entry.name)
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
            except (DirectoryNotEmptyError, ResourceNotFoundError):
                pass

        plugins.send("Dir.remove")


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __iter__(self):
        return self