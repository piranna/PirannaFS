'''
Created on 04/08/2010

@author: piranna
'''

import stat

from collections import namedtuple
from os      import listdir
from os.path import join, splitext

from sql import Compact, GetColumns, GetLimit


# Store data in UNIX timestamp instead ISO format (sqlite default)
import datetime, time
import sqlite3
def adapt_datetime(ts):
    return time.mktime(ts.timetuple())
sqlite3.register_adapter(datetime.datetime, adapt_datetime)


class DictObj(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        try:
            self[name] = value
        except KeyError:
            raise AttributeError(name)


def DictObj_factory(cursor, row):
    d = DictObj()
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DB():
    '''
    classdocs
    '''

    def _parseFunctions(self, path):
        for methodName, params in [
                 ("readdir", ('parent_dir', 'limit')),
                 ("rename", ('parent_old', 'name_old', 'parent_new', 'name_new')),
                 ("unlink", ('parent_dir', 'name')),
#                 ("Free_Chunks", ('chunk',)),
                 ("Get_Chunks", ('file', 'floor', 'ceil')),
                 ("Get_Chunks_Truncate", ('file', 'ceil')),
                 ("Set_Size", ('inode', 'size')),
                 ("Get_Size", ('inode',)),
                 ("Get_Inode", ('parent_dir', 'name')),
                 ("Get_Mode", ('inode',)),
                 ("Get_FreeChunk_BestFit", ('sectors_required', 'blocks')),
                 ("utimens", ('inode', 'access', 'modification')),
                 ("getinfo", ('parent_dir', 'name'))
                                         ]:
            with open(join(path, methodName + '.sql')) as f:
                sql = Compact(f.read(), path)

            # One-value function
            if GetLimit(sql) == 1:
                columns = GetColumns(sql)

                # Value function
                if len(columns) == 1 and columns[0] != '*':
                    def applyMethod(sql, methodName, params, column):
#                        Params = namedtuple('Params', params)
                        def method(self, *args):
#                            d = Params._make(*args)
                            d = {}
                            for index, param in enumerate(params):
                                d[param] = args[index]

                            result = self.connection.execute(sql, d)
                            result = result.fetchone()
                            if result:
                                return result[column]

                        setattr(self.__class__, methodName, method)

                    applyMethod(sql, methodName, params, columns[0])

                # Register function
                else:
                    def applyMethod(sql, methodName, params):
#                        Params = namedtuple('Params', params)
                        def method(self, *args):
#                            d = Params._make(*args)
                            d = {}
                            for index, param in enumerate(params):
                                d[param] = args[index]

                            result = self.connection.execute(sql, d)
                            return result.fetchone()

                        setattr(self.__class__, methodName, method)

                    applyMethod(sql, methodName, params)

            # Table function
            else:
                def applyMethod(sql, methodName, params):
#                    Params = namedtuple('Params', params)
                    def method(self, *args):
#                        d = Params._make(*args)
                        d = {}
                        for index, param in enumerate(params):
                            d[param] = args[index]

                        result = self.connection.execute(sql, d)
                        return result.fetchall()

                    setattr(self.__class__, methodName, method)

                applyMethod(sql, methodName, params)


    def __init__(self, connection, drive, sector_size):                     # OK
        '''
        Constructor
        '''
        self.connection = connection
        self.connect()

        def Get_NumSectors():
            # http://stackoverflow.com/questions/283707/size-of-an-open-file-object
            drive.seek(0, 2)
            end = drive.tell()
            drive.seek(0)
            return (end - 1) // sector_size

        self.__sector_size = sector_size

        self.__queries = self.__LoadQueries('/home/piranna/Proyectos/FUSE/PirannaFS/src/sql')
        self.__Create_Database(Get_NumSectors())

        self._parseFunctions('/home/piranna/Proyectos/FUSE/PirannaFS/src/sql')

    def __del__(self):
        self.connection.commit()
        self.connection.close()


    def connect(self):
        self.connection.row_factory = DictObj_factory
        self.connection.isolation_level = None

        # SQLite tune-ups
        self.connection.execute("PRAGMA synchronous = OFF;")
        self.connection.execute("PRAGMA temp_store = MEMORY;")  # Not so much

        # Force enable foreign keys check
        self.connection.execute("PRAGMA foreign_keys = ON;")


    def link(self, parent_dir, name, child_entry):                          # OK
#        print >> sys.stderr, '*** link', parent_dir,name,child_entry

        cursor = self.connection.cursor()
        cursor.execute(self.__queries['link'],
            {"parent_dir":parent_dir, "name":name, "child_entry":child_entry})

        return cursor.lastrowid


    def mkdir(self):                                                        # OK
        '''
        Make a new directory
        '''
        with self.connection:
            inode = self.__Make_DirEntry(stat.S_IFDIR)
            self.connection.execute(self.__queries['Dir.make'])

        return inode


    def mknod(self):                                                        # OK
        '''
        Make a new file
        '''
        with self.connection:
            inode = self.__Make_DirEntry(stat.S_IFREG)
            self.connection.execute(self.__queries['mknod'])

        return inode


#    def utimens(self, inode, access, modification):
#        return self.connection.execute(self.__queries['utimens'],
#            {"access":access, "modification":modification, "inode":inode})


    def Free_Chunks(self, chunk):
        """Free chunks whose offset is greather that new file size"""
        return self.connection.execute(self.__queries['Free_Chunks'], chunk)


    def Get_FreeSpace(self):
        """Get the free space available in the filesystem"""
        result = self.connection.execute(self.__queries['Get_FreeSpace']).fetchone()
        if result:
            return result['size'] * self.__sector_size
        return 0


    def __Make_DirEntry(self, type):                                          # OK
        '''
        Make a new dir entry
        and return its inode
        '''
        cursor = self.connection.cursor()
        cursor.execute(self.__queries['Direntry.make'],
                       {"type":type})

        return cursor.lastrowid


    def Put_Chunks(self, chunks):                                           # OK
        return self.connection.executemany(self.__queries['Put_Chunks'], chunks)


    def Split_Chunks(self, chunk):                                          # OK
        """
        Split the chunks in the database in two (old-head and new-tail)
        based on it's defined length
        """
        def ChunkConverted():
            """[Hack] None objects get stringed to 'None' while SQLite queries
            expect 'NULL' instead. This function return a newly dict with
            all None objects converted to 'NULL' valued strings.
            """
            d = {}
            for key, value in chunk.iteritems():
                d[key] = "NULL" if value == None else value
            return d

        # Create new chunks containing the tail sectors and
        # update the old chunks length to contain only the head sectors
        sql = self.__queries['Split_Chunks'] % ChunkConverted()
        self.connection.executescript(sql)


    def __Create_Database(self, num_sectors, first_sector=0):               # OK
        with self.connection:
            self.connection.executescript(self.__queries['__Create_Database_1'])

#            sql = (self.__queries['__Create_Database_2']
#                   % {"type":stat.S_IFDIR})
#            self.connection.executescript(sql)

            # If directories table is empty (table has just been created)
            # create initial row defining the root directory
            if not self.connection.execute('SELECT * FROM dir_entries LIMIT 1').fetchone():
                sql = (self.__queries['__Create_Database_2']
                       % {"type":stat.S_IFDIR})
                self.connection.executescript(sql)

            self.connection.execute(self.__queries['__Create_Database_3'],
                                    {"length":num_sectors,
                                     "sector":first_sector})

#            # If chunks table is empty (table has just been created)
#            # create initial row defining all the partition as free
#            if not self.connection.execute('SELECT * FROM chunks LIMIT 1').fetchone():
#    #            self.connection.execute("PRAGMA foreign_keys = OFF")
#                self.connection.execute(self.__queries['__Create_Database_3'],
#                                        {"length":num_sectors,
#                                         "sector":first_sector})
#    #            self.connection.execute("PRAGMA foreign_keys = ON")


    def __LoadQueries(self, dirPath):
        result = {}

        for filename in listdir(dirPath):
            with open(join(dirPath, filename)) as f:
                result[splitext(filename)[0]] = f.read()

        return result