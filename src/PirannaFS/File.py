'''
Created on 02/04/2011

@author: piranna
'''

from stat import S_IFDIR, S_IFREG

from os import SEEK_SET, SEEK_CUR, SEEK_END
from os.path import split

from DB import DictObj

from fs.errors import ResourceInvalidError, ResourceNotFoundError


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

    # Common

    def __init__(self, fs, path, make=False):
        '''
        Constructor
        '''
        # Get file inode or raise exception
        try:
            self._inode = fs.Get_Inode(path)
        except ResourceNotFoundError:
            if make:
                self._make()
            else:
                self._inode = None
        else:
            # If inode is a dir, raise error
            if fs.db.Get_Mode(inode=self._inode) == S_IFDIR:
                raise ResourceInvalidError(path)

        self.fs = fs        # Filesystem
        self.db = fs.db     # Database
        self.ll = fs.ll     # Low level implementation

        self.path = path
        path, self.name = split(path)
        self.parent = fs.Get_Inode(path)

        self._offset = 0


    def getsize(self):
        """Returns the size (in bytes) of a resource.

        :rtype: integer
        :returns: the size of the file
        """
        if self._inode != None:
            return self.db.Get_Size(inode=self._inode)
        return 0

    isempty = getsize


    def remove(self):
        """Remove a file from the filesystem.

        :raises ParentDirectoryMissingError: if a containing directory is missing and recursive is False
        :raises ResourceInvalidError:        if the path is a directory or a parent path is an file
        :raises ResourceNotFoundError:       if the path is not found
        """
#        # Get inode and name from path

        if self._inode == None:
            raise ResourceNotFoundError(self.path)

        # Unlink dir entry
        self.db.unlink(parent_dir=self.parent, name=self.name)

        self._inode = None
        self._offset = 0


        # Evented

    def _make(self):
        self._inode = self.db.mknod(type=S_IFREG)
        self.db.link(parent_dir=self.parent, name=self.name,
                     child_entry=self._inode)


    @writeable
    def _truncate(self, size):
        ceil = (size - 1) // self.ll.sector_size

        # If new file size if bigger than zero, split chunks
        if ceil > -1:
            for chunk in self.db.Get_Chunks_Truncate(file=self._inode, ceil=ceil):
                print "_truncate"
                self.db.Split_Chunks(**ChunkConverted(chunk))

        def Free_Chunks(chunk):
            self.db.Free_Chunks(**chunk)
    #        self.__Compact_FreeSpace()

        # Free unwanted chunks from the file
        for chunk in self.db.Get_Chunks_Truncate(file=self._inode, ceil=ceil):
            Free_Chunks(chunk)

        # Set new file size
        self._Set_Size(size)


    # File-like

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
        chunks = self._Get_Chunks(floor, ceil)
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
            chunks = self._Get_Chunks(floor, floor)
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


    def seek(self, offset, whence=SEEK_SET):
        """
        """
        # Set whence
        if   whence == SEEK_SET: whence = 0
        elif whence == SEEK_CUR: whence = self._offset
        elif whence == SEEK_END: whence = self.db.Get_Size(inode=self._inode)
        else:                    raise ResourceInvalidError(self.path)

        # Readjust offset
        self._offset = whence + offset

    def tell(self):
        """Return the current cursor position offset

        @return: integer
        """
        return self._offset


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


    # Protected

    def _CalcMode(self, mode):
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
            if self._inode == None:
                self.make()
            else:
                self._truncate(0)

        elif 'a' in mode:
            # Action
            if self._inode == None:
                self.make()
            else:
                self.seek(0, SEEK_END)

            # Set mode
            self._mode.add('w')
            self._mode.add('a')
            if '+' in mode:
                self._mode.add('r')

        # Re-set `self._mode` as an inmutable frozenset.
        self._mode = frozenset(self._mode)


    def _Calc_Bounds(self, offset):
        floor = self._offset // self.ll.sector_size
        ceil = (self._offset + offset - 1) // self.ll.sector_size

        return floor, ceil

    def _Get_Chunks(self, floor, ceil):                             # OK
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
        floor, ceil = self._Calc_Bounds(remanent)

        return floor, ceil, remanent

    def __readPost(self, readed, remanent):
        """Set read query offset and cursor"""
        offset = self._offset % self.ll.sector_size
        self._offset += remanent

        return readed[offset:self._offset]


    def _Set_Size(self, size):
        """Set file size and reset filesystem free space counter"""
        self.db.Set_Size(inode=self._inode, size=size)
        self.fs._freeSpace = None