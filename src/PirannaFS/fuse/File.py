'''
Created on 14/08/2010

@author: piranna
'''

import sys
import errno

import plugins

from DB import DictObj, ChunkConverted

from ..File import BaseFile, readable, writeable


class File(BaseFile):
    '''
    classdocs
    '''

    def __init__(self, fs, path, flags, mode=None):                               # OK
        '''
        Constructor
        '''
#        print >> sys.stderr, '\n*** File __init__',fs, path,flags,mode

        self.__sector_size = fs.sector  # Sector size

        # Get file inode
        self.__inode = fs.Get_Inode(path[1:])

        # File not exist
        if self.__inode == -errno.ENOENT:
            inodeName = fs.Path2InodeName(path[1:])
            if inodeName < 0:
                return inodeName
            parent_dir_inode, name = inodeName

            # If dir_entry exist,
            # return error
            if fs.Get_Inode(name, parent_dir_inode) >= 0:
                return -errno.EEXIST

            self.__inode = self.db.mknod()
            self.db.link(parent_dir_inode, name, self.__inode)

        # Error
        elif self.__inode < 0:
            return self.__inode

        # Init base class
        BaseFile.__init__(self, fs, path)


    # Undocumented
    '''
    I have been not be able to found documentation for this functions,
    but it seems they are required to work using a file class in fuse-python
    since a patch done in 2008 to allow direct access to hardware instead
    of data been cached in kernel space before been sended to user space.
    Now you know the same as me, or probably more. If so, don't doubt in
    tell me it :-)
    '''
    def direct_io(self, *args, **kwargs):
        print >> sys.stderr, '*** direct_io', args, kwargs
        return -errno.ENOSYS

    def keep_cache(self, *args, **kwargs):
        print >> sys.stderr, '*** keep_cache', args, kwargs
        return -errno.ENOSYS


    # Overloaded

    # inits
#    def create(self):
#        print >> sys.stderr, '*** create'
#        return -errno.ENOSYS


#    def open(self):
#        print >> sys.stderr, '*** open'
#        return -errno.ENOSYS


#    # proxied
#    def fgetattr(self):
#        print >> sys.stderr, '*** fgetattr'
#        return -errno.ENOSYS
#
#
#    def flush(self):
#        print >> sys.stderr, '*** flush'
#        return -errno.ENOSYS
#
#
#    def fsync(self, isSyncFile):
#        print >> sys.stderr, '*** fsync', isSyncFile
#        return -errno.ENOSYS


    @writeable
    def ftruncate(self, length):
        if length < 0:
            return -errno.EINVAL

        ceil = divmod(length, self.__sector_size)
        if ceil[1]:
            ceil = ceil[0] + 1
        else:
            ceil = ceil[0]

        # Split chunks whose offset+length is greather that new file size
        for chunk in self.db.Get_Chunks_Truncate(file=self.__inode, ceil=ceil):
            if self.__Split_Chunks(chunk):
                self._Free_Chunks(chunk)

        # Set new file size
        self.db.Set_Size(inode=inode, size=length)

        return 0


#    def lock(self, cmd,owner, **kw):
#        print >> sys.stderr, '*** lock', cmd,owner
#        return -errno.ENOSYS


    @readable
    def read(self, length, offset):                                              # OK
#        print >> sys.stderr, '*** read', length,offset

        if not length:
            return None

        if offset < 0:
            return -errno.EINVAL

        # Get file size
        size = self.db.Get_Size(inode=self.__inode)

        # If offset required is greather or equals that file size
        # return EOF
        if offset >= size:
            return None

        # If length greather that remanent data
        # adjust length
        if length > size - offset:
            length = size - offset

        # Calc floor and ceil blocks required
        floor = offset // self.__sector_size
        ceil = (offset + length) // self.__sector_size

        # Readjust offset to be read query offset instead of file offset
        offset -= floor * self.__sector_size

#        print >> sys.stderr, "floor",floor, "ceil",ceil, "offset",offset

        # Read chunks
        chunks = self.__Get_Chunks(self.__inode, floor, ceil)
#        print >> sys.stderr, chunks

        readed = self.ll.Read(chunks)
#        print >> sys.stderr, repr(readed)

        plugins.send("File.read")
        return readed[offset:offset + length]


