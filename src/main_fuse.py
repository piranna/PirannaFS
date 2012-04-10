#!/usr/bin/python
'''
Created on 26/07/2010

@author: piranna
'''

import sqlite3

from plugins import Manager

from pirannafs.backends.fuse import Filesystem


def main():
    'Start a new instance of the filesystem using the FUSE backend'

    # Load plugins
    Manager('./plugins')

    # Set database and drive
    db_file = sqlite3.connect('../db.sqlite')
    drive = '../disk_part.img'

    # Start filesystem
    fs = Filesystem(db_file, drive)
    fs.multithreaded = False
    fs.main()


if __name__ == '__main__':
    main()
