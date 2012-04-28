'''
Created on 02/04/2011

@author: piranna
'''

from collections import namedtuple
from os          import SEEK_END
from stat        import S_IFDIR, S_IFREG

from pirannafs.errors import FileNotFoundError, IsADirectoryError
from pirannafs.errors import StorageSpace

from direntry import DirEntry


def readable(method):
    def wrapper(self, *args, **kwargs):
        if 'r' in self._mode:
            return method(self, *args, **kwargs)
        raise IOError("File not opened for reading")
    return wrapper


def writeable(method):
    def wrapper(self, *args, **kwargs):
        if 'w' in self._mode:
            if 'a' in self._mode:
                self.seek(0, SEEK_END)
            return method(self, *args, **kwargs)
        raise IOError("File not opened for writting")
    return wrapper


class BaseFile(DirEntry):
    '''
    classdocs
    '''

    def __init__(self, fs, path):
        '''
        Constructor

        @raise IsADirectoryError:
        @raise ParentDirectoryMissing:
        @raise ParentNotADirectoryError:
        '''
        # Get the inode of the parent or raise ParentDirectoryMissing exception
        DirEntry.__init__(self, fs, path)

        # If inode is a dir, raise error
        if self._inode and fs.db.Get_Mode(inode=self._inode) == S_IFDIR:
            raise IsADirectoryError(path)

        self.ll = fs.ll     # Low level implementation
        self._offset = 0

    #
    # Evented
    #

    @writeable
    def _truncate(self, size):
        ceil = (size - 1) // self.ll.sector_size

        # If new file size if bigger than zero, split chunks
        if ceil >= 0:
            self.db.truncate1(inode=self._inode, ceil=ceil,
                              size=size)  # Set_Size

        # Free unwanted chunks from the file
        else:
            self.db.truncate2(inode=self._inode, ceil=ceil,
                              size=size)  # Set_Size

        # Reset calculated free space on filesystem
        self.fs._freeSpace = None

#    @writeable
#    def _write(self, data):
#        if not data:
#            return
#
#        size = len(data)
#        floor, ceil = self.__CalcBounds(size)
#        sectors_required = ceil - floor
#
#### DB ###
#        # Get written chunks of the file
#        chunks = self.__GetChunks(floor, ceil)
#
#        # Check if there's enought free space available
#        for chunk in chunks:
#            # Discard chunks already in file from required space
#            if chunk.sector != None:
#                sectors_required -= chunk.length + 1
#
#        # Raise error if there's not enought free space available
#        if sectors_required > self.fs._FreeSpace() // self.ll.sector_size:
#            raise StorageSpace
#### DB ###
#
#### DB ###
#        # Fill holes between written chunks (if any)
#        for index, chunk in enumerate(chunks):
##            print "chunks durante", chunks
#            if chunk.sector == None:
#                chunk_block = chunk.block
#                chunk_length = chunk.length
#
#                while chunk_length >= 0:
#                    # Get the free chunk that best fit the hole
#                    free = self.db.Get_FreeChunk_BestFit(sectors_required=chunk_length)
#
#                    # If the free chunk is bigger than the hole, split it
#                    # Obviously, it's just the only one returned...
#                    free_length = free.length
#                    if free_length > chunk_length:
#                        free_length = chunk_length
#                        self.db.Split_Chunks(block=free.block,
#                                             inode=free.inode,
#                                             length=free_length)
#
#                    # Add the free chunk to the hole
#                    Namedtuple = namedtuple('namedtuple', free._fields)
#                    chunks.insert(index, Namedtuple(None, self._inode,
#                                                    chunk_block, free_length,
#                                                    free.sector))
#                    index += 1
#
#                    # Increase block number for the next free chunk in the hole
#                    # and decrease size of hole
#                    chunk_block += free_length + 1
#                    chunk_length -= free_length + 1
#
#                # Remove hole chunk since we have filled it
#                chunks.pop(index)
#### DB ###
#
#        file_size = self._offset + size
#
#        # If there is an offset in the first sector
#        # adapt data chunks
#        offset = self._offset % self.ll.sector_size
#        if offset:
#            sector = chunks[0].sector
##            print "sector:", sector, chunks
#
#            # If first sector was not written before
#            # fill space with zeroes
#            if sector == None:
#                sector = '\0' * offset
#
#            # Else get it's current value as base for new data
#            else:
#                sector = self.ll.Read_Chunk(sector, 0)[:offset]
#
#            # Adapt data
#            data = sector + data
#
#        # Write chunks data to the drive
#        self.ll.Write(chunks, data)
#
#        # Set new offset
#        self._offset = file_size
#
#### DB - They are independent and unrelated between them, so don't worry ###
#        # Put chunks in database
#        self.db.Put_Chunks(chunk._asdict() for chunk in chunks)
#
#        # Set new file size and reset calculated free space on filesystem
#        self.db._Set_Size(inode=self._inode, size=file_size)
#### DB ###

    @writeable
    def _write(self, data):
        if not data:
            return

        size = len(data)
        floor, ceil = self.__CalcBounds(size)
        sectors_required = ceil - floor

