'''
Created on 16/08/2010

@author: piranna
'''

import sys

import errno
import os
import stat

import fuse
fuse.fuse_python_api = (0, 2)

import plugins

import Dir
import File
import DB
import LL



class FileSystem(fuse.Fuse):
    def __init__(self, *args,**kw):
        fuse.Fuse.__init__(self, *args,**kw)

        # This thing that is like a ugly hack it seems that is the correct way
        # to pass parameters to the FUSE core as it's explained at
        # https://techknowhow.library.emory.edu/blogs/rsutton/2009/01/16/python-fuse-command-line-arguments
        # and at the Xmp.py example code. You have to set the default values
        # to object attributes that will be overwritten later by the parser.
        # Really too little pythonic...
        self.db = '../test/db.sqlite'
        self.drive = '../test/disk_part.img'
        self.sector = 512

        self.parser.add_option(mountopt="db", metavar="DB",
                               default=self.db,
                               help="filesystem metadata database")
        self.parser.add_option(mountopt="drive", metavar="DRIVE",
                               default=self.drive,
                               help="filesystem drive")
        self.parser.add_option(mountopt="sector", metavar="SECTOR_SIZE",
                               default=self.sector,
                               help="filesystem sector size")

        self.parse(values=self, errex=1)

        self.db = DB.DB(self.db)
        self.ll = LL.LL(self.drive,self.sector)

        # http://sourceforge.net/apps/mediawiki/fuse/index.php?title=FUSE_Python_Reference#File_Class_Methods
        # http://old.nabble.com/Python:-Pass-parameters-to-file_class-td18301066.html

        class wrapped_dir_class(Dir.Dir):
            def __init__(self2, *a,**kw):
                Dir.Dir.__init__(self2, self, *a,**kw)

        class wrapped_file_class(File.File):
            def __init__(self2, *a,**kw):
                File.File.__init__(self2, self, *a,**kw)

        self.dir_class = wrapped_dir_class
        self.file_class = wrapped_file_class
#        print >> sys.stderr, '*** FS.__init__'
        plugins.send("FS.__init__", db=self.db, ll=self.ll)


    # Overloaded
    def access(self, path,mode):
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


    def getattr(self, path):                                                    # OK
#        print >> sys.stderr, '\n*** FS.getattr', path

        inodeName = self.Path2InodeName(path[1:])
        if inodeName < 0:
            return inodeName
        parent_dir,name = inodeName

#        print >> sys.stderr, "\t",repr(parent_dir),repr(name)

        dir_entry = self.db.getattr(parent_dir,name)
#        print >> sys.stderr, "\t",repr(dir_entry)

        if not dir_entry:
            return -errno.ENOENT
        return dir_entry


#    def getxattr(self, path,name,size):
#        print >> sys.stderr, '*** getxattr', path,name,size
#        return -errno.ENOSYS


    def link(self, targetPath,linkPath):                                        # OK
        '''
        Link to a file
        '''
#        print >> sys.stderr, '*** link', targetPath,linkPath
        # Check if targetPath is a valid path
        targetInode = self.Get_Inode(targetPath[1:])
        if targetInode < 0:
            return targetInode

        # Get parent dir of linkPath
        inodeName = self.Path2InodeName(linkPath[1:])
        if inodeName < 0:
            return inodeName
        link_parentInode,name = inodeName

        # Check if linkPath exist
        if self.Get_Inode(name,link_parentInode) >=0:
            return -errno.EEXIST

        # Make link
        self.db.link(link_parentInode,name,targetInode)

        # Return success
        return 0


#    def listxattr(self, path,size):
#        print >> sys.stderr, '*** listxattr', path,size
#        return -errno.ENOSYS


    def mkdir(self, path,mode):                                                 # OK
#        print >> sys.stderr, '*** mkdir', path,mode
        error = self.__Mkdir(path[1:],mode)
        if error < 0:
            return error

        return 0


    def readlink(self, path):
#        print >> sys.stderr, '*** readlink', path

        response = plugins.send("FS.readlink", sender=self, path=path)
#        print >> sys.stderr, '\tresponse', response
        if response:
            return str(response[0][1])

        return ""


#    def removexattr(self):
#        print >> sys.stderr, '*** removexattr'
#        return -errno.ENOSYS


    def rename(self, path_old,path_new):                                        # OK
        '''
        Rename a file
        '''
