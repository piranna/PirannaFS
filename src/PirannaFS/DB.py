'''
Created on 04/08/2010

@author: piranna
'''

import stat
import sys

from multiprocessing import Lock


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

    def __init__(self, connection, drive, sector_size):                         # OK
        '''
        Constructor
        '''
        self.connection = connection

        self.connection.row_factory = DictObj_factory
        self.connection.isolation_level = None

        self.connection.execute("PRAGMA foreign_keys = ON;")

        self._lock = Lock()

        def Get_NumSectors():
            # http://stackoverflow.com/questions/283707/size-of-an-open-file-object
            drive.seek(0, 2)
            end = drive.tell()
            drive.seek(0)
            return (end - 1) // sector_size

        self.__sector_size = sector_size

        self.__Create_Database(Get_NumSectors())


    # Python-FUSE
    def getattr(self, parent_dir, name):                                        # OK
        '''
        Get the stat info of a directory entry
        '''
#        print >> sys.stderr, '*** DB.getattr', parent_dir,name

        with self._lock:
            inodeCreation = self.__Get_InodeCreation(parent_dir, name)
            if inodeCreation:
                return self.connection.execute('''
                    SELECT
                        0 AS st_dev,
                        0 AS st_uid,
                        0 AS st_gid,

                        dir_entries.type         AS st_mode,
                        dir_entries.inode        AS st_ino,
                        COUNT(links.child_entry) AS st_nlink,

                        :creation                                                AS st_ctime,
                        CAST(STRFTIME('%s',dir_entries.access) AS INTEGER)       AS st_atime,
                        CAST(STRFTIME('%s',dir_entries.modification) AS INTEGER) AS st_mtime,

                        COALESCE(files.size,0) AS st_size

                    FROM dir_entries
                        LEFT JOIN files
                            ON dir_entries.inode == files.inode
                        LEFT JOIN links
                            ON dir_entries.inode == links.child_entry

                    WHERE dir_entries.inode == :inode

                    GROUP BY dir_entries.inode
                    LIMIT 1
                    ''',
                    inodeCreation).fetchone()

    # PyFilesystem
    def getinfo(self, parent_dir, name):                                        # OK
        '''
        Get the stat info of a directory entry
        '''
#        print >> sys.stderr, '*** DB.getattr', parent_dir,name

        with self._lock:
            inodeCreation = self.__Get_InodeCreation(parent_dir, name)
            if inodeCreation:
                return self.connection.execute('''
                    SELECT
                        0 AS st_dev,
                        0 AS st_uid,
                        0 AS st_gid,

                        dir_entries.type         AS st_mode,
                        dir_entries.inode        AS st_ino,
                        COUNT(links.child_entry) AS st_nlink,

                        :creation                                                AS st_ctime,
                        CAST(STRFTIME('%s',dir_entries.access) AS INTEGER)       AS st_atime,
                        CAST(STRFTIME('%s',dir_entries.modification) AS INTEGER) AS st_mtime,

                        COALESCE(files.size,0) AS size

                    FROM dir_entries
                        LEFT JOIN files
                            ON dir_entries.inode == files.inode
                        LEFT JOIN links
                            ON dir_entries.inode == links.child_entry

                    WHERE dir_entries.inode == :inode

                    GROUP BY dir_entries.inode
                    LIMIT 1
                    ''',
                    inodeCreation).fetchone()


    def link(self, parent_dir_inode, name, child_entry_inode):                  # OK