### DB ###
        # Get written chunks of the file
        chunks = self.__GetChunks(floor, ceil)

        # Check if there's enought free space available.
        # This implementation is only for overwriting, not copy-on-write
        for chunk in chunks:
            # Discard chunks already in file from required space
            if chunk.sector != None:
                sectors_required -= chunk.length + 1

        # Raise exception if there's not enought free space available
        if sectors_required > self.fs._FreeSpace() // self.ll.sector_size:
            raise StorageSpace
### DB ###

### DB ###
        # Fill holes between written chunks (if any)
        for index, chunk in enumerate(chunks):
#            print "chunks durante", chunks
            if chunk.sector == None:
                chunk_block = chunk.block

    ### DB ###
                # Get the free chunk that best fit the hole
                last = self.db.Get_FreeChunk_BestFit1(sectors_required=chunk.length)
                if last:
                    free_chunks = [last]

                else:
        ### DB ###
                    free_chunks = self.db.Get_FreeChunk_BestFit2(sectors_required=chunk.length)
                    if not free_chunks:
                        raise StorageSpace

                    # Update free chunks to be the correct blocks
                    Namedtuple = namedtuple('namedtuple',
                                            free_chunks[0]._fields)
                    for i, c in enumerate(free_chunks[:-1]):
                        free_chunks[i] = Namedtuple(None, self._inode,
                                                    chunk_block, c.length,
                                                    c.sector)
                        chunk_block += c.length + 1
        ### DB ###

                    last = free_chunks[-1]

        ### DB ###
                # If the last/only free chunk is bigger than the hole, split it
                last_length = last.length
                if last_length > chunk.length:
                    last_length = chunk.length
                    self.db.Split_Chunks(block=last.block,
                                         inode=last.inode,
                                         length=last_length)

                Namedtuple = namedtuple('namedtuple', last._fields)
                free_chunks[-1] = Namedtuple(None, self._inode,
                                             chunk_block, last_length,
                                             last.sector)
        ### DB ###
    ### DB ###

                # Add the free chunk to the hole
                chunks[index:index + 1] = free_chunks
### DB ###

        # Get write offset of the first sector
        offset = self._offset % self.ll.sector_size

        # If there is an offset in the first sector and it was not written
        # before, padding with zeroes and reset offset since we have filled it
        if offset and chunks[0].inode == None:
            data = '\0' * offset + data
            offset = 0

        # Write chunks data to the drive
        self.ll.Write(chunks, data, offset)

        # Set new file size and offset
        file_size = self._offset + size
        self._offset = file_size

### DB - They are independent and unrelated between them, so don't worry ###
        # Put chunks in database
        self.db.Put_Chunks(chunk._asdict() for chunk in chunks)

        # Set new file size and reset calculated free space on filesystem
        self.db._Set_Size(inode=self._inode, size=file_size)
### DB ###

    #
    # File-like interface
    #

    def __del__(self):
        self.close()

    def close(self):
        self.flush()
#        self._mode = frozenset()

    def flush(self):
        pass
