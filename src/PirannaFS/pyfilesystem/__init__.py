'''
Created on 16/08/2010

@author: piranna
'''

from fs import base

import Dir
import File

import FS



class FileSystem(FS.FileSystem, base.FS):
    def __init__(self):
        base.FS.__init__(self)

        db = '../test/db.sqlite'
        drive = '../test/disk_part.img'
        sector = 512

        FS.FileSystem.__init__(self, db,drive,sector)


    #
    # Essential methods
    #

#    def getinfo(self, path):
#        """Returns information for a path as a dictionary. The exact content of
#        this dictionary will vary depending on the implementation, but will
#        likely include a few common values.
#
#        :param path: a path to retrieve information for
#        :rtype: dict
#        """
#        pass


#    def isdir(self, path):
#        """Check if a path references a directory.
#
#        :param path: a path in the filessystem
#        :rtype: bool
#
#        """
#        pass


#    def isfile(self, path):
#        """Check if a path references a file.
#
#        :param path: a path in the filessystem
#        :rtype: bool
#
#        """
#        pass


#    def listdir(self,   path="./",
#                        wildcard=None,
#                        full=False,
#                        absolute=False,
#                        dirs_only=False,
#                        files_only=False):
#        """Lists the the files and directories under a given path.
#
#        The directory contents are returned as a list of unicode paths.
#
#        :param path: root of the path to list
#        :type path: string
#        :param wildcard: Only returns paths that match this wildcard
#        :type wildcard: string containing a wildcard, or a callable that accepts a path and returns a boolean
#        :param full: returns full paths (relative to the root)
#        :type full: bool
#        :param absolute: returns absolute paths (paths begining with /)
#        :type absolute: bool
#        :param dirs_only: if True, only return directories
#        :type dirs_only: bool
#        :param files_only: if True, only return files
#        :type files_only: bool        
#        :rtype: iterable of paths
#
#        :raises ResourceNotFoundError: if the path is not found
#        :raises ResourceInvalidError: if the path exists, but is not a directory
#
#        """
#        pass


#    def makedir(self, path, recursive=False, allow_recreate=False):
#        """Make a directory on the filesystem.
#
#        :param path: path of directory
#        :param recursive: if True, any intermediate directories will also be created
#        :type recursive: bool
#        :param allow_recreate: if True, re-creating a directory wont be an error
#        :type allow_create: bool
#
#        :raises DestinationExistsError: if the path is already a directory, and allow_recreate is False
#        :raises ParentDirectoryMissingError: if a containing directory is missing and recursive is False
#        :raises ResourceInvalidError: if a path is an existing file
#
#        """
#        pass


#    def open(self, path, mode="r", **kwargs):
#        """Open a the given path as a file-like object.
#
#        :param path: a path to file that should be opened
#        :param mode: ,ode of file to open, identical to the mode string used
#            in 'file' and 'open' builtins
#        :param kwargs: additional (optional) keyword parameters that may
#            be required to open the file        
#        :rtype: a file-like object
#        """
#        raise UnsupportedError("open file")


#    def remove(self, path):
#        """Remove a file from the filesystem.
#
#        :param path: Path of the resource to remove
#
#        :raises ResourceNotFoundError: if the path does not exist
#        :raises ResourceInvalidError: if the path is a directory
#
#        """
#        pass


#    def removedir(self, path, recursive=False, force=False):
#        """Remove a directory from the filesystem
#
#        :param path: path of the directory to remove
#        :param recursive: pf True, then empty parent directories will be removed
#        :type recursive: bool
#        :param force: if True, any directory contents will be removed
#        :type force: bool
#
#        :raises ResourceNotFoundError: If the path does not exist
#        :raises ResourceInvalidError: If the path is not a directory
#        :raises DirectoryNotEmptyError: If the directory is not empty and force is False
#
#        """
#        pass


#    def rename(self, src, dst):
#        """Renames a file or directory
#
#        :param src: path to rename
#        :param dst: new name
#        """
#        pass


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


#    def opendir(self, path):
#        """Opens a directory and returns a FS object representing its contents.
#
#        :param path: path to directory to open
#        :rtype: An FS object
#        """
#        pass


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


#    def isdirempty(self, path):
#        """Check if a directory is empty (contains no files or sub-directories)
#
#        :param path: a directory path
#        :rtype: bool
#        """
#        pass


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