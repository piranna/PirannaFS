'''
Created on 12/08/2010

@author: piranna
'''

import errno



def write(self, path,data,offset):
    size = len(buffer)
    floor = offset//self.__sector_size
    ceil = (offset+size)//self.__sector_size

    # Get free space
    chunks,sectors_required = self.__Get_FreeSpace(1 + ceil-floor)

    # Get recicled sectors (if neccesary)
    if sectors_required > 0:
        chunks_recicled = []
        timestamp = None

        for chunk in self.__db.Get_Recicled():
            chunks_recicled.append(chunk)

            if timestamp:
                if chunk['timestamp'] > timestamp:
                    break
            else:
                sectors_required -= chunk.length
                if sectors_required <= 0:
                    timestamp = chunk['timestamp']

        if sectors_required > 0:
            return -errno.ENOSPC

        else:
            self.__db.Free_Recicled(chunks_recicled)
            chunks.extend(chunks_recicled)
            chunks.sort(key=lambda chunk: str(chunk.drive)+":"+str(chunk.sector))
            if self.__Compact_FreeSpace(chunks):
                chunks = self.__Get_FreeSpace(1 + ceil-floor)

    # Adapt data chunks
    block = LL.Read([{"sector":,"length":1}])
    data = block[:offset-(floor*self.__sector_size)] + data

    data += '0'*(offset+size - ceil*self.__sector_size)

    # Prepare chunks
    chunks_write = []

    file =
    timestamp = 

    for chunk in chunks:
        block = chunk.block
        length = 0

        for sector in range(0:chunk['length']):
            if iguales:
                if length:
                    if sector < chunk['length']-1:
                        self.__db.Split_Chunks(file,chunk.block,length)

                    chunks_write.append((file,block,length,timestamp,
                                         chunk['drive'],chunk['sector']))
                    block += length
                    length = 0

            else:
                length += 1

        if length:
            chunks_write.append((file,block,length,timestamp,
                                 chunk['drive'],chunk['sector']))

    # Write chunks
    LL.Write(chunks_write,data)
    self.__db.Put_Chunks(chunks_write)

    # Return size of the written data
    return size

    
    return self.__db.write(self.Get_Inode(path),data,offset)





    def Compact_FreeSpace(self, chunk1,chunk2):
        return self.__connection.execute('''
            UPDATE chunks(length,timestamp)
            SET(length+?,CURRENT_TIMESTAMP)
            WHERE drive = ?
                AND sector = ?;

            DELETE FROM chunks
            WHERE drive = ?
                AND sector = ?;
            ''',
            (chunk2.length,
             chunk1.drive,chunk1.sector,
             chunk2.drive,chunk2.sector))


    def Get_Recicled(self):
        '''
        Get the free space chunk that best fit to the requested space
        '''
        return self.__connection.execute('''
            SELECT drive,sector,length FROM chunks
            WHERE file > 0
                AND timestamp < MAX(timestamp)
            GROUP BY file,block
            SORT BY timestamp
            ''')


    def Free_Recicled(self, chunks):
        '''
        Free chunks
        '''
        return self.__connection.executemany('''
            UPDATE chunks(file,block,timestamp)
            SET(NULL,0,CURRENT_TIMESTAMP)
            WHERE drive = :drive
                AND sector = :sector
            ''',
            chunks)


    def Put_Chunks(self, chunks):
        return self.__connection.executemany('''
            INSERT INTO chunks
            VALUES(?)
            ''',
            chunks)




    def __Compact_FreeSpace(self, chunks):
        compacted = False

        if len(chunks) > 1:
            chunk1 = chunks[0]

            for chunk2 in chunks[1:]:
                if chunk1.sector+chunk1.length = chunk2.sector:
                    self.__db.Compact_FreeSpace(chunk1,chunk2)
                    chunk1.length += chunk2.length

                    compacted = True

                else:
                    chunk1 = chunk2

        return compacted