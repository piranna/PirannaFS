'''
Created on 09/04/2012

@author: piranna
'''

from os.path import abspath, dirname, join, sep, split
from sqlite3 import connect
from stat    import S_IFDIR

from antiorm.backends.sqlite import Sqlite
from antiorm.utils           import Namedtuple_factory

from ..errors import ParentDirectoryMissing, NotADirectoryError, ResourceNotFound
from ..LL     import LL


class FS(object):
    '''
    classdocs
    '''

    def __init__(self, db_file, drive, db_dirPath=None, sector_size=512):
        self.ll = LL(drive, sector_size)

        #
        # Database

#        db_conn = connect(db_file)
        db_conn = connect(db_file, check_same_thread=False)

        db_conn.row_factory = Namedtuple_factory
#        db_conn.isolation_level = None

        # SQLite tune-ups
        db_conn.execute("PRAGMA synchronous = OFF;")
        db_conn.execute("PRAGMA temp_store = MEMORY;")

        # Force enable foreign keys check
        db_conn.execute("PRAGMA foreign_keys = ON;")

        # Store data in UNIX timestamp instead ISO format (sqlite default)
        # and None objects as 'NULL' strings
        from datetime import datetime
        from time import mktime
        from sqlite3 import register_adapter

        def adapt_datetime(ts):
            return mktime(ts.timetuple())
        register_adapter(datetime, adapt_datetime)

        #
        # antiORM

        if not db_dirPath:
            db_dirPath = join(dirname(abspath(__file__)), '..', 'sql')
        self.db = Sqlite(db_conn, db_dirPath, True)

        # http://stackoverflow.com/questions/283707/size-of-an-open-file-object
        drive = self.ll._file

        def Get_NumSectors():
            drive.seek(0, 2)
            end = drive.tell()
            drive.seek(0)
            return (end - 1) // sector_size

        self.db.create(type=S_IFDIR, length=Get_NumSectors(), sector=0)

        self._freeSpace = None
        self.__sector_size = sector_size

    def _FreeSpace(self):
        if self._freeSpace == None:
            freespace = self.db.Get_FreeSpace()

            if freespace:
                self._freeSpace = freespace * self.__sector_size
            else:
                self._freeSpace = 0

        return self._freeSpace

    def _Get_Inode(self, path, inode=0):                                   # OK
        '''
        Get the inode of a path
        '''
#        print >> sys.stderr, '*** _Get_Inode', repr(path),inode

        # If there are path elements
        # get their inodes
        if path:
            parent, _, path = path.partition(sep)

            # Get inode of the dir entry
            inode = self.db.Get_Inode(parent_dir=inode, name=parent)

            # If there's no such dir entry, raise the adecuate exception
            # depending of it's related to the resource we are looking for
            # or to one of it's parents
            if inode == None:
                if path:
                    raise ParentDirectoryMissing(parent)
                else:
                    raise ResourceNotFound(parent)

            # If the dir entry is a directory
            # get child inode
            if self.db.Get_Mode(inode=inode) == S_IFDIR:
                return self._Get_Inode(path, inode)

            # If is not a directory and is not the last path element
            # return error
            if path:
                raise NotADirectoryError(path)

        # Path is empty, so
        # * it's the root path
        # * or we consumed it
        # * or it's not a directory and it's the last path element
        # so return computed inode
        return inode

    def _Path2InodeName(self, path):                                       # OK
        '''
        Get the parent dir inode and the name of a dir entry defined by path
        '''
#        print >> sys.stderr, '*** _Path2InodeName', repr(path)
        path, name = split(path)
        try:
            inode = self._Get_Inode(path)
        except ResourceNotFound:
            raise ParentDirectoryMissing(path)

        return inode, name
