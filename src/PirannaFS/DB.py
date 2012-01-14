'''
Created on 04/08/2010

@author: piranna
'''

from os      import listdir
from os.path import join, splitext
from stat    import S_IFDIR

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

            # Insert statement (return last row id)
            if IsType('INSERT')(stream):
                stmts = split2(stream)

                # One statement query
                if len(stmts) == 1:
                    def applyMethod(sql, methodName):
                        def method(self, **kwargs):
                            cursor = self.connection.cursor()
                            cursor.execute(sql, kwargs)
                            return cursor.lastrowid

                        setattr(self.__class__, methodName, method)

                    applyMethod(unicode(stmts[0]), methodName)

                # Multiple statement query (return last row id of first one)
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

                    # Value function (one register, one field)
                    if len(columns) == 1 and columns[0] != '*':
                        def applyMethod(sql, methodName, column):
                            def method(self, **kwargs):
                                result = self.connection.execute(sql, kwargs)
                                result = result.fetchone()
                                if result:
                                    return result[column]

                            setattr(self.__class__, methodName, method)

                        applyMethod(Tokens2Unicode(stream), methodName,
                                    columns[0])

                    # Register function (one register, several fields)
                    else:
                        def applyMethod(sql, methodName):
                            def method(self, **kwargs):
                                result = self.connection.execute(sql, kwargs)
                                return result.fetchone()

                            setattr(self.__class__, methodName, method)

                        applyMethod(Tokens2Unicode(stream), methodName)

                # Table function (several registers)
                else:
                    def applyMethod(sql, methodName):
                        def method(self, _=None, **kwargs):
                            # Received un-named parameter
                            if _:
                                # Parameters are given as a dictionary,
                                # put them in the correct place (bad guy...)
                                if isinstance(_, dict):
                                    kwargs = _

                                # Iterable of parameters, use executemany()
                                else:
                                    return self.connection.executemany(sql, _)

                            # Execute single SQL statement
                            result = self.connection.execute(sql, kwargs)
                            return result.fetchall()

                        setattr(self.__class__, methodName, method)

                    applyMethod(Tokens2Unicode(stream), methodName)

            # Multiple statement query
            else:
                import sys
                if 'sqlite3' in sys.modules:
                    def applyMethod(sql, methodName):
                        def method(self, **kwargs):
                            self.connection.executescript(sql % kwargs)

                        setattr(self.__class__, methodName, method)

                    applyMethod(S2SF(Tokens2Unicode(stream)), methodName)

                else:
                    stmts = split2(stream)

                    def applyMethod(stmts, methodName):
                        def method(self, **kwargs):
                            for stmt in stmts:
                                self.connection.execute(stmt, kwargs)

                        setattr(self.__class__, methodName, method)

                    applyMethod([S2SF(unicode(x)) for x in stmts], methodName)




    def __init__(self, db_conn, sql_dir, drive, sector_size):              # OK
        '''
        Constructor
        '''
        self.connection = db_conn
        self.connect()

        # http://stackoverflow.com/questions/283707/size-of-an-open-file-object
        def Get_NumSectors():
            drive.seek(0, 2)
            end = drive.tell()
            drive.seek(0)
            return (end - 1) // sector_size

        self._parseFunctions(sql_dir)

        self.create(type=S_IFDIR, length=Get_NumSectors(), sector=0)

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
