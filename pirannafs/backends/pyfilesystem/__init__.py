'''
Created on 16/08/2010

@author: piranna
'''

from os.path import split
from stat    import S_IFDIR

from fs        import base
from fs.errors import ParentDirectoryMissingError, ResourceInvalidError
from fs.errors import ResourceNotFoundError

from pirannafs.base.fs import FS as BaseFS
from pirannafs.errors  import IsADirectoryError, NotADirectoryError
from pirannafs.errors  import ParentDirectoryMissing, ResourceNotFound

#import plugins

from dir  import Dir
from file import File


class FS(BaseFS, base.FS):
    _meta = {"pickle_contents": False, "thread_safe": False}

    _dir_class_map = {'copy':      'copydir',
                      'isempty':   'isdirempty',
                      'ilist':     'ilistdir',
                      'ilistinfo': 'ilistdirinfo',
                      'list':      'listdir',
                      'listinfo':  'listdirinfo',
                      'make':      'makedir',
                      'makeopen':  'makeopendir',
                      'move':      'movedir',
                      'open':      'opendir',
                      'remove':    'removedir',
                      'walk':      'walk',
                      'walkdirs':  'walkdirs',
                      'walkfiles': 'walkfiles'}

    _file_class_map = {'contents': 'getcontents',
                       'copy':     'copy',
                       'move':     'move',
                       'open':     'open',
                       'remove':   'remove',
                       'safeopen': 'safeopen',
                       'size':     'getsize'}

    dir_class = Dir
    file_class = File

    def _delegate_methods(self, klass, class_map):
        """Method that looks inside class `klass` and its ancestors for some
        methods to delegate from the base filesystem class according to
        `class_map`
        """
        if klass:
            # Get the `klass` and its ancestors methods resolved in MRO
            methodsMRO = []
            for c in klass.mro():
                methodsMRO.extend(c.__dict__.iteritems())

            # Run over `class_map` looking for known methods in `methodsMRO`
            for class_method, fs_method in class_map.iteritems():
                for method_name, method_func in methodsMRO:

                    # If mapped method exists in `klass` or its ancestors (and
                    # assuming fs programmer didn't do something stupid...),
                    # we create a new function that creates a `klass` instance
                    # and call the delegated method
                    if class_method == method_name:
                        # [Hack] reference to the function to circunvalate the
                        # fact that `method_func` is common for delegated
                        # methods. Really it should be possible to assign it
                        # without `applyMethod` function...
                        def applyMethod(func):
                            def method(self, path="", *args, **kwargs):
                                with klass(self, path) as obj:
                                    return func(obj, *args, **kwargs)

                            # Set the delegated method to the one we have just
                            # created
                            setattr(self.__class__, fs_method, method)

                        applyMethod(method_func)
                        break

    def __init__(self, db_file, drive, db_dirPath=None, sector_size=512):
        BaseFS.__init__(self, db_file, drive, db_dirPath, sector_size)
        base.FS.__init__(self)

        self._delegate_methods(self.dir_class, self._dir_class_map)
        self._delegate_methods(self.file_class, self._file_class_map)

#        print "__init__", plugins.send("FS.__init__", db=db_file, ll=self.ll)
#        plugins.send("FS.__init__", db=self.db, ll=self.ll)

    #
    # Essential methods
    #

    def getinfo(self, path):                                               # OK
        """Returns information for a path as a dictionary. The exact content of
        this dictionary will vary depending on the implementation, but will
        likely include a few common values.

        :param path: a path to retrieve information for

        :rtype: dict

        :raises ParentDirectoryMissingError
        :raises ResourceInvalidError
        :raises ResourceNotFoundError:  If the path does not exist
        """
        parent_dir, name = self._Path2InodeName(path)

        inode = self.db.Get_Inode(parent_dir=parent_dir, name=name)
        if inode == None:
            raise ResourceNotFoundError(path)

        return self.db.getinfo(parent_dir=parent_dir, name=name)._asdict()

    def isdir(self, path):                                                 # OK
        """Check if a path references a directory.

        :param path: a path in the filesystem

        :rtype: bool
        """
        try:
            inode = self._Get_Inode(path)
        except (NotADirectoryError,
                ParentDirectoryMissing, ResourceNotFound):
            return False
        return self.db.Get_Mode(inode=inode) == S_IFDIR

    def isfile(self, path):                                                # OK
        """Check if a path references a file

        :param path: a path in the filessystem

        :rtype: bool
        """
        try:
            inode = self._Get_Inode(path)
        except (IsADirectoryError, NotADirectoryError,
                ParentDirectoryMissing, ResourceNotFound):
            return False
        return self.db.Get_Mode(inode=inode) != S_IFDIR

    def rename(self, src, dst):                                            # OK
        """Renames a file or directory

        :param src: path to rename
        :param dst: new name

        :raises ParentDirectoryMissingError: if a containing directory is
            missing
        :raises ResourceInvalidError: if the path or a parent path is not a
            directory or src is a parent of dst or one of src or dst is a dir
            and the other not
        :raises ResourceNotFoundError: if the src path does not exist
        """
        if src == dst:
            return

        if src in dst:
            raise ResourceInvalidError(src)

        # Get parent dir inodes and names
        try:
            parent_inode_old, name_old = self._Path2InodeName(src)
            parent_inode_new, name_new = self._Path2InodeName(dst)
        except ParentDirectoryMissing, e:
            raise ParentDirectoryMissingError(e)

        # If dst exist, unlink it before rename src link
        inode = self.db.Get_Inode(parent_dir=parent_inode_new, name=name_new)
        if inode != None:
            # If old path type is different from new path type then raise error
            type_old = self.db.Get_Mode(inode=self._Get_Inode(name_old,
                                                             parent_inode_old))
            type_new = self.db.Get_Mode(inode=self._Get_Inode(name_new,
                                                             parent_inode_new))

            if type_old != type_new:
                raise ResourceInvalidError(src)

            # Unlink new path and rename old path to new
            self.db.unlink(parent_dir=parent_inode_new, name=name_new)

        # Rename old link
        self.db.rename(parent_old=parent_inode_old, name_old=name_old,
                       parent_new=parent_inode_new, name_new=name_new)


    #
    # Utility methods
    #

#    def createfile(self, path, data=""):
#        """A convenience method to create a new file from a string.
#
#        :param path: a path of the file to create
#        :param data: a string or a file-like object containing the contents for
#            the new file
#        """
#        pass

    def _Path2InodeName(self, path):                                       # OK
        '''
        Get the parent dir inode and the name of a dir entry defined by path
        '''
        path, name = split(path)
        try:
            inode = self._Get_Inode(path)
        except ResourceNotFound:
            raise ParentDirectoryMissing(path)

        return inode, name
