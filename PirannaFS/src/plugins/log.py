'''
Created on 26/09/2010

@author: piranna
'''

import sys

import plugins



class log(plugins.Plugin):
    def __init__(self):
#        print >> sys.stderr, '*** log.__init__'

        self.__db = None

        plugins.connect(self.create,"FS.__init__")
        plugins.connect(self.log)


    def create(self, db):
        '''
        Create the log table in the database
        '''
#        print >> sys.stderr, '*** create', db

        self.__db = db
        self.__db.connection.execute('''
            CREATE TABLE IF NOT EXISTS log
            (
                'who'   TEXT      NULL,                      --User
                'what'  TEXT      NOT NULL,                  --Action / Caller.Action?
                'where' TEXT      NOT NULL,                  --Caller / GPS?    # http://live.gnome.org/action/show/GnomeActivityJournal
                'when'  timestamp DEFAULT CURRENT_TIMESTAMP, --Timestamp
                'why'   TEXT      NULL,
                'how'   TEXT      NOT NULL,                  --Parameters
                'whom'  INTEGER   NULL,                      --Inode
                'for'   TEXT      NULL,

                FOREIGN KEY('whom') REFERENCES dir_entries(inode)
                    ON UPDATE CASCADE
            )
        ''')


#    def log(self, **named):
    def log(self):
        '''
        Make a log entry in the database
        '''
#        print >> sys.stderr, '*** log', named

        frame = sys._getframe(3)

        what  = frame.f_code.co_name
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

        return self.__db.connection.execute('''
            INSERT INTO log('what','where','how')
            VALUES(?,?,?)
            ''',
            (what,where,str(how)))