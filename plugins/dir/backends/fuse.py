'''
Created on 15/08/2010

@author: piranna
'''

import errno
import sys

import fuse

import plugins

from ..base import BaseDir


class Dir(BaseDir):
    '''
    classdocs
    '''

    def __init__(self, fs, path):                                          # OK
        '''
        Constructor
        '''
#        print >> sys.stderr, '*** Dir __init__',fs, path

        BaseDir.__init__(self, fs, path)
#        BaseDir.__init__(self, fs, path[1:])

    # Overloaded

#    def fsyncdir(self):
#        print >> sys.stderr, '*** fsyncdir'
#        return -errno.ENOSYS

#    def opendir(self):
#        print >> sys.stderr, '*** opendir'
#        return -errno.ENOSYS

    def readdir(self, offset=None):                                        # OK
        """Lists the files and directories under a given path.
        The directory contents are returned as a list of fuse.Direntry structs.

        @rtype: iterable of fuse.Direntry structs
        """
        for direntry in self._list():
            yield fuse.Direntry(direntry)


#    def releasedir(self):
#        print >> sys.stderr, '*** releasedir'
#        return -errno.ENOSYS
