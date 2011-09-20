'''
Created on 14/08/2010

@author: piranna
'''

import os
import stat

from fs.errors import DestinationExistsError
from fs.errors import ResourceInvalidError, ResourceNotFoundError
from fs.errors import StorageSpaceError

import plugins

from ..DB import ChunkConverted
from ..File import BaseFile, readable, writeable


class File(BaseFile):
    '''
    classdocs
    '''
    def __init__(self, fs, path):
        """Constructor

        @raise ParentDirectoryMissingError:
        @raise ResourceNotFoundError:
        @raise ResourceInvalidError:
        """
        BaseFile.__init__(self, fs, path)

        # File mode
        self._mode = frozenset()


    def make(self):
        # Check if dir_entry
        if self._inode:
            raise DestinationExistsError(self.path)

        # Make file
        self._make()


    def open(self, mode="r", **kwargs):
        self._CalcMode(mode)

        return self


    def truncate(self, size=0):
        size += self._offset

        if size < 0:
            raise ResourceInvalidError(msg="truncate under zero")

        self._truncate(size)


    @writeable
    def write(self, data):
        if not data: return

        # Initialize vars here to minimize database acess isolation
        data_size = len(data)
        file_size = self._offset + data_size
        floor, ceil = self._Calc_Bounds(data_size)
        sectors_required = ceil - floor

### DB ###
        # Get written chunks of the file
        chunks = self._Get_Chunks(floor, ceil)

        # Check if there's enought free space available
        for chunk in chunks:
            # Discard chunks already in file from required space
            if chunk.sector != None:
                sectors_required -= chunk.length + 1

        # Raise error if there's not enought free space available
        if sectors_required > self.fs.FreeSpace() // self.ll.sector_size:
            raise StorageSpaceError

#        print "sectors_required", sectors_required
#        print "chunks antes", chunks
### DB ###

        # If there is an offset in the first sector
        # adapt data chunks
        offset = self._offset % self.ll.sector_size
        if offset:
            sector = chunks[0]['sector']
#            print "sector:", sector, chunks

            # If first sector was not written before
            # fill space with zeroes
            if sector == None:
                sector = '\0' * offset

            # Else get it's current value as base for new data
            else:
                sector = self.ll.Read([{"sector":sector, "length":0}])
                sector = sector[:offset]

            # Adapt data
            data = sector + data
#            print "data:", repr(data)

### DB ###
        # Fill holes between written chunks (if any)
        for chunk in chunks:
#            print "chunks durante", chunks
            if chunk.sector == None:
                index = chunks.index(chunk)
                block = chunk.block

                while chunk.length >= 0:
                    # Get the free chunk that best fit the hole

                    free = self.db.Get_FreeChunk_BestFit(sectors_required=chunk.length,
                            blocks=','.join([str(chunk.block) for chunk in chunks]))

                    # If free chunk is bigger that hole, split it
                    if free.length > chunk.length:
                        free.length = chunk.length
                        self.db.Split_Chunks(**ChunkConverted(free))

                    # Adapt free chunk
                    free.file = self._inode
                    free.block = block

                    # Add free chunk to the hole
                    chunks.insert(index, free)
                    index += 1

                    # Increase block number for the next free chunk in the hole
                    # and decrease length of hole
                    block += free.length + 1
                    chunk.length -= free.length + 1

                # Remove hole chunk since we have filled it
                chunks.pop(index)

        # Put chunks in database
#        print "chunks despues", chunks
        self.db.Put_Chunks(chunks)

        # Set new file size if neccesary
        if self.db.Get_Size(inode=self._inode) < file_size:
            self._Set_Size(file_size)
### DB ###

        # Write chunks data to the drive
        for chunk in chunks:
            offset = (chunk.block - floor) * self.ll.sector_size
            self.ll.Write_Chunk(chunk.sector,
                data[offset:offset + (chunk.length + 1) * self.ll.sector_size])

        # Set new offset
        self._offset = file_size