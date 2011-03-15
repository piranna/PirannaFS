'''
Created on 16/08/2010

@author: piranna
'''

import errno
import os
import stat

from fs import base
from fs.errors import *

import Dir
import File

import plugins

from .. import DB, LL


class FileSystem(base.FS):
    def __init__(self, db, drive, sector_size):
        base.FS.__init__(self)

        self.db = DB.DB(db)
        self.ll = LL.LL(drive, sector_size)

        self.dir_class = Dir.Dir
        self.file_class = File.File

        plugins.send("FS.__init__", db=self.db, ll=self.ll)


    #
    # Essential methods
    #

    def getinfo(self, path):                                                    # OK
        """Returns information for a path as a dictionary. The exact content of
        this dictionary will vary depending on the implementation, but will
        likely include a few common values.

        :param path: a path to retrieve information for

        :rtype: dict

        :raises ParentDirectoryMissingError
        :raises ResourceInvalidError
        :raises ResourceNotFoundError:  If the path does not exist
        """
        parent_dir, name = self.Path2InodeName(path[1:])

        return self.db.getattr(parent_dir, name)


    def isdir(self, path):                                                      # OK
        """Check if a path references a directory.

        :param path: a path in the filesystem

        :rtype: bool

        :raises ParentDirectoryMissingError
        :raises ResourceInvalidError
        :raises ResourceNotFoundError:  If the path does not exist
        """
        inode = self.Get_Inode(path[1:])

        return self.db.Get_Mode(inode) == stat.S_IFDIR

    def isfile(self, path):                                                     # OK
        """Check if a path references a file.

        :param path: a path in the filessystem

        :rtype: bool

        :raises ParentDirectoryMissingError
        :raises ResourceInvalidError
        :raises ResourceNotFoundError:  If the path does not exist
        """
        return not self.isdir(path)


    def listdir(self, path="./", wildcard=None, full=False, absolute=False, # OK
                      dirs_only=False, files_only=False):
        """Lists the files and directories under a given path.
        The directory contents are returned as a list of unicode paths.

        :param path: root of the path to list
        :type path: string
        :param wildcard: Only returns paths that match this wildcard
        :type wildcard: string containing a wildcard, or a callable that accepts a path and returns a boolean
        :param full: returns full paths (relative to the root)
        :type full: bool
        :param absolute: returns absolute paths (paths begining with /)
        :type absolute: bool
        :param dirs_only: if True, only return directories
        :type dirs_only: bool
        :param files_only: if True, only return files
        :type files_only: bool

        :rtype: iterable of paths

        :raises UnsupportedError: if the method was not defined

        :raises ParentDirectoryMissingError: if a containing directory is missing
        :raises ResourceInvalidError:        if the path exists, but is not a directory
        :raises ResourceNotFoundError:       if the path is not found
        """
        if self.dir_class:
            dir = self.dir_class(self, path)
            return self._listdir_helper(path, dir.list(), wildcard, full,
                                        absolute, dirs_only, files_only)

        raise UnsupportedError("list dir")

    def makedir(self, path, recursive=False, allow_recreate=False):             # OK
        """Make a directory on the filesystem.

        :param path: path of directory
        :param recursive: if True, any intermediate directories will also be created
        :type recursive: bool
        :param allow_recreate: if True, re-creating a directory wont be an error
        :type allow_create: bool

        :raises DestinationExistsError: if the path is already a directory, and allow_recreate is False
        :raises UnsupportedError:       if the method was not defined

        :raises ParentDirectoryMissingError: if a containing directory is missing and recursive is False
        :raises ResourceInvalidError:        if a path is an existing file
        :raises ResourceNotFoundError:       if the path is not found
        """
        if self.dir_class:
            dir = self.dir_class(self, path)
            dir.make(recursive, allow_recreate)

        raise UnsupportedError("make dir")

    def open(self, path, mode="r", **kwargs):
        """Open the given path as a file-like object.

        :param path: a path to the file that should be opened
        :param mode: mode of file to open, identical to the mode string used
            in 'file' and 'open' builtins
        :param kwargs: additional (optional) keyword parameters that may
            be required to open the file

        :rtype: a file-like object

        :raises UnsupportedError: if the method was not defined

        :raises ParentDirectoryMissingError: if a containing directory is missing and recursive is False
        :raises ResourceInvalidError:        if a parent path is an file
        :raises ResourceNotFoundError:       if the path is not found
        """
        if self.file_class:
            return self.file_class(self, path, mode, kwargs)

        raise UnsupportedError("open file")

    def remove(self, path):                                                     # OK
        """Remove a file from the filesystem.

        :param path: Path of the resource to remove

        :raises ParentDirectoryMissingError: if a containing directory is missing and recursive is False
        :raises ResourceInvalidError:        if the path is a directory or a parent path is an file
        :raises ResourceNotFoundError:       if the path is not found
        """
        # Return error if triying to unlink root path of the filesystem
        if path == os.sep:
            raise ResourceError(path)

        # Get inode and name from path
        inode, name = self.Path2InodeName(path[1:])

        # If the dir entry is a directory
        # raise error
        if self.db.Get_Mode(inode) == stat.S_IFDIR:
            raise ResourceInvalidError(path)

        # Unlink dir entry
        self.db.unlink(inode, name)

    def removedir(self, path, recursive=False, force=False):                    # OK
        """Remove a directory from the filesystem

        :param path: path of the directory to remove
        :param recursive: if True, then empty parent directories will be removed
        :type recursive: bool
        :param force: if True, any directory contents will be removed
        :type force: bool

        :raises DirectoryNotEmptyError: if the directory is not empty and force is False
        :raises UnsupportedError:       if the method was not defined

        :raises ParentDirectoryMissingError: if a containing directory is missing
        :raises ResourceInvalidError:        if the path or a parent path is not a directory
        :raises ResourceNotFoundError:       if the path is not found
        """
        if self.dir_class:
            dir = self.dir_class(self, path)
            dir.remove(recursive, force)

        raise UnsupportedError("remove dir")

    def rename(self, src, dst):                                                 # OK
        """Renames a file or directory

        :param src: path to rename
        :param dst: new name

        :raises ParentDirectoryMissingError: if a containing directory is missing
        :raises ResourceInvalidError:        if the path or a parent path is not a directory
                                             or src is a parent of dst
                                             or one of src or dst is a dir and the other not 
        :raises ResourceNotFoundError:       if the src path does not exist
        """
        if src == dst:
            return

        if src in dst:
            raise ResourceInvalidError(src)

        src = src[1:]
        dst = dst[1:]

        # Get parent dir inodes and names
        parent_inode_old, name_old = self.Path2InodeName(src)
        parent_inode_new, name_new = self.Path2InodeName(dst)

        # If dst exist, unlink it before rename src link
        if self.db.Get_Inode(parent_inode_new, name_new) != None:
            # If old path type is different from new path type then raise error
            type_old = self.db.Get_Mode(self.Get_Inode(name_old, parent_inode_old))
            type_new = self.db.Get_Mode(self.Get_Inode(name_new, parent_inode_new))

            if type_old != type_new:
                raise ResourceInvalidError(src)

            # Unlink new path and rename old path to new
            self.db.unlink(parent_inode_new, name_new)

        # Rename old link
        self.db.rename(parent_inode_old, name_old,
                       parent_inode_new, name_new)


    #
    # Non - Essential methods
    #

