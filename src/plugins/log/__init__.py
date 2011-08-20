'''
Created on 26/09/2010

@author: piranna
'''

import sys

import plugins

from DB import DB


class log(plugins.Plugin):
    def __init__(self):
#        print '*** log.__init__'

        self.db = DB('/home/piranna/Proyectos/FUSE/PirannaFS/TestPirannaFS_1.sqlite')

#        plugins.connect(self.create, "FS.__init__")
        plugins.connect(self.log)


#    def log(self, **named):
    def log(self):
        '''
        Make a log entry in the database
        '''
#        print '*** log'

        frame = sys._getframe(3)

        what = frame.f_code.co_name
        where = frame.f_locals['self'].__class__.__name__

        how = dict(frame.f_locals)
        del how['self']

    #    print >> sys.stderr, 'who\t'#,   "user"
    #    print >> sys.stderr, 'what\t',  what
    #    print >> sys.stderr, 'where\t', where
    #    print >> sys.stderr, 'when\t'#,  "now"
    #    print >> sys.stderr, 'why\t'
    #    print >> sys.stderr, 'how\t',   how
    #    print >> sys.stderr, 'whom\t'#,  "inode"
    #    print >> sys.stderr, 'for\t'
    #    print

        return self.db.insert(what=what, where=where, how=str(how))