#        print >> sys.stderr, '*** link', parent_dir_inode,name,child_entry_inode

        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO links(parent_dir,name,child_entry)
            VALUES(?,?,?)
            ''',
            (parent_dir_inode, name, child_entry_inode))

        return cursor.lastrowid


    def mkdir(self):                                                            # OK
        '''
        Make a new directory
        '''
        with self._lock:
            inode = self.Make_DirEntry(stat.S_IFDIR)
            self.connection.execute('''
                INSERT INTO directories(inode)
                VALUES(?)
                ''',
                (inode,))

        return inode


    def mknod(self):                                                            # OK
        '''
        Make a new file
        '''
        with self._lock:
            inode = self.Make_DirEntry(stat.S_IFREG)
            self.connection.execute('''
                INSERT INTO files(inode)
                VALUES(?)
                ''',
                (inode,))

        return inode


    def readdir(self, parent, limit=None):                                                  # OK
        sql = '''
            SELECT name FROM links
            WHERE parent_dir = ?
            '''
        if limit:
            sql += "LIMIT %" % limit

        return self.connection.execute(sql, (parent,)).fetchall()


    def rename(self, parent_old, name_old, parent_new, name_new):               # OK
        return self.connection.execute('''
            UPDATE links
            SET parent_dir = ?, name = ?
            WHERE parent_dir = ? AND name = ?
            ''',
            (parent_new, name_new,
             parent_old, name_old))


    def unlink(self, parent_dir_inode, name):                                   # OK
#        print >> sys.stderr, '\t', parent_dir_inode,name
        return self.connection.execute('''
            DELETE FROM links
            WHERE parent_dir = ? AND name = ?
            ''',
            (parent_dir_inode, name))


    def utimens(self, inode, ts_acc, ts_mod):
        if ts_acc == None:  ts_acc = "now"
        if ts_mod == None:  ts_mod = "now"

        return self.connection.execute('''
            UPDATE dir_entries
            SET access = ?, modification = ?
            WHERE inode = ?
            ''',
            (ts_acc, ts_mod, inode))


    def Free_Chunks(self, chunk):
        """Free chunks whose offset is greather that new file size"""
        print >> sys.stderr, '*** Free_Chunks', chunk

        return self.connection.execute('''
            UPDATE chunks
            SET file = NULL, block = 0
            WHERE file = :file AND block > :block + :length
            ''',
            chunk)


    def Get_Chunks(self, file, floor, ceil):                                    # OK
        '''
        Get chunks of the required file that are content between the
        defined floor and ceil
        '''
        return self.connection.execute('''
            SELECT * FROM chunks
            WHERE file = ?
              AND block BETWEEN ? AND ?-length
            GROUP BY file,block
            ORDER BY block
            ''',
            (file, floor, ceil)).fetchall()


    def Get_Chunks_Truncate(self, file, ceil):
        """
        Get chunks whose block+length is greather that new file size
        """
        return self.connection.execute('''
            SELECT file, block, ?-block AS length
            FROM chunks
            WHERE file IS ?
              AND block+length > ?
            ''',
            (ceil, file, ceil))


    def Get_FreeChunk_BestFit(self, sectors_required, blocks):                  # OK
        '''Get the free chunk that best fit to the requested space.

        'Best fit' here means that it's the smallest free chunk whose size is
        equals-or-bigger or it's the biggest one that is smaller
        that the requested size
        '''
        return self.connection.execute('''
            SELECT * FROM chunks
            WHERE file IS NULL
