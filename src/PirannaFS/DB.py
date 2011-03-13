'''
Created on 04/08/2010

@author: piranna
'''

import stat
import sys

import sqlite3



def DictObj_factory(cursor, row):
    class DictObj(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)

    d = DictObj()
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DB():
    '''
    classdocs
    '''

    def __init__(self, db_name):                                                # OK
        '''
        Constructor
        '''
        self.connection = sqlite3.connect(db_name)

        self.connection.row_factory = DictObj_factory
#        self.connection.row_factory = sqlite3.Row
        self.connection.isolation_level = None

        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.__Create_Database()


    def getattr(self, parent_dir,name):                                         # OK
        '''
        Get the stat info of a directory entry
        '''
#        print >> sys.stderr, '*** DB.getattr', parent_dir,name

        inodeCreation = self.__Get_InodeCreation(parent_dir,name)
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


    def link(self, parent_dir_inode,name,child_entry_inode):                    # OK
#        print >> sys.stderr, '*** link', parent_dir_inode,name,child_entry_inode

        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO links(parent_dir,name,child_entry)
            VALUES(?,?,?)
            ''',
            (parent_dir_inode,name,child_entry_inode))

        return cursor.lastrowid


    def mkdir(self):                                                            # OK
        '''
        Make a new directory
        '''
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
        inode = self.Make_DirEntry(stat.S_IFREG)
        self.connection.execute('''
            INSERT INTO files(inode)
            VALUES(?)
            ''',
            (inode,))

        return inode


    def readdir(self, parent):                                                  # OK
        return self.connection.execute('''
            SELECT name FROM links
            WHERE parent_dir = ?
            ''',
            (parent,)).fetchall()


    def rename(self, parent_old,name_old, parent_new,name_new):                 # OK
        return self.connection.execute('''
            UPDATE links
            SET parent_dir = ?, name = ?
            WHERE parent_dir = ? AND name = ?
            ''',
            (parent_new,name_new,
             parent_old,name_old))


    def unlink(self, parent_dir_inode,name):                                    # OK
#        print >> sys.stderr, '\t', parent_dir_inode,name
        return self.connection.execute('''
            DELETE FROM links
            WHERE parent_dir = ? AND name = ?
            ''',
            (parent_dir_inode,name))


    def utimens(self, inode, ts_acc,ts_mod):
        if ts_acc == None:  ts_acc = "now"
        if ts_mod == None:  ts_mod = "now"

        return self.connection.execute('''
            UPDATE dir_entries
            SET access = ?, modification = ?
            WHERE inode = ?
            ''',
            (ts_acc,ts_mod, inode))


    def Free_Chunks(self, chunk):
        print >> sys.stderr, '*** Free_Chunks',chunk

        # Free chunks whose offset is greather that new file size
        return self.connection.execute('''
            UPDATE chunks
            SET file = NULL, block = 0
            WHERE file = :file AND block >= :block+:length
            ''',
            chunk)


    def Get_Chunks(self, file,floor,ceil):                                      # OK
        '''
        Get chunks of the required file that are content between the
        defined floor and ceil
        '''
        return self.connection.execute('''
            SELECT * FROM chunks
            WHERE file = ?
              AND block BETWEEN ? AND ?-length+1
            GROUP BY file,block
            ORDER BY block
            ''',
            (file,floor,ceil)).fetchall()


    def Get_Chunks_Truncate(self, file,ceil):
        """
        Get chunks whose offset+length is greather that new file size
        """
        print >> sys.stderr, '*** Get_Chunks_Truncate',chunk

        return cursor.execute('''
            SELECT file, block, ?-block AS length
            FROM chunks
            WHERE file IS ?
              AND block+length > ?
            ''',
            (ceil,file,ceil))


    def Get_FreeSpace(self, sectors_required,chunks):                           # OK
        '''
        Get the free space chunk that best fit to the requested space
        or is the biggest space available and has not been get before
        '''
        return self.connection.execute('''
            SELECT * FROM chunks
            WHERE file IS NULL
                AND length <= COALESCE
                              (
                                  (
                                      SELECT length FROM chunks
                                      WHERE file IS NULL
                                          AND length >= ?
--                                          AND NOT IN ()
                                      ORDER BY length
                                      LIMIT 1
                                  ),
                                  ?
                              )
--                AND NOT IN ()
            ORDER BY length DESC
            LIMIT 1
            ''',
            (sectors_required,sectors_required)).fetchone()


    def Get_Inode(self, parent_dir,name):                                       # OK
        '''
        Get the inode of a dir entry
        from a given parent directory inode and a dir entry name
        '''
        inode = self.__Get_InodeCreation(parent_dir,name)
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

        return None


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

        return None


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


    def Set_Size(self, inode,length):                                           # OK
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
        if chunk['length'] > 0:
            cursor = self.connection.cursor()

            # Create new chunks containing the tail sectors
            cursor.execute('''
                INSERT INTO chunks(file, block,         length,         sector)
                SELECT             file, block+:length, length-:length, sector+:length
                    FROM chunks
                    WHERE file IS :file
                      AND block = :block
                ''',
                chunk)

            if cursor.rowcount > 0:
                # Update the old chunks length to contain only the head sectors
                cursor.execute('''
                    UPDATE chunks
                    SET length = :length
                    WHERE file IS :file
                      AND block = :block
                    ''',
                    chunk)

                return True


    def __Create_Database(self):                                                # OK
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
                    ON DELETE CASCADE ON UPDATE CASCADE
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
                    ON DELETE SET NULL ON UPDATE CASCADE
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
                INSERT INTO dir_entries(inode)
                VALUES(0)
                ''')
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
                (2048,0))
#            self.connection.execute("PRAGMA foreign_keys = ON")


    def __Get_InodeCreation(self, parent_dir,name):                             # OK
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
            (parent_dir,str(name))).fetchone()