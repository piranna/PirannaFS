'''
Created on 20/04/2012

@author: piranna
'''


class Inode(object):
    '''
    classdocs
    '''

    def __init__(self, fs, inode):
        '''
        Constructor
        '''
        self.fs = fs
        self.db = fs.db

        self._inode = inode

    def close(self):
        raise NotImplementedError

    def next(self):
        data = self.readline()
        if data:
            return data
        raise StopIteration

    def readline(self):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __iter__(self):
        return self
