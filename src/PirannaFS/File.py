'''
Created on 02/04/2011

@author: piranna
'''

from stat import S_IFDIR, S_IFREG

from os import SEEK_END
from os.path import split

from antiorm import DictObj

from errors import ResourceInvalid, ResourceNotFound, StorageSpace


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


class BaseFile(object):
    '''
    classdocs
    '''

    def __init__(self, fs, path):
        '''
        Constructor
        '''
        # Get file inode or raise exception
        try:
            self._inode = fs._Get_Inode(path)
        except ResourceNotFound:
            self._inode = None
        else:
            # If inode is a dir, raise error
            if fs.db.Get_Mode(inode=self._inode) == S_IFDIR:
                raise ResourceInvalid(path)

        self.fs = fs        # Filesystem
        self.db = fs.db     # Database
        self.ll = fs.ll     # Low level implementation

        self.path = path
        path, self.name = split(path)
        self.parent = fs._Get_Inode(path)

        self._offset = 0

    #
    # Evented
    #

    @writeable
    def _truncate(self, size):
        ceil = (size - 1) // self.ll.sector_size

        # If new file size if bigger than zero, split chunks
        if ceil > -1:
            chunks = self.db.Get_Chunks_Truncate(file=self._inode, ceil=ceil)
            self.db.Split_Chunks(chunks)

        # Free unwanted chunks from the file
        chunks = self.db.Get_Chunks_Truncate(file=self._inode, ceil=ceil)
        self.db.Free_Chunks(chunks)

        # Set new file size
        self.__Set_Size(size)

    @writeable
    def _write(self, data):
        if not data:
            return

        size = len(data)
        floor, ceil = self.__CalcBounds(size)
        sectors_required = ceil - floor

        ### DB ###
        sectors_required, chunks = self.__GetChunksWritten(sectors_required,
                                                           floor, ceil)

        # Raise error if there's not enought free space available
        if sectors_required > self.fs._FreeSpace() // self.ll.sector_size:
            raise StorageSpace
        ### DB ###

        file_size = self._offset + size

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

### DB ###
        # Fill holes between written chunks (if any)
        for chunk in chunks:
#            print "chunks durante", chunks
            if chunk.sector == None:
                index = chunks.index(chunk)
                block = chunk.block

                while chunk.length >= 0:
                    # Get the free chunk that best fit the hole

                    req = chunk.length
                    blocks = ','.join([str(chunk.block) for chunk in chunks])
                    free = self.db.Get_FreeChunk_BestFit(sectors_required=req,
                            blocks=blocks)

                    # If free chunk is bigger that hole, split it
                    if free.length > chunk.length:
                        free.length = chunk.length
                        self.db.Split_Chunks(**free)

                    # Adapt free chunk
                    free.file = self._inode
                    free.block = block

                    # Add free chunk to the hole
                    chunks.insert(index, free)
                    index += 1

                    # Increase block number for the next free chunk in the hole
                    # and decrease size of hole
                    block += free.length + 1
                    chunk.length -= free.length + 1

                # Remove hole chunk since we have filled it
                chunks.pop(index)
### DB ###

        # Write chunks data to the drive
        for chunk in chunks:
            offset = (chunk.block - floor) * self.ll.sector_size
            d = data[offset:offset + (chunk.length + 1) * self.ll.sector_size]
            self.ll.Write_Chunk(chunk.sector, d)

        # Set new offset
        self._offset = file_size

### DB ###
        # Put chunks in database
        self.db.Put_Chunks(chunks)

        # Set new file size if neccesary
        if self.db.Get_Size(inode=self._inode) < file_size:
            self.__Set_Size(file_size)
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

    def next(self):
        data = self.readline()
        if data:
            return data
        raise StopIteration

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
                raise ResourceNotFound(self.path)

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
        chunks = self.db.Get_Chunks(file=self._inode, floor=floor, ceil=ceil)

        #If there are chunks, check their bounds
        if chunks:
            # Create first chunk if not stored
            chunk = DictObj(chunks[0])

            if chunk['block'] > floor:

                chunk.length = chunk['block'] - floor - 1
                chunk['block'] = floor
                chunk['drive'] = None
                chunk['sector'] = None

                chunks = [chunk].extend(chunks)

            # Create last chunk if not stored
            chunk = DictObj(chunks[-1])

            chunk['block'] += chunk.length
            if  chunk['block'] < ceil:
                chunk['block'] += 1
                chunk.length = ceil - chunk['block']

                chunk['drive'] = None
                chunk['sector'] = None
                chunks.append(chunk)

        # There's no chunks for that file at this blocks, make a fake empty one
        else:
            # Create first chunk if not stored
            chunk = DictObj()

            chunk.length = ceil - floor
            chunk.block = floor
            chunk.drive = None
            chunk.sector = None

            chunks.append(chunk)

        # Return list of chunks
        return chunks

    def __GetChunksWritten(self, sectors_required, floor, ceil):
        """Get written chunks of the file"""
        chunks = self.__GetChunks(floor, ceil)

        # Check if there's enought free space available
        for chunk in chunks:
            # Discard chunks already in file from required space
            if chunk.sector != None:
                sectors_required -= chunk.length + 1

        return sectors_required, chunks

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

    def __Set_Size(self, size):
        """Set file size and reset filesystem free space counter"""
        self.db.Set_Size(inode=self._inode, size=size)
        self.fs._freeSpace = None
