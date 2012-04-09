'''
Created on 16/08/2010

@author: piranna
'''

import errno
import sys

import fuse
fuse.fuse_python_api = (0, 2)

import Dir
import File

from ...base.fs import FS as BaseFS



class Filesystem(BaseFS, fuse.Fuse):
    def __init__(self, db_file, db_dirPath, drive, sector_size=512, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)

        # This thing that is like a ugly hack it seems that is the correct way
        # to pass parameters to the FUSE core as it's explained at
        # https://techknowhow.library.emory.edu/blogs/rsutton/2009/01/16/python-fuse-command-line-arguments
        # and at the Xmp.py example code. You have to set the default values
        # to object attributes that will be overwritten later by the parser.
        # Really too little pythonic...
        self.db_file = db_file
        self.db_dirPath = db_dirPath

        self.drive = drive
        self.sector_size = sector_size

        self.parser.add_option(mountopt="db_file", metavar="DB_FILE",
                               default=self.db_file,
                               help="filesystem metadata database")
        self.parser.add_option(mountopt="db_dirPath", metavar="DB_DIRPATH",
                               default=self.db_dirPath,
                               help="filesystem database SQL queries directory")
        self.parser.add_option(mountopt="drive", metavar="DRIVE",
                               default=self.drive,
                               help="filesystem drive")
        self.parser.add_option(mountopt="sector_size", metavar="SECTOR_SIZE",
                               default=self.sector_size,
                               help="filesystem sector size")

        self.parse(values=self, errex=1)

#        self.db = DB.DB(self.db)
#        self.ll = LL.LL(self.drive, sector_size)

        # http://sourceforge.net/apps/mediawiki/fuse/index.php?title=FUSE_Python_Reference#File_Class_Methods
        # http://old.nabble.com/Python:-Pass-parameters-to-file_class-td18301066.html

        class wrapped_dir_class(Dir.Dir):
            def __init__(self2, *a, **kw):
                Dir.Dir.__init__(self2, self, *a, **kw)

        class wrapped_file_class(File.File):
            def __init__(self2, *a, **kw):
                File.File.__init__(self2, self, *a, **kw)

        self.dir_class = wrapped_dir_class
        self.file_class = wrapped_file_class

        BaseFS.__init__(self, self.db_file, self.db_dirPath, self.drive,
                        sector_size)


    # Overloaded
    def access(self, path, mode):
        print >> sys.stderr, '*** access'
        return -errno.ENOSYS


#    def bmap(self):
#        print >> sys.stderr, '*** bmap'

#        return -errno.ENOSYS


#    def chmod(self, path,mode):
#        print >> sys.stderr, '*** chmod', path,mode
#        return -errno.ENOSYS


#    def chown(self, path,user,group):
#        print >> sys.stderr, '*** chown', path,user,group
#        return -errno.ENOSYS


#    def fsinit(self):
#        print >> sys.stderr, '*** fsinit'
#        return -errno.ENOSYS


#    def fsdestroy(self):
#        print >> sys.stderr, '*** fsdestroy'
#        return -errno.ENOSYS


#    def getxattr(self, path,name,size):
#        print >> sys.stderr, '*** getxattr', path,name,size
#        return -errno.ENOSYS


#    def listxattr(self, path,size):
#        print >> sys.stderr, '*** listxattr', path,size
#        return -errno.ENOSYS


#    def removexattr(self):
#        print >> sys.stderr, '*** removexattr'
#        return -errno.ENOSYS


## [BUG] http://sourceforge.net/mailarchive/forum.php?thread_name=4B4608C7.9030901%40hartwork.org&forum_name=fuse-devel
#
#    def utime(self, path,times=None):                                           # FAILURE
#        '''
#        Set the access and modification time stamps of PATH
#        '''
#        print >> sys.stderr, '*** utime', path,times
#        if times==None:
#            times = (None,None)
#
#        return self.utimens(path, times[0],times[1])
#
#
#    def utimens(self, path,ts_acc=None,ts_mod=None):                            # FAILURE
#        '''
#        Set the access and modification time stamps of PATH
#        '''
#        print >> sys.stderr, '*** utimens', path,ts_acc,ts_mod
#        inode = self._Get_Inode(path[1:])
#        if inode < 0:
#            return inode
#
#        if ts_acc == None: ts_acc = "now"
#        if ts_mod == None: ts_mod = "now"
#        self.db.utimens(inode=inode, access=ts_acc,modification=ts_mod)
#
#        return 0