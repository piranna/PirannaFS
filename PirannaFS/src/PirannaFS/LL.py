'''
Created on 07/08/2010

@author: piranna
'''



class LL:
    def __init__(self, drive,sector_size):
        """
        Constructor

        Open the underlying device to be written
        """
        self.__file = file(drive, "r+b")
        self.__sector_size = sector_size


    def __del__(self):
        """
        Destructor

        Close the underlying device that have been written
        """
        self.__file.close()


    def Read(self, chunks):
        """
        Read data from the underlying device
        """
        data = ""
        for chunk in chunks:
            if chunk['sector'] != None:
                data += self.Read_Chunk(chunk['sector'],
                                        chunk['length'])

            else:
                data += '\0'*chunk['length']*self.__sector_size

        return data


    def Read_Chunk(self, sector,length):
        """
        Read a single chunk from the underlying device
        """
        self.__file.seek(sector*self.__sector_size)
        return self.__file.read(length*self.__sector_size)


    def Write_Chunk(self, sector, data):
        """
        Write a single chunk in the underlying device
        """
        self.__file.seek(sector*self.__sector_size)
        self.__file.write(data)