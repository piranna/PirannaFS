'''
Created on 02/04/2011

@author: piranna
'''

from os.path import split

from fs.errors import ParentDirectoryMissingError, ResourceNotFoundError


class BaseDir(object):
    '''
    classdocs
    '''


    def __init__(self, fs, path):
        '''
        Constructor
        '''
        self.fs = fs
        self.db = fs.db

        self.path = path
        path, self.name = split(path)

        try:
            self.parent = fs.Get_Inode(path)
        except (ParentDirectoryMissingError, ResourceNotFoundError):
            self.parent = path


    def isempty(self):
        """Check if a directory is empty (contains no files or sub-directories)

        @rtype: bool
        """
        print "BaseDir.isempty"
        return self.db.readdir(self._inode, 1)


    #
    # File-like interface
    #


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __iter__(self):
        return self