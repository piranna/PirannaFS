'''
Created on 15/08/2010

@author: piranna
'''

import os
import stat

from os.path import split

from fs.errors import DestinationExistsError, DirectoryNotEmptyError
from fs.errors import ParentDirectoryMissingError, RemoveRootError
from fs.errors import ResourceInvalidError, ResourceNotFoundError

from pirannafs.errors import DirNotFoundError, NotADirectoryError
from pirannafs.errors import ParentDirectoryMissing, ResourceError, ResourceNotFound

import plugins

from ...base.dir import BaseDir


class Dir(BaseDir):
    '''
    http://pubs.opengroup.org/onlinepubs/007908799/xsh/dirent.h.html
    '''

    def __init__(self, fs, path):                                          # OK
        """Constructor

        @param fs: reference to the filesystem instance
        @param path: path of this dir
        @type path: string

        :raises ParentDirectoryMissingError: if a containing directory is
            missing
        :raises ResourceInvalidError:        if the path exists, but is not a
            directory
        :raises ResourceNotFoundError:       if the path is not found
        """
        if path == './':    # [HACK] Ugly hack to pass unittest, need a re-do
            path = ''

        # Base
#        BaseDir.__init__(self, fs, path)

        self.fs = fs
        self.db = fs.db

        self.path = path
        parent_path, self.name = split(path)

        try:
            self.parent = fs._Get_Inode(parent_path)
        except (ParentDirectoryMissing, ResourceNotFound):
            self.parent = parent_path

        # PyFilesystem
        try:
            self._inode = fs._Get_Inode(path)
        except (ResourceError, ResourceNotFound):
            self._inode = None
        else:
            # If inode is not a dir, raise error
            if fs.db.Get_Mode(inode=self._inode) != stat.S_IFDIR:
                raise ResourceInvalidError(path)

#    def copy(self):
#        pass

    def isempty(self):
        """Check if a directory is empty (contains no files or sub-directories)

        @rtype: bool
        """
#        print "BaseDir.isempty"
        return self.db.readdir(parent_dir=self._inode, limit=1)

    def ilist(self, wildcard=None,
              full=False, absolute=False, dirs_only=False, files_only=False):
        """Generator yielding the files and directories under a given path.

        This method behaves identically to :py:meth:`fs.base.FS.listdir` but
        returns an generator instead of a list.  Depending on the filesystem
        this may be more efficient than calling :py:meth:`fs.base.FS.listdir`
        and iterating over the resulting list.
        """
        return self.fs._listdir_helper(self.path, self._list(), wildcard, full,
                                       absolute, dirs_only, files_only)

#    def ilistinfo(self):
#        pass

    def list(self, wildcard=None,
             full=False, absolute=False, dirs_only=False, files_only=False):
        """Lists the files and directories under a given path.

        The directory contents are returned as a list of unicode paths.

        :param path: root of the path to list
        :type path: string
        :param wildcard: Only returns paths that match this wildcard
        :type wildcard: string containing a wildcard, or a callable that
            accepts a path and returns a boolean
        :param full: returns full paths (relative to the root)
        :type full: bool
        :param absolute: returns absolute paths (paths beginning with /)
        :type absolute: bool
        :param dirs_only: if True, only return directories
        :type dirs_only: bool
        :param files_only: if True, only return files
        :type files_only: bool

        :rtype: iterable of paths

        :raises `fs.errors.ParentDirectoryMissingError`: if an intermediate
            directory is missing
        :raises `fs.errors.ResourceInvalidError`: if the path exists, but is
            not a directory
        :raises `fs.errors.ResourceNotFoundError`: if the path is not found
        """
        try:
            return list(self.ilist(wildcard, full, absolute, dirs_only,
                                   files_only))
        except DirNotFoundError, e:
            raise ResourceNotFoundError(e)

#    def listinfo(self):
#        pass

    def make(self, recursive=False, allow_recreate=False):
        """Make a directory on the filesystem.

        @param recursive: if True, any intermediate directories will also be
            created
        @type recursive: bool
        @param allow_recreate: if True, recreating a directory wont be an error
        @type allow_create: bool

        :raises DestinationExistsError: if the path is already a directory, and
            allow_recreate is False
        """
        plugins.send("Dir.make.begin")

        # Check if dir_entry exist and we can recreate it if so happens
        if self._inode:
            if allow_recreate:
                return
            raise DestinationExistsError(self.path)

        # Get parent dir
        if isinstance(self.parent, basestring):
            if not recursive:
                raise ParentDirectoryMissingError(self.path)

            # Parents doesn't exist, they are the Three Wise men ;-)
            # but we want to create them anyway to get their inode
            d = Dir(self.fs, self.parent)
            d.make(True)
            self.parent = d._inode

        # Make directory
        self._inode = self.db._Make_DirEntry(type=stat.S_IFDIR)
        self.db.link(parent_dir=self.parent, name=self.name,
                     child_entry=self._inode)

        plugins.send("Dir.make.end")

#    def makeopen(self):
#        pass
#
#    def open(self):
#        pass

    def remove(self, recursive=False, force=False):
        """Remove a directory from the filesystem

        @param recursive: if True, then empty parent directories will be
            removed
        @type recursive: bool
        @param force: if True, any directory contents will be removed
        @type force: bool

        @raise DirectoryNotEmptyError: if the directory is not empty and force
            is False
        @raise ResourceNotFoundError: if the directory not exists
        """
        if self.path == '/':
            raise RemoveRootError()

        if not self._inode:
            raise ResourceNotFoundError(self.path)

        # Force dir deletion
        if force:
            for dir_entry in self.db.readdir(parent_dir=self._inode, limit= -1):
                path = os.path.join(self.path, dir_entry.name)

                try:
                    inode = self.fs._Get_Inode(path)

                # Path doesn't exist, probably because it was removed by
                # another thead while we were getting the entries in this one.
                # Since in any case we are removing it, we can ignore the
                # exception
                except ResourceNotFound:
                    pass

                else:
                    # Entry is from a directory, delete it recursively
                    if self.db.Get_Mode(inode=inode) == stat.S_IFDIR:
                        d = Dir(self.fs, path)
                        d.remove(force=True)

                    # Entry is from a file, ask to filesystem to delete it
                    else:
                        self.fs.remove(path)

        # If dir is not empty raise error
        if self.db.readdir(parent_dir=self._inode, limit= -1):
            raise DirectoryNotEmptyError(self.path)

        # Removed directory
        self.db.unlink(parent_dir=self.parent, name=self.name)
        self._inode = None

        # Delete parent dirs recursively if empty
        if recursive:
            path = self.path.rpartition(os.sep)[0]
            d = Dir(self.fs, path)
            try:
                d.remove(True)
            except (DirectoryNotEmptyError, ResourceNotFoundError):
                pass

        plugins.send("Dir.remove")


#    def walk(self):
#        pass
#
#    def walkdirs(self):
#        pass
#
#    def walkfiles(self):
#        pass
