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
            self._inode = fs.Get_Inode(path[1:])
        except ResourceError:
            self._inode = None
        else:
            # If inode is not a dir, raise error
            if fs.db.Get_Mode(self._inode) != stat.S_IFDIR:
                raise ResourceInvalidError(path)


    # Overloaded

    # inits
#    def opendir(self):
#        print >> sys.stderr, '*** opendir'
#        return -errno.ENOSYS


    # proxied
#    def fsyncdir(self):
#        print >> sys.stderr, '*** fsyncdir'
#        return -errno.ENOSYS


    def readdir(self, offset=None):                                         # OK
#        print >> sys.stderr, '*** readdir', offset
        if self._inode == None:
            raise ResourceNotFoundError(self.path)

        plugins.send("Dir.list.begin")

#        yield fuse.Direntry('.')
#        yield fuse.Direntry('..')

        for dir_entry in self.db.readdir(self._inode):
            if dir_entry['name']:
                yield fuse.Direntry(unicode(dir_entry['name']))
#                yield fuse.Direntry(str(dir_entry['name']))

        plugins.send("DIR.list.end")


#    def releasedir(self):
#        print >> sys.stderr, '*** releasedir'
#        return -errno.ENOSYS
