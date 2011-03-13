'''
Created on 15/08/2010

@author: piranna
'''

import errno
import os
import stat

import plugins



class Dir:
    '''
    classdocs
    '''

    def __init__(self, fs, path):                                              # OK
        '''
        Constructor
        '''
        self.__inode = self.Get_Inode(path[1:])
        self.__db = fs.db

        # Inode is not from a dir
        if self.__db.Get_Mode(self.__inode) != stat.S_IFDIR:
            raise ResourceInvalidError(path)

    def isempty(self):
        return True

    def make(self, recursive=False, allow_recreate=False):
        try:
            parent_dir_inode,name = self.Path2InodeName(path)

        except ResourceNotFoundError:
            if not recursive:
                raise

            # Parent doesn't exist but we want to create them
            path = path.rpartition(os.sep)
            parent_dir_inode = self._mkdir(path[0], mode, recursive)
            name = path[2]

        # If parent dir is not a directory,
        # return error
        if self.db.Get_Mode(parent_dir_inode) != stat.S_IFDIR:
            raise ResourceInvalidError(path)

        # If dir_entry exist,
        # return its inode if it's a directory or error
        inode = self.Get_Inode(name,parent_dir_inode)
        if inode >= 0:
#            if self.db.Get_Mode(inode) == stat.S_IFDIR:
#                return inode
            return -errno.EEXIST

        # Make directory
        inode = self.db.mkdir()
        self.db.link(parent_dir_inode,name,inode)

        return inode


        if error < 0:
            if error == -errno.EEXIST and not allow_recreate:
                raise DestinationExistsError(path)

            if error == -errno.ENOENT:
                raise ParentDirectoryMissingError(path)

    def read(self):                                                          # OK
#        yield unicode('.')
#        yield unicode('..')

        for dir_entry in self.__db.readdir(self.__inode):
            if dir_entry['name']:
                yield unicode(dir_entry['name'])

        plugins.send("DIR.readdir")

    def remove(self, recursive=False, force=False):
#        if force:
#            pass

        # Inode dir is not empty 
        if self.db.readdir(self.__inode):
            return -errno.ENOTEMPTY

        # Unlink removed directory and return it's operation result
        return self.db.unlink(parent_dir_inode,name)

        if recursive:
            path = path.rsplit(os.sep,1)[0]
            self.removedir(path,True)