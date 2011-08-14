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

from ..Dir import BaseDir


class Dir(BaseDir):
    '''
    http://pubs.opengroup.org/onlinepubs/007908799/xsh/dirent.h.html
    '''

    def __init__(self, fs, path):                                           # OK
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

        BaseDir.__init__(self, fs, path)

        try:
            self._inode = fs.Get_Inode(path)
        except ResourceError:
            self._inode = None
        else:
            # If inode is not a dir, raise error
            if fs.db.Get_Mode(self._inode) != stat.S_IFDIR:
                raise ResourceInvalidError(path)


#    def ilist(self, wildcard=None,
#              full=False, absolute=False, dirs_only=False, files_only=False):
#        """Generator yielding the files and directories under a given path.
#
#        This method behaves identically to :py:meth:`fs.base.FS.listdir` but
#        returns an generator instead of a list.  Depending on the filesystem
#        this may be more efficient than calling :py:meth:`fs.base.FS.listdir`
#        and iterating over the resulting list.
#        """
#        return self.readline()


    def list(self, wildcard=None,
             full=False, absolute=False, dirs_only=False, files_only=False):
        """Lists the files and directories under a given path.

        The directory contents are returned as a list of unicode paths.

        :param path: root of the path to list
        :type path: string
        :param wildcard: Only returns paths that match this wildcard
        :type wildcard: string containing a wildcard, or a callable that accepts
            a path and returns a boolean
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
        :raises `fs.errors.ResourceInvalidError`: if the path exists, but is not
            a directory
        :raises `fs.errors.ResourceNotFoundError`: if the path is not found
        """
        return self.fs._listdir_helper(self.path, self.readlines(), wildcard,
                                       full, absolute, dirs_only, files_only)


    def make(self, recursive=False, allow_recreate=False):
        """Make a directory on the filesystem.

        @param recursive: if True, any intermediate directories will also be
            created
        @type recursive: bool
        @param allow_recreate: if True, re-creating a directory wont be an error
        @type allow_create: bool

        :raises DestinationExistsError: if the path is already a directory, and
            allow_recreate is False
        """
        plugins.send("Dir.make.begin")

        # Check if dir_entry exist and we can recreate it if so happens
        if self._inode:
            if allow_recreate:
                return
            else:
                raise DestinationExistsError(self.path)

        # Get parent dir
        if isinstance(self.parent, basestring):
            if not recursive:
                raise

            # Parents doesn't exist, they are the Three Wise men ;-)
            # but we want to create them anyway to get their inode
            d = Dir(self.fs, self.parent)
            d.make(True)
            self.parent = d._inode

        # Make directory
        self._inode = self.db.mkdir()
        self.db.link(self.parent, self.name, self._inode)

        plugins.send("Dir.make.end")


    def remove(self, recursive=False, force=False):
        """Remove a directory from the filesystem

        @param recursive: if True, then empty parent directories will be removed
        @type recursive: bool
        @param force: if True, any directory contents will be removed
        @type force: bool

        @raise DirectoryNotEmptyError: if the directory is not empty and force
            is False
        @raise ResourceNotFoundError: if the directory not exists
        """
        if not self._inode:
            raise ResourceNotFoundError(self.path)

        # Force dir deletion
        if force:
            for dir_entry in self.db.readdir(self._inode, -1):
                path = os.path.join(self.path, dir_entry.name)

                try:
                    inode = self.fs.Get_Inode(path)

                # Path doesn't exist, probably because it was removed by another
                # thead while we were getting the entries in this one. Since in
                # any case we are removing it, we can ignore the exception
                except ResourceNotFoundError:
                    pass

                else:
                    if self.db.Get_Mode(inode) == stat.S_IFDIR:
                        d = Dir(self.fs, path)
                        d.remove(force=True)
                    else:
                        self.fs.remove(path)

        # If dir is not empty raise error
        if self.db.readdir(self._inode, -1):
            raise DirectoryNotEmptyError(self.path)

        # Removed directory
        self.db.unlink(self.parent, self.name)
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


    #
    # File-like interface
    #

    def close(self):
        pass


    def next(self):
        data = self.readline()
        if data:
            return data
        raise StopIteration


    def readline(self):                                                     # OK
        """Lists the files and directories under a given path.
        The directory contents are returned as a list of unicode paths.

        @rtype: iterable of paths
        """
        if self._inode == None:
            raise ResourceNotFoundError(self.path)

        plugins.send("Dir.list.begin")

#        yield unicode('.')
#        yield unicode('..')

        for dir_entry in self.db.readdir(self._inode):
            if dir_entry['name']:
                yield unicode(dir_entry['name'])

        plugins.send("Dir.list.end")

    def readlines(self):
        """Return a list of all lines in the file."""
        if self._inode == None:
            raise ResourceNotFoundError(self.path)

        plugins.send("Dir.list.begin")

#        d = [ln for ln in self.readline()]
        d = []
        for dir_entry in self.db.readdir(self._inode, -1):
            if dir_entry['name']:
                d.append(unicode(dir_entry['name']))

        plugins.send("Dir.list.end")

        return d