--                AND block NOT IN (:blocks)
                AND length <= COALESCE
                              (
                                  (
                                      SELECT length FROM chunks
                                      WHERE file IS NULL
--                                          AND block NOT IN (:blocks)
                                          AND length >= :sectors_required
                                      ORDER BY length
                                      LIMIT 1
                                  ),
                                  :sectors_required
                              )
            ORDER BY length DESC
            LIMIT 1
            ''',
            {"blocks":','.join([str(block) for block in blocks]),
             "sectors_required":sectors_required}).fetchone()


    def Get_FreeSpace(self):
        """Get the free space available in the filesystem"""
        return self.connection.execute('''
            SELECT SUM(length+1) AS size
            FROM chunks
            WHERE file IS NULL
            ''').fetchone()['size'] * self.__sector_size


    def Get_Inode(self, parent_dir, name):                                      # OK
        '''
        Get the inode of a dir entry
        from a given parent directory inode and a dir entry name
        '''
        inode = self.__Get_InodeCreation(parent_dir, name)
        if inode:
            return inode['inode']


    def Get_Mode(self, inode):                                                  # OK
        '''
        Get the mode of a file
        from a given file inode
        '''
        inode = self.connection.execute('''
            SELECT type
            FROM dir_entries
            WHERE inode == ?
            LIMIT 1
            ''',
            (inode,)).fetchone()

        if inode:
            return inode['type']


    def Get_Size(self, inode):                                                  # OK
        '''
        Get the size of a file
        from a given file inode
        '''
        inode = self.connection.execute('''
            SELECT size
            FROM files
            WHERE inode == ?
            LIMIT 1
            ''',
            (inode,)).fetchone()

        if inode:
            return inode['size']


    def Make_DirEntry(self, type):                                              # OK
        '''
        Make a new dir entry
        and return its inode
        '''
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO dir_entries(type)
            VALUES(?)
            ''',
            (type,))

        return cursor.lastrowid


    def Put_Chunks(self, chunks):                                               # OK
        return self.connection.executemany('''
            UPDATE chunks
            SET file  = :file,
                block = :block
            WHERE sector=:sector
--            WHERE drive=:drive AND sector=:sector
            ''',
            chunks)


    def Set_Size(self, inode, length):                                          # OK
        return self.connection.execute('''
            UPDATE files
            SET size = ?
            WHERE inode = ?
            ''',
            (length, inode))


    def Split_Chunks(self, chunk):                                              # OK
        """
        Split the chunks in the database in two (old-head and new-tail)
        based on it's defined length
        """
        def ChunkConverted():
            d = {}
            for key, value in chunk.iteritems():
                if value == None:
                    d[key] = "NULL"
                else:
                    d[key] = value
            return d

        # Create new chunks containing the tail sectors and
        # update the old chunks length to contain only the head sectors
        self.connection.executescript('''
            INSERT INTO chunks(file, block,              length,              sector)
            SELECT             file, block+%(length)s+1, length-%(length)s-1, sector+%(length)s+1
                FROM chunks
                WHERE file IS %(file)s
                  AND block = %(block)s;

                UPDATE chunks SET length  = %(length)s
                WHERE file IS %(file)s
                  AND block = %(block)s;
            ''' % ChunkConverted())


    def __Create_Database(self, num_sectors, first_sector=0):                   # OK
        with self._lock:
            self.connection.executescript('''
                CREATE TABLE IF NOT EXISTS dir_entries
                (
                    inode        INTEGER   PRIMARY KEY,

                    type         INTEGER   NOT NULL,
                    access       timestamp DEFAULT CURRENT_TIMESTAMP,
                    modification timestamp DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS directories
                (
                    inode INTEGER PRIMARY KEY,

                    FOREIGN KEY(inode) REFERENCES dir_entries(inode)
                        ON DELETE CASCADE ON UPDATE CASCADE
                );

                CREATE TABLE IF NOT EXISTS links
                (
                    id          INTEGER   PRIMARY KEY,

                    child_entry INTEGER   NOT NULL,
                    parent_dir  INTEGER   NOT NULL,
                    name        TEXT      NOT NULL,
                    creation    timestamp DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY(child_entry) REFERENCES dir_entries(inode)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY(parent_dir) REFERENCES directories(inode)
                        ON DELETE CASCADE ON UPDATE CASCADE,

                    UNIQUE(parent_dir,name)
                );

                CREATE TABLE IF NOT EXISTS files
                (
                    inode INTEGER PRIMARY KEY,

                    size  INTEGER DEFAULT 0,

                    FOREIGN KEY(inode) REFERENCES dir_entries(inode)
                        ON DELETE CASCADE ON UPDATE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chunks
                (
                    id     INTEGER PRIMARY KEY,

                    file   INTEGER NULL,
                    block  INTEGER NOT NULL,
                    length INTEGER NOT NULL,
                    sector INTEGER NOT NULL,

                    FOREIGN KEY(file) REFERENCES files(inode)
                        ON DELETE SET NULL ON UPDATE CASCADE,

                    UNIQUE(file,block),
                    UNIQUE(file,sector)
                );

    -- Triggers

                CREATE TRIGGER IF NOT EXISTS remove_if_it_was_the_last_file_link
                AFTER DELETE ON links
                WHEN NOT EXISTS(
                    SELECT * FROM links
                    WHERE child_entry = OLD.child_entry
                    LIMIT 1
                    )
                BEGIN
                    DELETE FROM dir_entries
                    WHERE dir_entries.inode = OLD.child_entry;
                END;
    --
                CREATE TRIGGER IF NOT EXISTS after_insert_on_links
                AFTER INSERT ON links
                BEGIN
                    UPDATE dir_entries
                    SET modification = CURRENT_TIMESTAMP
                    WHERE dir_entries.inode = NEW.parent_dir;
                END;

                CREATE TRIGGER IF NOT EXISTS after_update_on_links
                AFTER UPDATE ON links
                BEGIN
                    UPDATE dir_entries
                    SET modification = CURRENT_TIMESTAMP
                    WHERE dir_entries.inode IN(OLD.parent_dir,NEW.parent_dir);
                END;

                CREATE TRIGGER IF NOT EXISTS after_delete_on_links
                AFTER DELETE ON links
                BEGIN
                    UPDATE dir_entries
                    SET modification = CURRENT_TIMESTAMP
                    WHERE dir_entries.inode = OLD.parent_dir;
                END;
                ''')

            # If directories table is empty (table has just been created)
            # create initial row defining the root directory
            if not self.connection.execute('SELECT * FROM dir_entries LIMIT 1').fetchone():
                self.connection.execute('''
                    INSERT INTO dir_entries(inode,type)
                    VALUES(0,?)
                    ''', (stat.S_IFDIR,))
                self.connection.execute('''
                    INSERT INTO directories(inode)
                    VALUES(0)
                    ''')
                self.connection.execute('''
                    INSERT INTO links(id,child_entry,parent_dir,name)
                    VALUES(0,0,0,'')
                    ''')

            # If chunks table is empty (table has just been created)
            # create initial row defining all the partition as free
            if not self.connection.execute('SELECT * FROM chunks LIMIT 1').fetchone():
    #            self.connection.execute("PRAGMA foreign_keys = OFF")
                self.connection.execute('''
                    INSERT INTO chunks(file,block,length,sector)
                    VALUES(NULL,0,?,?)
                    ''',
                    (num_sectors, first_sector))
    #            self.connection.execute("PRAGMA foreign_keys = ON")


    def __Get_InodeCreation(self, parent_dir, name):                             # OK
        '''
        Get the inode and the creation date of a dir entry
        from a given parent directory inode and a dir entry name
        '''
        return self.connection.execute('''
            SELECT
                child_entry                              AS inode,
                CAST(STRFTIME('%s',creation) AS INTEGER) AS creation
            FROM links
            WHERE parent_dir == ?
                AND name == ?
            LIMIT 1
            ''',
            (parent_dir, unicode(name))).fetchone()