'''
Created on 26/09/2010

@author: piranna
'''

import sys

import plugins



def db_create(self):
    self.connection.execute('''
        CREATE TABLE IF NOT EXISTS log
        (
            link     INTEGER   PRIMARY KEY,

            deletion timestamp DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(link) REFERENCES links(id)
                ON UPDATE CASCADE
        )
    ''')


def db_unlinks(self, inode):
    '''
    Make a new file
    '''
    print >> sys.stderr, '*** db_log', inode

#    return self.connection.execute('''
#        INSERT INTO log(inode)
#        VALUES(?)
#        ''',
#        (inode,)).fetchone()


#plugins.connect(db_create,"FS.__init__")
plugins.connect(db_log)