#    def copy(self, src, dst, overwrite=False, chunk_size=16384):
#        """Copies a file from src to dst.
#
#        :param src: the source path
#        :param dst: the destination path
#        :param overwrite: if True, then an existing file at the destination may
#            be overwritten; If False then DestinationExistsError
#            will be raised.
#        :param chunk_size: size of chunks to use if a simple copy is required
#            (defaults to 16K).
#        """
#        pass


#    def copydir(self, src, dst, overwrite=False, ignore_errors=False, chunk_size=16384):
#        """copies a directory from one location to another.
#
#        :param src: source directory path
#        :param dst: destination directory path
#        :param overwrite: if True then any existing files in the destination
#            directory will be overwritten
#        :type overwrite: bool
#        :param ignore_errors: if True, exceptions when copying will be ignored
#        :type ignore_errors: bool
#        :param chunk_size: size of chunks to use when copying, if a simple copy
#            is required (defaults to 16K)
#        """
#        pass


#    def desc(self, path):
#        """Returns short descriptive text regarding a path. Intended mainly as
#        a debugging aid
#
#        :param path: A path to describe
#        :rtype: str
#        
#        """
#        pass


#    def exists(self, path):
#        """Check if a path references a valid resource.
#
#        :param path: A path in the filessystem
#        :rtype: bool
#        """
#        pass


#    def move(self, src, dst, overwrite=False, chunk_size=16384):
#        """moves a file from one location to another.
#
#        :param src: source path
#        :param dst: destination path
#        :param overwrite: if True, then an existing file at the destination path
#            will be silently overwritten; if False then an exception
#            will be raised in this case.
#        :type overwrite: bool
#        :param chunk_size: Size of chunks to use when copying, if a simple copy
#            is required
#        :type chunk_size: integer
#        """
#        pass


#    def movedir(self, src, dst, overwrite=False, ignore_errors=False, chunk_size=16384):
#        """moves a directory from one location to another.
#
#        :param src: source directory path
#        :param dst: destination directory path
#        :param overwrite: if True then any existing files in the destination
#            directory will be overwritten
#        :param ignore_errors: if True then this method will ignore FSError
#            exceptions when moving files
#        :param chunk_size: size of chunks to use when copying, if a simple copy
#            is required
#        """
#        pass


    def opendir(self, path):
        """Opens a directory and returns a FS object representing its contents.

        :param path: path to directory to open
        :rtype: An FS object
        """
        if self.dir_class:
            return self.dir_class(self, path)

        raise UnsupportedError("open dir")


#    def safeopen(self, *args, **kwargs):
#        """Like 'open', but returns a NullFile if the file could not be opened.
#
#        A NullFile is a dummy file which has all the methods of a file-like object,
#        but contains no data.
#
#        :rtype: file-like object
#
#        """
#        pass


