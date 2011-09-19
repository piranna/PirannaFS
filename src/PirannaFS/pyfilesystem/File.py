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
        """

        @raise ParentDirectoryMissingError:
        @raise ResourceNotFoundError:
        @raise ResourceInvalidError:
        """
        # Get file inode or raise exception
        try:
            self._inode = fs.Get_Inode(path)
        except ResourceNotFoundError:
            self._inode = None
        else:
            # If inode is a dir, raise error
            if fs.db.Get_Mode(inode=self._inode) == stat.S_IFDIR:
                raise ResourceInvalidError(path)

        # Init base class
        BaseFile.__init__(self, fs, path)

        self._mode = frozenset()

    def __del__(self):
        self.close()


    def close(self):
        self.flush()
#        self._mode = frozenset()

        plugins.send("File.close")

    def flush(self):
        pass
#        self.ll._file.flush()


    def make(self):
        # Check if dir_entry
        if self._inode:
            raise DestinationExistsError(self.path)

        # Make file
        self._inode = self.db.mknod(type=stat.S_IFREG)
        self.db.link(parent_dir=self.parent, name=self.name,
                     child_entry=self._inode)

    def next(self):
        data = self.readline()
        if data:
            return data
        raise StopIteration


    def open(self, mode="r", **kwargs):
        def CalcMode():
            # Based on code from filelike.py

            # Set `self._mode` as a set so we can modify it.
            # Needed to truncate the file while processing the mode
            self._mode = set()

            # Calc the mode and perform the corresponding initialization actions
            if 'r' in mode:
                # Action
                if self._inode == None:
                    raise ResourceNotFoundError(self.path)

                # Set mode
                self._mode.add('r')
                if '+' in mode:

                    self._mode.add('w')

            elif 'w' in mode:
                # Set mode
                self._mode.add('w')
                if '+' in mode:
                    self._mode.add('r')

                # Action
#                print "inode", inode
                if self._inode == None:
                    self.make()
                else:
                    self.truncate()

            elif 'a' in mode:
                # Action
                if self._inode == None:
                    self.make()
                else:
                    self.seek(0, os.SEEK_END)

                # Set mode
                self._mode.add('w')
                self._mode.add('a')
                if '+' in mode:
                    self._mode.add('r')

            # Re-set `self._mode` as an inmutable frozenset.
            self._mode = frozenset(self._mode)

        CalcMode()

        return self


    @readable
    def read(self, size= -1):
        """
        """
#        print >> sys.stderr, '*** read', length

        plugins.send("File.read begin")
        data = self._read(size)
        plugins.send("File.read end")
        return data

    @readable
    def readline(self, size= -1):
        """
        """
        plugins.send("File.readline begin")

        # Adjust read size
        remanent = self.db.Get_Size(inode=self._inode) - self._offset
        if 0 <= size < remanent:
            remanent = size

        # Calc floor required
        floor = self._offset // self.ll.sector_size

        block = floor
        readed = ""

        while remanent > 0:
            # Read chunk
            chunks = self._Get_Chunks(block)
            data = self.ll.Read(chunks)

            # Check if we have get end of line
            try:
                index = data.index('\n') + 1

            except ValueError:
                # Calc next block required
                readed += data
                block += chunks[0].length + 1
                remanent -= len(data)

            else:
                readed += data[:index]
                break

        # Set read query offset and cursor
        offset = self._offset - floor * self.ll.sector_size
        self._offset += len(readed)

        plugins.send("File.readline end")

        return readed[offset:self._offset]

    @readable
    def readlines(self, sizehint= -1):
        """
        """
        plugins.send("File.readlines begin")
        data = self._read(sizehint).splitlines(True)
        plugins.send("File.readlines end")
        return data

    def seek(self, offset, whence=os.SEEK_SET):
        """
        """
#        print >> sys.stderr, '*** read', length,offset

        plugins.send("File.seeking")

        # Set whence
        if   whence == os.SEEK_SET: whence = 0
        elif whence == os.SEEK_CUR: whence = self._offset
        elif whence == os.SEEK_END: whence = self.db.Get_Size(inode=self._inode)
        else:                       raise ResourceInvalidError(self.__path)

        # Readjust offset
        self._offset = whence + offset

        plugins.send("File.seeked")

    def tell(self):
        """Return the current cursor position offset

        @return: integer
        """
        return self._offset


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

        plugins.send("File.write", chunks=chunks, data=data)

    @writeable
    def writelines(self, sequence):
        data = ""
        for line in sequence:
            data += line
        self.write(data)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __iter__(self):
        return self


#    def __str__(self):
#        return "<File in %s %s>" % (self.__fs, self.path)
#
#    __repr__ = __str__
#
#    def __unicode__(self):
#        return unicode(self.__str__())