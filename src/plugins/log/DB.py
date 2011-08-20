'''
Created on 20/08/2011

@author: piranna
'''

from os      import listdir
from os.path import dirname, join, splitext

import sqlite3

from sqlparse import split2
from sqlparse.filters import Tokens2Unicode

from sql2 import Compact, GetColumns, GetLimit, IsType


class DB:
    '''
    classdocs
    '''


    def _parseFunctions(self, dirPath):
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
                            cursor.execute(unicode(stmts[0]) % kwargs)
                            rowid = cursor.lastrowid

                            for stmt in stmts[1:]:
                                cursor.execute(unicode(stmt) % kwargs)

                            return rowid

                        setattr(self.__class__, methodName, method)

                    applyMethod(stmts, methodName)

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

                applyMethod(Tokens2Unicode(stream), methodName)


    def __init__(self, core):
        '''
        Constructor
        '''
        # Database files
        self.connection = sqlite3.connect('../../../log.sqlite')
        self.connection.execute('ATTACH DATABASE :core AS core', {'core': core})

        self.connection.isolation_level = None

        # SQLite tune-ups
        self.connection.execute("PRAGMA synchronous = OFF;")
        self.connection.execute("PRAGMA temp_store = MEMORY;")  # Not so much

        # Force enable foreign keys check
        self.connection.execute("PRAGMA foreign_keys = ON;")

        self._parseFunctions(join(dirname(__file__), 'sql'))

        self.create()