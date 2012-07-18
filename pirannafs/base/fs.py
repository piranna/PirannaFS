'''
Created on 09/04/2012

@author: piranna
'''

from os.path import abspath, dirname, join
from sqlite3 import connect

from antiorm.backends.sqlite import Sqlite
from antiorm.utils           import namedtuple_factory

from plugins import send


def initDB(db_file, db_dirPath):
    #
    # Database

#    db_conn = connect(db_file)
    db_conn = connect(db_file, check_same_thread=False)

    db_conn.row_factory = namedtuple_factory
#    db_conn.isolation_level = None

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

    return Sqlite(db_conn, db_dirPath, False, True)


class FS(object):
    '''
    classdocs
    '''

    def __init__(self, db_file, db_dirPath=None):
        if not db_dirPath:
            db_dirPath = join(dirname(abspath(__file__)), '..', 'sql')
        self.db = initDB(db_file, db_dirPath)

        self.db.create()

    @property
    def freespace(self):
        freespace = 0
        for _, space in send('FS.freespace'):
            freespace += space
        return freespace
