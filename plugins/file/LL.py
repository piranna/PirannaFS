'''
Created on 07/08/2010

@author: piranna
'''


class LL:
    def __init__(self, drive, sector_size):
        """
        Constructor

        Open the underlying device to be written
        """
        if isinstance(drive, basestring):
            self._file = file(drive, "r+b")
        else:
            self._file = drive

        self.sector_size = sector_size

    def __del__(self):
        """
        Destructor

        Close the underlying device that have been written
        """
        self._file.close()

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
            end = start + (chunk.length + 1) * self.sector_size

            self.Write_Chunk(chunk.sector, data[start:end], sector_offset)

            # We have just written the first sector, we can reset offset to 0
            sector_offset = 0

    def Write_Chunk(self, sector, data, sector_offset=0):
        """
        Write a single chunk in the underlying device
        """
        self._file.seek(sector * self.sector_size + sector_offset)
        self._file.write(data)
