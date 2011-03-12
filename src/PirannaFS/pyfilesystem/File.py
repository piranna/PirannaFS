'''
Created on 14/08/2010

@author: piranna
'''

import os

from fs.errors import *

import plugins



class File(object):
    '''
    classdocs
    '''
    def __init__(self, fs, path, mode):
        self.__inode = fs.Get_Inode(path[1:])

        self.__mode = mode
        self.__offset = 0


    def close(self):
        pass


    def flush(self):
        pass


    def next(self):
        pass


    def read(self, size=-1):
#        print >> sys.stderr, '*** read', length

        plugins.send("File.reading")

        # Adjust read size
        remanent = self.__db.Get_Size(self.__inode) - self.__offset
        if size < 0 or size > remanent:
            size = remanent

        # Calc floor and ceil blocks required
        floor = self.__offset//self.__sector_size
        ceil = (self.__offset+size)//self.__sector_size

#        print >> sys.stderr, "floor",floor, "ceil",ceil

        # Read chunks
        chunks = self.__Get_Chunks(self.__inode,floor,ceil)
        readed = self.__ll.Read(chunks)
#        print >> sys.stderr, chunks
#        print >> sys.stderr, repr(readed)

        # Set read query offset and cursor
        offset = self.__offset - floor*self.__sector_size
        self.__offset += size

        # Return data
        plugins.send("File.readed")
        return readed[offset:self.__offset]


    def readline(self, size=-1):
        pass


#    def readlines(self, sizehint=-1):
#        pass


    def seek(self, offset, whence=os.SEEK_SET):
#        print >> sys.stderr, '*** read', length,offset

        plugins.send("File.seeking")

        # Set whence
        if whence == os.SEEK_SET:
            whence = 0
        elif whence == os.SEEK_CUR:
            whence = self.__offset
        elif whence == os.SEEK_END:
            whence = self.__db.Get_Size(self.__inode)
        else:
            raise ResourceInvalidError(self.__path)

        # Readjust offset
        offset = whence + offset
#        if offset < 0:
#            raise
        self.__offset = offset

        plugins.send("File.seeked")


    def tell(self):
        pass


    def truncate(self, size=0):
        pass


    def write(self, data):
        pass


    def writelines(self, sequence):
        pass


#    def __del__(self):
#        pass
#
#
#    def __enter__(self):
#        pass
#
#
#    def __exit__(self,exc_type,exc_value,traceback):
#        pass


    def __iter__(self):
        pass


#    def __str__(self):
#        return "<File in %s %s>" % (self.__fs, self.path)
#
#    __repr__ = __str__
#
#
#    def __unicode__(self):
#        return unicode(self.__str__())