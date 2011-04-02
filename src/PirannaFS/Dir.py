'''
Created on 02/04/2011

@author: piranna
'''

class BaseDir:
    '''
    classdocs
    '''


    def __init__(self, fs):
        '''
        Constructor
        '''
        self.fs = fs


    def isempty(self):
        """Check if a directory is empty (contains no files or sub-directories)

        @rtype: bool
        """
        return self.fs.db.readdir(self._inode, 1)