#    def settimes(self, path, accessed_time=None, modified_time=None):
#        """Set the accessed time and modified time of a file
#        
#        :param path: path to a file
#        :param accessed_time: a datetime object the file was accessed (defaults to current time) 
#        :param modified_time: a datetime object the file was modified (defaults to current time)
#        
#        """
#        pass


    #
    # Utility methods
    #

#    def createfile(self, path, data=""):
#        """A convenience method to create a new file from a string.
#
#        :param path: a path of the file to create
#        :param data: a string or a file-like object containing the contents for the new file
#        """
#        pass


#    def getcontents(self, path):
#        """Returns the contents of a file as a string.
#
#        :param path: A path of file to read
#        :rtype: str
#        :returns: file contents
#        """
#        pass


#    def getsize(self, path):
#        """Returns the size (in bytes) of a resource.
#
#        :param path: a path to the resource
#        :rtype: integer
#        :returns: the size of the file
#        """
#        pass


    def isdirempty(self, path):
        """Check if a directory is empty (contains no files or sub-directories)

        @param path: a directory path

        @rtype: bool
        """
        if self.file_class:
            dir = self.file_class(self, path)
            return dir.isempty()

        raise UnsupportedError("is empty dir")


#    def makeopendir(self, path, recursive=False):
#        """makes a directory (if it doesn't exist) and returns an FS object for
#        the newly created directory.
#
#        :param path: path to the new directory
#        :param recursive: if True any intermediate directories will be created
#
#        """
#        pass


#    def walk(self,
#             path="/",
#             wildcard=None,
#             dir_wildcard=None,
#             search="breadth",
#             ignore_errors=False):
#        """Walks a directory tree and yields the root path and contents.
#        Yields a tuple of the path of each directory and a list of its file
#        contents.
#
#        :param path: root path to start walking
#        :param wildcard: if given, only return files that match this wildcard
#        :type wildcard: A string containing a wildcard (e.g. *.txt) or a callable that takes the file path and returns a boolean
#        :param dir_wildcard: if given, only walk directories that match the wildcard
#        :type dir_wildcard: A string containing a wildcard (e.g. *.txt) or a callable that takes the directory name and returns a boolean
#        :param search: -- a string dentifying the method used to walk the directories. There are two such methods:
#            * 'breadth' Yields paths in the top directories first
#            * 'depth' Yields the deepest paths first
#        :param ignore_errors: ignore any errors reading the directory
#
#        """
#        pass


#    def walkfiles(self,
#                  path="/",
#                  wildcard=None,
#                  dir_wildcard=None,
#                  search="breadth",
#                  ignore_errors=False ):
#        """Like the 'walk' method, but just yields file paths.
#
#        :param path: root path to start walking
#        :param wildcard: if given, only return files that match this wildcard
#        :type wildcard: A string containing a wildcard (e.g. *.txt) or a callable that takes the file path and returns a boolean
#        :param dir_wildcard: if given, only walk directories that match the wildcard
#        :type dir_wildcard: A string containing a wildcard (e.g. *.txt) or a callable that takes the directory name and returns a boolean
#        :param search: same as walk method
#        :param ignore_errors: ignore any errors reading the directory
#        """
#        pass


#    def walkdirs(self,
#                 path="/",
#                 wildcard=None,
#                 search="breadth",
#                 ignore_errors=False):
#        """Like the 'walk' method but yields directories.
#
#        :param path: root path to start walking
#        :param wildcard: if given, only return dictories that match this wildcard
#        :type wildcard: A string containing a wildcard (e.g. *.txt) or a callable that takes the directory name and returns a boolean
#        :param search: same as the walk method
#        :param ignore_errors: ignore any errors reading the directory
#        """
#        pass


    def Get_Inode(self, path, inode=0):                                          # OK
        '''
        Get the inode of a path
        '''
#        print >> sys.stderr, '*** Get_Inode', repr(path),inode

        # If there are path elements
        # get their inodes
        if path:
            path = path.partition(os.sep)

            # Get inode of the dir entry
            inode = self.db.Get_Inode(inode, path[0])

            # If there's no such dir entry, raise the adecuate exception
            # depending of it's related to the resource we are looking for
            # or to one of it's parents
            if inode == None:
                if os.sep in path:
                    raise ParentDirectoryMissingError(path)
                else:
                    raise ResourceNotFoundError(path)

            # If the dir entry is a directory
            # get child inode
            if self.db.Get_Mode(inode) == stat.S_IFDIR:
                return self.Get_Inode(path[2], inode)

            # If is not a directory and is not the last path element
            # return error
            if path[2]:
                raise ResourceInvalidError(path)

        # Path is empty, so
        # * it's the root path
        # * or we consumed it
        # * or it's not a directory and it's the last path element
        # so return computed inode
        return inode

    def Path2InodeName(self, path):                                             # OK
        '''
        Get the parent dir inode and the name of a dir entry defined by path
        '''
#        print >> sys.stderr, '*** Path2InodeName', repr(path)
        path = path.rpartition(os.sep)
        inode = self.Get_Inode(path[0])

        return inode, path[2]