#        print >> sys.stderr, '*** rename', path_old,path_new

        if path_old == path_new:
            return 0

        if path_old in path_new:
            return -errno.EINVAL

        path_old = path_old[1:]
        path_new = path_new[1:]

        # Get old parent dir inode and name
        inodeName = self.Path2InodeName(path_old)
        if inodeName < 0:
            return inodeName
        parent_dir_inode_old,name_old = inodeName

        # Get type of old path
        type_old = self.db.Get_Mode(self.Get_Inode(name_old,parent_dir_inode_old))

        inodeName = self.Path2InodeName(path_new)
        if inodeName < 0:

            # If new doesn't exist,
            # rename link directly
            if inode == -errno.ENOENT:
                path_new = path_new.rpartition(os.sep)

                self.db.rename(parent_dir_inode_old,name_old,
                               self.__Mkdir(path_new[0]),path_new[2])

                # Return success
                return 0

            # Return error
            return inodeName
        parent_dir_inode_new,name_new = inodeName

        # Get type of new path
        type_new = self.db.Get_Mode(self.Get_Inode(name_new,parent_dir_inode_new))

        # Old path is a file and new path is a dir
        if(type_old != stat.S_IFDIR
        and type_new == stat.S_IFDIR):
            return -errno.EISDIR

        # Old path is a dir and new path is a file
        if(type_old == stat.S_IFDIR
        and type_new != stat.S_IFDIR):
            return -errno.ENOTDIR

        # Unlink new path and rename old path to new
        self.db.unlink(parent_dir_inode_new,name_new)
        self.db.rename(parent_dir_inode_old,name_old,
                       parent_dir_inode_new,name_new)

        # Return success
        return 0


    def rmdir(self, path):                                                      # OK
        '''
        Remove a directory
        '''
#        print >> sys.stderr, '*** rmdir', path

        inode = self.Get_Inode(path[1:])
        if inode < 0:
            return inode

        if self.db.Get_Mode(inode) != stat.S_IFDIR:
            return -errno.ENOTDIR

        aux = self.db.readdir(inode)
#        print >> sys.stderr, aux
        if aux:
            return -errno.ENOTEMPTY

        return self.unlink(path)


#    def setxattr(self):
#        print >> sys.stderr, '*** setxattr'
#        return -errno.ENOSYS


    def statfs(self):
#        print >> sys.stderr, '*** statfs'
        return fuse.StatVfs()


    def symlink(self, targetPath,linkPath):                                     # OK
#        print >> sys.stderr, '*** symlink', targetPath,linkPath

        response = plugins.send("FS.symlink", sender=self,
                                            targetPath=targetPath,
                                            linkPath=linkPath)
        if response:
            return response[0][1]
#        return 0


    def unlink(self, path):                                                     # OK
        '''
        Remove a dir entry
        '''
#        print >> sys.stderr, '*** unlink', path

        if path == os.sep:
            return -errno.EBUSY

        inodeName = self.Path2InodeName(path[1:])
        if inodeName < 0:
            return inodeName
        parent_dir_inode,name = inodeName

        self.db.unlink(parent_dir_inode,name)

        return 0


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
#        inode = self.Get_Inode(path[1:])
#        if inode < 0:
#            return inode
#
#        self.db.utimens(inode, ts_acc,ts_mod)
#
#        return 0


    # Shared
    def Get_Inode(self, path,inode=0):                                          # OK
        '''
        Get the inode of a path
        '''
#        print >> sys.stderr, '*** Get_Inode', repr(path),inode

        # If there are path elements
        # get their inodes
        if path:
            path = path.partition(os.sep)

            # Get inode of the dir entry
            inode = self.db.Get_Inode(inode,path[0])

            # There's no such dir entry
            if inode == None:
                return -errno.ENOENT

            # If the dir entry is a directory
            # get child inode
            if self.db.Get_Mode(inode) == stat.S_IFDIR:
                return self.Get_Inode(path[2],inode)

            # If is not a directory and is not the last path element
            # return error
            if path[2]:
                return -errno.ENOTDIR

        # If path is empty (we achieved root path)
        # or is not a directory and is last path element
        # return computed inode
        return inode


    def Path2InodeName(self, path):                                             # OK
        '''
        Get the parent dir inode and the name of a dir entry defined by path
        '''
#        print >> sys.stderr, '*** Path2InodeName', repr(path)
        path = path.rpartition(os.sep)

        inode = self.Get_Inode(path[0])
        if inode < 0:
#            print >> sys.stderr, '\t', inode
            return inode

#        print >> sys.stderr, '\t', inode,repr(path[2])
        return inode,path[2]


    # Private
    def __Mkdir(self, path,mode):                                               # OK
        inodeName = self.Path2InodeName(path)
        if inodeName >= 0:
            parent_dir_inode,name = inodeName

        elif inodeName == -errno.ENOENT:
            path = path.rpartition(os.sep)
            parent_dir_inode = self.__Mkdir(path[0], mode)
            name = path[2]

        else:
            return inodeName

        # If parent dir is not a directory,
        # return error
        if self.db.Get_Mode(parent_dir_inode) != stat.S_IFDIR:
            return -errno.ENOTDIR

        # If dir_entry exist,
        # return its inode if it's a directory or error
        inode = self.Get_Inode(name,parent_dir_inode)
        if inode >= 0:
            if self.db.Get_Mode(inode) == stat.S_IFDIR:
                return inode
            return -errno.EEXIST

        # Make directory
        inode = self.db.mkdir()
        self.db.link(parent_dir_inode,name,inode)

        return inode