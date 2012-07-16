'''
Created on 07/08/2010

@author: piranna
'''

from fcntl  import ioctl


# http://kogs-www.informatik.uni-hamburg.de/~meine/software/scripts/readfloppy
_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = (_IOC_NRSHIFT + _IOC_NRBITS)
_IOC_SIZESHIFT = (_IOC_TYPESHIFT + _IOC_TYPEBITS)
_IOC_DIRSHIFT = (_IOC_SIZESHIFT + _IOC_SIZEBITS)

_IOC_NONE = 0

def _IOC(dir, type, nr, size):
    return (dir << _IOC_DIRSHIFT |
            type << _IOC_TYPESHIFT |
            nr << _IOC_NRSHIFT |
            size << _IOC_SIZESHIFT)

def _IO(type, nr):
    return _IOC(_IOC_NONE, type, nr, 0)

BLKSSZGET = _IO(0x12, 104)

def _sector_size(fd):
    try:
        return ioctl(fd.fileno(), BLKSSZGET, -1)
    except IOError:
        return 512


class LL:
    def __init__(self, drive):
        """
        Constructor

        Open the underlying device to be written
        """
        if isinstance(drive, basestring):
            self._file = file(drive, "r+b")
        else:
            self._file = drive

        self.sector_size = _sector_size(self._file)

    def __del__(self):
        """
        Destructor

        Close the underlying device that have been written
        """
        self._file.close()

    def Get_NumSectors(self):
        """
        http://stackoverflow.com/questions/283707/size-of-an-open-file-object
        """
        # Store current position on the unterlying device
        prev = self._file.tell()

        # Get end position of the underlying device
        self._file.seek(0, 2)
        end = self._file.tell()

        # Restore underlying device to previous position
        self._file.seek(prev)

        # Return the number of sectors of the underlying device
        return (end - 1) // self.sector_size

    def Read(self, chunks):
        """
        Read data from the underlying device
        """
        data = ""

        for chunk in chunks:
            if chunk.sector != None:
                data += self.Read_Chunk(chunk.sector, chunk.length)
            else:
                data += '\0' * (chunk.length + 1) * self.sector_size

        return data

    def Read_Chunk(self, sector, length):
        """
        Read a single chunk from the underlying device
        """
        self._file.seek(sector * self.sector_size)
        return self._file.read((length + 1) * self.sector_size)

    def Write(self, chunks, data, sector_offset=0):
        """
        Write data the underlying device
        """
        for chunk in chunks:
            start = chunk.block * self.sector_size
            end = (chunk.block + chunk.length + 1) * self.sector_size

            self.Write_Chunk(chunk.sector, data[start:end], sector_offset)

            # We have just written the first sector, we can reset offset to 0
            sector_offset = 0

    def Write_Chunk(self, sector, data, sector_offset=0):
        """
        Write a single chunk in the underlying device
        """
        self._file.seek(sector * self.sector_size + sector_offset)
        self._file.write(data)
