'''
Created on 04/08/2010

@author: piranna
'''

import stat

from os      import listdir
from os.path import join, splitext

from sqlparse import split2
from sqlparse.filters import Tokens2Unicode

from sql2 import Compact, GetColumns, GetLimit, IsType


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


def ChunkConverted(chunk):
    """[Hack] None objects get converted to 'None' while SQLite queries
    expect 'NULL' instead. This function return a newly dict with
    all None objects converted to 'NULL' valued strings.
    """
    d = {}
    for key, value in chunk.iteritems():
        d[key] = "NULL" if value == None else value
    return d


class DB():
    '''
    classdocs
    '''
    def _parseFunctions(self, dirPath):
        import re

        def S2SF(sql):
            "Convert from SQLite escape query format to Python string format"
            return re.sub(":\w+", lambda m: "%%(%s)s" % m.group(0)[1:], sql)

        for filename in listdir(dirPath):
            methodName = splitext(filename)[0]

            with open(join(dirPath, filename)) as f:
                stream = Compact(f.read(), dirPath)

            # Insert statement (last row id)
            if IsType('INSERT')(stream):
                stmts = split2(stream)

                if len(stmts) == 1:
                    def applyMethod(sql, methodName):
                        def method(self, **kwargs):
                            cursor = self.connection.cursor()
                            cursor.execute(sql, kwargs)
                            return cursor.lastrowid

                        setattr(self.__class__, methodName, method)

                    applyMethod(unicode(stmts[0]), methodName)

                else:
                    def applyMethod(stmts, methodName):
                        def method(self, **kwargs):
                            cursor = self.connection.cursor()
                            cursor.execute(stmts[0] % kwargs)
                            rowid = cursor.lastrowid

                            for stmt in stmts[1:]:
                                cursor.execute(stmt % kwargs)

                            return rowid

                        setattr(self.__class__, methodName, method)

                    applyMethod([S2SF(unicode(x)) for x in stmts], methodName)

            # One statement query
            elif len(split2(stream)) == 1:
                # One-value function
                if GetLimit(stream) == 1:
                    columns = GetColumns(stream)

                    # Value function
                    if len(columns) == 1 and columns[0] != '*':
                        def applyMethod(sql, methodName, column):
                            def method(self, **kwargs):
                                result = self.connection.execute(sql, kwargs)
                                result = result.fetchone()
                                if result:
                                    return result[column]

                            setattr(self.__class__, methodName, method)

                        applyMethod(Tokens2Unicode(stream), methodName, columns[0])

                    # Register function
                    else:
                        def applyMethod(sql, methodName):
                            def method(self, **kwargs):
                                result = self.connection.execute(sql, kwargs)
                                return result.fetchone()

                            setattr(self.__class__, methodName, method)

                        applyMethod(Tokens2Unicode(stream), methodName)

                # Table function
                else:
                    def applyMethod(sql, methodName):
                        def method(self, **kwargs):
                            result = self.connection.execute(sql, kwargs)
                            return result.fetchall()

                        setattr(self.__class__, methodName, method)

                    applyMethod(Tokens2Unicode(stream), methodName)

            # Multiple statement query
            else:
                def applyMethod(sql, methodName):
                    def method(self, **kwargs):
                        self.connection.executescript(sql % kwargs)

                    setattr(self.__class__, methodName, method)

                applyMethod(S2SF(Tokens2Unicode(stream)), methodName)


    def __init__(self, db_conn, sql_dir, drive, sector_size):                     # OK
        '''
        Constructor
        '''
        self.connection = db_conn
        self.connect()

        def Get_NumSectors():
            # http://stackoverflow.com/questions/283707/size-of-an-open-file-object
            drive.seek(0, 2)
            end = drive.tell()
            drive.seek(0)
            return (end - 1) // sector_size

        self._parseFunctions(sql_dir)

        self.create(type=stat.S_IFDIR, length=Get_NumSectors(), sector=0)

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


    def Put_Chunks(self, chunks):                                           # OK
        return self.connection.executemany(
             """UPDATE chunks
                SET file = :file, block = :block
                WHERE sector=:sector
                -- WHERE drive=:drive AND sector=:sector""",
            chunks)
#        return self.connection.executemany(self.__queries['Put_Chunks'], chunks)