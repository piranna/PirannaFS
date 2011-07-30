'''
Created on 15/08/2010

@author: piranna
'''

import sys

import errno

import fuse

import plugins



class Dir:
    '''
    classdocs
    '''

    def __init__(self, fs, path):                                               # OK
        '''
        Constructor
        '''
#        print >> sys.stderr, '*** Dir __init__',fs, path

        self.__inode = fs.Get_Inode(path[1:])
        self.__db = fs.db


    # Overloaded

    # inits
#    def opendir(self):
#        print >> sys.stderr, '*** opendir'
#        return -errno.ENOSYS


    # proxied
#    def fsyncdir(self):
#        print >> sys.stderr, '*** fsyncdir'
#        return -errno.ENOSYS


    def readdir(self, offset=None):                                             # OK
#        print >> sys.stderr, '*** readdir', offset
#        yield fuse.Direntry('.')
#        yield fuse.Direntry('..')

        for dir_entry in self.__db.readdir(self.__inode):
            if dir_entry['name']:
                yield fuse.Direntry(str(dir_entry['name']))

        plugins.send("DIR.readdir")


#    def releasedir(self):
#        print >> sys.stderr, '*** releasedir'
#        return -errno.ENOSYS
