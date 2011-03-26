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

from ..DB import DictObj


def readable(method):
    def wrapper(self, *args, **kwargs):
        if 'r' in self._mode:
            return method(self, *args, **kwargs)
    return wrapper

def writeable(method):
    def wrapper(self, *args, **kwargs):
        if 'w' in self._mode:
            if 'a' in self._mode:
                self.seek(0, os.SEEK_END)
            return method(self, *args, **kwargs)
    return wrapper


class File(object):
    '''
    classdocs
    '''
    def __init__(self, fs, path, mode, **kwargs):
        """

        @raise ParentDirectoryMissingError:
        @raise ResourceNotFoundError:
        @raise ResourceInvalidError:
        """
        try:
            self.__inode = fs.Get_Inode(path)
        except ResourceNotFoundError:
            self.__inode = None
        else:
            # If inode is a dir, raise error
            if fs.db.Get_Mode(self.__inode) == stat.S_IFDIR:
                raise ResourceInvalidError(path)

        self.__offset = 0
        self.fs = fs
        self.path = path

        # Based on code from filelike.py
        self._mode = set()

        if 'r' in mode:
            # Mode
            self._mode.add('r')
            if '+' in mode:
                self._mode.add('w')

            if self.__inode == None:
                raise ResourceNotFoundError(path)

        elif 'w' in mode:
            # Mode
            self._mode.add('w')
            if '+' in mode:
                self._mode.add('r')

            if self.__inode == None:
                self.make()
            else:
                self.truncate()

        elif 'a' in mode:
            # Mode
            self._mode.add('w')
            self._mode.add('a')
            if '+' in mode:
                self._mode.add('r')

            if self.__inode == None:
                self.make()
            else:
                self.seek(0, os.SEEK_END)


    def close(self):
        plugins.send("File.close")

    def flush(self):
        pass

    def make(self):
        # Check if dir_entry
        if self.__inode:
            raise DestinationExistsError(self.path)

        # Get parent dir
        parent_dir_inode, name = self.fs.Path2InodeName(self.path)

        # Make file
        self.__inode = self.fs.db.mknod()
        self.fs.db.link(parent_dir_inode, name, self.__inode)

    def next(self):
        data = self.readline()
        if data:
            return data
        raise StopIteration


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
        remanent = self.fs.db.Get_Size(self.__inode) - self.__offset
        if 0 <= size < remanent:
            remanent = size

        # Calc floor required
        floor = self.__offset // self.fs.ll.sector_size

        block = floor
        readed = ""

        while remanent > 0:
            # Read chunk
            chunks = self.__Get_Chunks(self.__inode, block)
            data = self.fs.ll.Read(chunks)

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
        offset = self.__offset - floor * self.fs.ll.sector_size
        self.__offset += len(readed)

        plugins.send("File.readline end")

        return readed[offset:self.__offset]

    @readable
    def readlines(self, sizehint= -1):
        """
        """
        plugins.send("File.readlines begin")
        data = self._read(sizehint).splitlines(True)
        plugins.send("File.readlines end")
        return data

    def _read(self, size):
        """
        """
        # Adjust read size
        remanent = self.fs.db.Get_Size(self.__inode) - self.__offset
        if remanent <= 0:
            return ""
        if 0 <= size < remanent:
            remanent = size

        # Calc floor and ceil blocks required
        floor, ceil = self.__Calc_Bounds(remanent)

        # Read chunks
        chunks = self.__Get_Chunks(self.__inode, floor, ceil)
        readed = self.fs.ll.Read(chunks)

        # Set read query offset and cursor
        offset = self.__offset % self.fs.ll.sector_size
        self.__offset += remanent

        return readed[offset:self.__offset]


    def remove(self):
        """Remove a file from the filesystem.

        :raises ParentDirectoryMissingError: if a containing directory is missing and recursive is False
        :raises ResourceInvalidError:        if the path is a directory or a parent path is an file
        :raises ResourceNotFoundError:       if the path is not found
        """
        # Get inode and name from path
        parent_inode, name = self.fs.Path2InodeName(self.path)

        # Unlink dir entry
        self.fs.db.unlink(parent_inode, name)

        self.__inode = None
        self.__offset = 0


    def seek(self, offset, whence=os.SEEK_SET):
        """
        """
#        print >> sys.stderr, '*** read', length,offset

        plugins.send("File.seeking")

        # Set whence
        if   whence == os.SEEK_SET: whence = 0
        elif whence == os.SEEK_CUR: whence = self.__offset
        elif whence == os.SEEK_END: whence = self.fs.db.Get_Size(self.__inode)
        else:                       raise ResourceInvalidError(self.__path)

        # Readjust offset
        self.__offset = whence + offset

        plugins.send("File.seeked")

    def tell(self):
        """Return the current cursor position offset

        @return: integer
        """
        return self.__offset


    @writeable
    def truncate(self, size=0):
        size += self.__offset

        ceil = divmod(size, self.fs.ll.sector_size)
        if ceil[1]:
            ceil = ceil[0] + 1
        else:
            ceil = ceil[0]

        # Split chunks whose offset+length is greather that new file size
        for chunk in self.fs.db.Get_Chunks_Truncate(self.__inode, ceil):
            if self.fs.db.Split_Chunks(chunk):
                self._Free_Chunks(chunk)

        # Set new file size
        self.fs.db.Set_Size(self.__inode, size)


    @writeable
    def write(self, data):
        if not data: return

        # Initialize vars here to minimize database acess isolation
        data_size = len(data)
        file_size = self.__offset + data_size
        floor, ceil = self.__Calc_Bounds(data_size)
        sectors_required = ceil - floor

