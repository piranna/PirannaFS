'''
Created on 15/08/2010

@author: piranna
'''

import sys

import errno

import fuse

import plugins

from ..Dir import BaseDir


class Dir(BaseDir):
    '''
    classdocs
    '''

    def __init__(self, fs, path):                                           # OK
        '''
        Constructor
        '''
#        print >> sys.stderr, '*** Dir __init__',fs, path

        BaseDir.__init__(self, fs, path)

        try:
            self._inode = fs._Get_Inode(path[1:])
        except ResourceError:
            self._inode = None
        else:
            # If inode is not a dir, raise error
            if fs.db.Get_Mode(inode=self._inode) != stat.S_IFDIR:
                raise ResourceInvalidError(path)


    # Overloaded

#    def fsyncdir(self):
#        print >> sys.stderr, '*** fsyncdir'
#        return -errno.ENOSYS


#    def opendir(self):
#        print >> sys.stderr, '*** opendir'
#        return -errno.ENOSYS


    def readdir(self, offset=None):                                         # OK
        """Lists the files and directories under a given path.
        The directory contents are returned as a list of fuse.Direntry structs.

        @rtype: iterable of fuse.Direntry structs
        """
        for dir_entry in self._list():
            yield fuse.Direntry(dir_entry)


#    def releasedir(self):
#        print >> sys.stderr, '*** releasedir'
#        return -errno.ENOSYS
