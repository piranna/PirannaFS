'''
Created on 20/09/2010

@author: piranna
'''

import stat

from os.path import abspath, dirname, join

import plugins

from pirannafs.base.fs import initDB
from pirannafs.errors  import FileExistsError, FileNotFoundError


class NotASymlink(OSError):
    pass


class symlinks(plugins.Plugin):
    def __init__(self):
        self.db = None

        plugins.connect(self.FS__init__, "FS.__init__")
        plugins.connect(self.readlink, "FS.readlink")
        plugins.connect(self.symlink, "FS.symlink")

    def FS__init__(self, db_file):
        self.db = initDB(db_file, join(dirname(abspath(__file__)), '..', '..',
                                  'pirannafs', 'sql'))
        self.db.create()

    def readlink(self, sender, path):
        '''
        Read a symlink to a file
        '''
#        print >> sys.stderr, '*** fs_readlink', sender,path

        if not path:
            raise FileNotFoundError(path)

        inode = sender.Get_Inode(path[1:])

        # Read symlink
        target = self.db.select(inode=inode)
#        print >> sys.stderr, "\t", target

        if target:
            return str(target['target'])

        raise NotASymlink(path)

    def symlink(self, sender, targetPath, linkPath):
        '''
        Make a symlink to a file
        symlink is only called if there isn't already another object
        with the requested linkname
        '''
#        print >> sys.stderr, '*** symlink', targetPath,linkPath

        # If no linkPath,
        # return error
        if not linkPath:
            raise FileNotFoundError(linkPath)

        # Get parent dir of linkPath
        link_parentInode, name = sender.Path2InodeName(linkPath[1:])

        # Check if exist a file, dir or symlink with the same name in this dir
        if sender.Get_Inode(name, link_parentInode) >= 0:
            raise FileExistsError(linkPath)

        # Make symlink
        inode = self.db._Make_Inode(stat.S_IFLNK)
        self.db.insert(inode=inode, target=targetPath)

        self.db.link(link_parentInode, name, inode)


if __name__ == '__main__':
    import unittest

    class Test(unittest.TestCase):
        pass

    unittest.main()