#        self.ll._file.flush()

    @readable
    def read(self, size= -1):
        floor, ceil, remanent = self.__readPre(size)
        if not remanent:
            return ""

        # Read chunks
        chunks = self.__GetChunks(floor, ceil)
        readed = self.ll.Read(chunks)

        return self.__readPost(readed, remanent)

    @readable
    def readline(self, size= -1):
        floor, _, remanent = self.__readPre(size)
        if not remanent:
            return ""

        # Read chunks
        readed = ""
        while remanent > 0:
            # Read chunk
            chunks = self.__GetChunks(floor, floor)
            data = self.ll.Read(chunks)

            # Check if we have get end of line
            try:
                index = data.index('\n') + 1

            except ValueError:
                # Calc next block required
                readed += data
                floor += chunks[0].length + 1
                remanent -= len(data)

            else:
                readed += data[:index]
                break

        remanent = len(readed)

        return self.__readPost(readed, remanent)

    def readlines(self, sizehint= -1):
        """
        """
        return self.read(sizehint).splitlines(True)

    def tell(self):
        """Return the current cursor position offset

        @return: integer
        """
        return self._offset

#    def __str__(self):
#        return "<File in %s %s>" % (self.__fs, self.path)
#
#    __repr__ = __str__
#
#    def __unicode__(self):
#        return unicode(self.__str__())

    #
    # Protected
    #

    def _CalcMode(self, mode):
        # Based on code from filelike.py

        def make():
            self._inode = self.db.mknod(type=S_IFREG)
            self.db.link(parent_dir=self.parent, name=self.name,
                         child_entry=self._inode)

        # Set `self._mode` as a set so we can modify it.
        # Needed to truncate the file while processing the mode
        self._mode = set()

        # Calc the mode and perform the corresponding initialization actions
        if 'r' in mode:
            # Action
            if self._inode == None:
                raise FileNotFoundError(self.path)

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
            if self._inode == None:
                make()
            else:
                self._truncate(0)

        elif 'a' in mode:
            # Action
            if self._inode == None:
                make()
            else:
                self.seek(0, SEEK_END)

            # Set mode
            self._mode.add('w')
            self._mode.add('a')
            if '+' in mode:
                self._mode.add('r')

        # Re-set `self._mode` as an inmutable frozenset.
        self._mode = frozenset(self._mode)

    #
    # Private
    #

    def __CalcBounds(self, size):
        floor = self._offset // self.ll.sector_size
        ceil = (self._offset + size - 1) // self.ll.sector_size

        return floor, ceil

    def __GetChunks(self, floor, ceil):                             # OK
        '''
        Get sectors and use empty entries for not maped chunks (all zeroes)
        '''
#        print >> sys.stderr, '\tGet_Chunks', file,floor,ceil

        # Stored chunks
        chunks = self.db.Get_Chunks(inode=self._inode, floor=floor, ceil=ceil)

        Namedtuple = namedtuple('namedtuple',
                                ('id', 'inode', 'block', 'length', 'sector'))

        #If there are chunks, check their bounds
        if chunks:
            # Create first chunk if not stored
            chunk = chunks[0]

            if chunk.block > floor:

                chunk.length = chunk.block - floor - 1
                chunk.block = floor
                chunk.sector = None

                chunk.drive = None
                chunks = [chunk].extend(chunks)

            # Create last chunk if not stored
            chunk = chunks[-1]

            chunk_block = chunk.block + chunk.length
            if chunk_block < ceil:
                chunk_block += 1
                chunk_length = ceil - chunk_block
                chunk_sector = None

#                chunk.drive = None
                chunks.append(Namedtuple(chunk.id, chunk.inode, chunk_block,
                                         chunk_length, chunk_sector))

        # There's no chunks for that file at this blocks, make a fake empty one
        else:
            # Create first chunk if not stored
            chunk = Namedtuple(None, None, floor, ceil - floor, None)

#            chunk.drive = None
            chunks.append(chunk)

        # Return list of chunks
        return chunks

    def __readPre(self, size= -1):
        if not size:
            return None, None, 0

        # Adjust read size
        remanent = self.db.Get_Size(inode=self._inode) - self._offset
        if remanent <= 0:
            return None, None, 0
        if 0 <= size < remanent:
            remanent = size

        # Calc floor and ceil blocks required
        floor, ceil = self.__CalcBounds(remanent)

        return floor, ceil, remanent

    def __readPost(self, readed, remanent):
        """Set read query offset and cursor"""
        offset = self._offset % self.ll.sector_size
        self._offset += remanent

        return readed[offset:self._offset]