### DB ###
        # Get written chunks of the file
        chunks = self.__Get_Chunks(self.__inode, floor, ceil)

        # Check if there's enought free space available
        for chunk in chunks:
            # Discard chunks already in file from required space
            if chunk.sector != None:
                sectors_required -= chunk.length + 1

#        # [ToDo] Calc free space before start spliting free chunks in database
#        # and fragment all the filesystem
#        if sectors_required < 
#            raise StorageSpaceError

#        print "sectors_required", sectors_required
#        print "chunks antes", chunks

        # Fill holes between written chunks (if any)
        for chunk in chunks:
#            print "chunks durante", chunks
            if chunk.sector == None:
                index = chunks.index(chunk)
                block = chunk.block

                while chunk.length >= 0:
                    # Get the free chunk that best fit the hole
                    free = self.fs.db.Get_FreeSpace(chunk.length,
                                            [chunk.block for chunk in chunks])

                    # If there's no more free space available, raise error
                    if not free:
                        raise StorageSpaceError

                    # If free chunk is bigger that hole, split it
                    if free.length > chunk.length:
                        free.length = chunk.length
                        self.fs.db.Split_Chunks(free)

                    # Adapt free chunk
                    free.file = self.__inode
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
        self.fs.db.Put_Chunks(chunks)

        # Set new file size if neccesary
        if self.fs.db.Get_Size(self.__inode) < file_size:
            self.fs.db.Set_Size(self.__inode, file_size)
### DB ###

        # If there is an offset in the first sector
        # adapt data chunks
        offset = self.__offset % self.fs.ll.sector_size
        if offset:
            sector = chunks[0]['sector']

            # If first sector was not written before
            # fill space with zeroes
            if sector == None:
                sector = '\0' * offset

            # Else get it's current value as base for new data
            else:
                sector = self.fs.ll.Read([{"sector":sector, "length":0}])
                sector = sector[:offset]

            # Adapt data
            data = sector + data

        # Write chunks data to the drive
        for chunk in chunks:
            offset = (chunk.block - floor) * self.fs.ll.sector_size
            self.fs.ll.Write_Chunk(chunk.sector,
                data[offset:offset + (chunk.length + 1) * self.fs.ll.sector_size])

        # Set new offset
        self.__offset = file_size

        plugins.send("File.write", chunks=chunks, data=data)

    @writeable
    def writelines(self, sequence):
        data = ""
        for line in sequence:
            data += line
        if data:
            self.write(data)


    def __del__(self):
        self.close()

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


    # Don't show

    def _Free_Chunks(self, chunk):
#        plugins.send("File._Free_Chunks", chunk=chunk)
        self.fs.db.Free_Chunks(chunk)
#        self.__Compact_FreeSpace()


    # Hide

    def __Calc_Bounds(self, offset):
        floor = self.__offset // self.fs.ll.sector_size
        ceil = (self.__offset + offset - 1) // self.fs.ll.sector_size

        return floor, ceil

    def __Get_Chunks(self, file, floor, ceil=None):                             # OK
        '''
        Get sectors and use empty entries for not maped chunks (all zeroes)
        '''
#        print >> sys.stderr, '\tGet_Chunks', file,floor,ceil

        # Adjust ceil if we want only one chunk
        if ceil == None: ceil = floor

        # Stored chunks
        chunks = self.fs.db.Get_Chunks(self.__inode, floor, ceil)
#        print "__Get_Chunks", chunks, floor, ceil
#        print "__Get_Chunks", self.fs.db.Get_Chunks(self.__inode, 0, 2047)

        #If there are chunks, check their bounds
        if chunks:
            # Create first chunk if not stored
            chunk = DictObj(chunks[0])

            if chunk['block'] > floor:

                chunk.length = chunk['block'] - floor - 1
                chunk['block'] = floor
                chunk['drive'] = None
                chunk['sector'] = None

                chunks = [chunk, ].extend(chunks)

            # Create last chunk if not stored
            chunk = DictObj(chunks[-1])

            chunk['block'] += chunk.length
            if  chunk['block'] < ceil:
                chunk['block'] += 1
                chunk.length = ceil - chunk['block']

                chunk['drive'] = None
                chunk['sector'] = None
                chunks.extend([chunk, ])

        # There're no chunks for that file at this blocks, make a fake empty one
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