#    def release(self, flags):
#        print >> sys.stderr, '*** release', flags
#        return -errno.ENOSYS


    @writeable
    def write(self, data, offset):                                               # OK
        print >> sys.stderr, '\n*** write', repr(data), offset

        if not data:
            return None

        if offset < 0:
            return -errno.EINVAL

        # Get data size
        data_size = len(data)

        # Get file size
        file_size = offset + data_size

        # Calc floor and ceil blocks required
        floor = offset // self.__sector_size
        ceil = file_size // self.__sector_size

        sectors_required = 1 + ceil - floor

        # Get file chunks
        chunks = self.__Get_Chunks(self.__inode, floor, ceil)
        for chunk in chunks:
            if chunk['sector']:
                sectors_required -= chunk['length']

        # Get free space (if required)
        if sectors_required > 0:
            chunks_free, sectors_required = self.__Get_FreeSpace(sectors_required)
            chunks.extend(chunks_free)

        # If more sectors are required
        # return no space error
        if sectors_required > 0:
            return -errno.ENOSPC

        # If there is an offset in the first sector
        # adapt data chunks
        offset -= floor * self.__sector_size
        if offset:
            sector = chunks[0]['sector']

            # If first sector was written before
            # get it's current value as base for new data
            if sector:
                sector = self.ll.Read([{"sector":sector, "length":1}])
                sector = sector[:offset]

            # If not,
            # fill it with zeroes
            else:
                sector = '\0' * (offset)

            # Adapt data
            data = sector + data

#        # Add remaining zeroes at end of the data
#        # to align to self.__sector_size (if neccesary)
#        offset = len(data)%self.__sector_size
#        if offset:
#            data += '\0'*(self.__sector_size - offset)

        # Prepare chunks
        # [ToDo] data_offset can be superfluous...
#        print >> sys.stderr, "chunks",repr(chunks)
        chunks_write = []
        data_offset = 0
        block = floor

        for chunk in chunks:

            # Split chunk if it's bigger that the required space
            length = 1 + (data_size - data_offset) // self.__sector_size
            if chunk['length'] > length:
                chunk['length'] = length
                self.__Split_Chunks(chunk)

            # Add chunk to writable ones
            chunk['file'] = self.__inode
            chunk['block'] = block

            chunks_write.append(chunk)

            data_offset += chunk['length'] * self.__sector_size
            block += chunk['length']

            if block >= ceil:
                break

        # Write chunks
#        print >> sys.stderr, "chunks_write",repr(chunks_write)
        for chunk in chunks_write:
            offset = (chunk['block'] - floor) * self.__sector_size
            d = data[offset:offset + chunk['length'] * self.__sector_size]

            self.ll.Write_Chunk(chunk['sector'], d)
            plugins.send("File.write", chunk=chunk['id'], data=d)

        self.db.Put_Chunks(chunks_write)

#        plugins.send("File.write", chunks_write=chunks_write, data=data)

        # Set new file size if neccesary
        if file_size > self.db.Get_Size(inode=self.__inode):
            self.db.Set_Size(inode=self.__inode, size=file_size)

        # Return size of the written data
        return data_size


    # Don't show
    def _Free_Chunks(self, chunk):
#        plugins.send("File.ftruncate", chunk=chunk)
        self.db.Free_Chunks(chunk)
#        self.__Compact_FreeSpace()


    # Hide
    def __Get_Chunks(self, file, floor, ceil):                                    # OK
        '''
        Get sectors and use empty entries for not maped chunks (all zeroes)
        '''
#        print >> sys.stderr, '\tGet_Chunks', file,floor,ceil

        # Stored chunks
        chunks = self.db.Get_Chunks(file=self.__inode, floor=floor, ceil=ceil)

        #If there are chunks,
        # check their bounds
        if chunks:
            # Create first chunk if not stored
            chunk = DictObj(chunks[0])

            if chunk['block'] > floor:

                chunk['length'] = chunk['block'] - floor
                chunk['block'] = floor
                chunk['drive'] = None
                chunk['sector'] = None

                chunks = [chunk, ].extend(chunks)

            # Create last chunk if not stored
            chunk = DictObj(chunks[-1])

            chunk['block'] += chunk['length']
            if chunk['block'] - 1 < ceil:
                chunk['length'] = ceil - chunk['block'] - 1

                if chunk['length'] > 0:
                    chunk['drive'] = None
                    chunk['sector'] = None
                    chunks.extend([chunk, ])

        return chunks


    def __Get_FreeSpace(self, sectors_required):                                # OK
#        print >> sys.stderr, '*** __Get_FreeSpace', sectors_required
        chunks = []

        while sectors_required > 0:
            chunk = self.db.Get_FreeSpace(sectors_required, chunks) * self.__sector_size

            # Not chunks available
            if not chunk:
                break

            sectors_required -= chunk.length
            chunks.append(chunk)

        return chunks, sectors_required


    def __Split_Chunks(self, chunk):
        if self.db.Split_Chunks(ChunkConverted(chunk)):
            plugins.send("File.__Split_Chunks", chunk=chunk)

            return True