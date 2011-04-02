'''
Created on 02/04/2011

@author: piranna
'''

from DB import DictObj


class BaseFile:
    '''
    classdocs
    '''


    def __init__(self, fs):
        '''
        Constructor
        '''
        self.fs = fs

        self._offset = 0


    def getsize(self):
        """Returns the size (in bytes) of a resource.

        :rtype: integer
        :returns: the size of the file
        """
        if self._inode != None:
            return self.fs.db.Get_Size(self._inode)
        return 0

    isempty = getsize


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

        self._inode = None
        self._offset = 0


    def _read(self, size):
        """
        """
        # Adjust read size
        remanent = self.fs.db.Get_Size(self._inode) - self._offset
        if remanent <= 0:
            return ""
        if 0 <= size < remanent:
            remanent = size

        # Calc floor and ceil blocks required
        floor, ceil = self._Calc_Bounds(remanent)

        # Read chunks
        chunks = self._Get_Chunks(floor, ceil)
        readed = self.fs.ll.Read(chunks)

        # Set read query offset and cursor
        offset = self._offset % self.fs.ll.sector_size
        self._offset += remanent

        return readed[offset:self._offset]


    def _Calc_Bounds(self, offset):
        floor = self._offset // self.fs.ll.sector_size
        ceil = (self._offset + offset - 1) // self.fs.ll.sector_size

        return floor, ceil

    def _Get_Chunks(self, floor, ceil=None):                             # OK
        '''
        Get sectors and use empty entries for not maped chunks (all zeroes)
        '''
#        print >> sys.stderr, '\tGet_Chunks', file,floor,ceil

        # Adjust ceil if we want only one chunk
        if ceil == None: ceil = floor

        # Stored chunks
        chunks = self.fs.db.Get_Chunks(self._inode, floor, ceil)
#        print "_Get_Chunks", chunks, floor, ceil
#        print "_Get_Chunks", self.fs.db.Get_Chunks(self._inode, 0, 2047)

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

    def _Set_Size(self, size):
        """Set file size and reset filesystem free space counter"""
        self.fs.db.Set_Size(self._inode, size)
        self.fs._freeSpace = None