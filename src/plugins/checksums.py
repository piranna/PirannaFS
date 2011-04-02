'''
Created on 26/09/2010

@author: piranna
'''

import sys

import zlib

import plugins



class checksums(plugins.Plugin):
    def __init__(self):
        plugins.connect(self.__Create, "FS.__init__")

        # Create
        plugins.connect(self.__Write, "File.write")

        # Update
        plugins.connect(self.__Split_Chunks, "File.__Split_Chunks")


    def __initialize(self, db, ll):
        '''
        Create the checksums table in the database
        '''
#        print >> sys.stderr, '*** create', db

        self.__db = db
        self.__ll = ll

        self.__db.connection.execute('''
            CREATE TABLE IF NOT EXISTS checksums
            (
                chunk    INTEGER PRIMARY KEY,

                checksum INTEGER NOT NULL,

                FOREIGN KEY(chunk) REFERENCES chunks(id)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )

-- Triggers

            CREATE TRIGGER IF NOT EXISTS remove_if_chunk_have_been_freed
            AFTER UPDATE ON chunks
            WHEN NEW.file IS NULL
            BEGIN
                DELETE FROM checksums
                WHERE checksums.chunk = OLD.id;
            END;
        ''')


    def __Split_Chunks(self, chunk):
        for chunk in self.__db.Get_Chunks(chunk['file'], chunk['block'],
                                          chunk['block'] + chunk['length'] + 1):
            self.__Write(chunk['id'], self.__ll.Read_Chunk(chunk))


    def __Write(self, chunk, data):
        '''
        Calculate the checksum of the data and link it's value to the chunk.
        If the checksum exist previously (for example, a truncate or a split
        chunks have been done) the checksum is replaced.
        '''
        print >> sys.stderr, '*** checksum', chunk, data

        return self.__db.connection.execute('''
            REPLACE INTO checksums(chunk,checksum)
            VALUES(?,?)
            ''',
            (chunk, zlib.crc32(data)))