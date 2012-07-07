#!/usr/bin/python
'''
Created on 26/07/2010

@author: piranna
'''

from os.path import abspath, dirname, join
from sqlite3 import connect

from plugins import Manager

from pirannafs.backends.fuse import Filesystem


def main():
    'Start a new instance of the filesystem using the FUSE backend'

    file_path = dirname(abspath(__file__))

    # Load plugins
    Manager(join(file_path, '../..', 'plugins'))

    # Set database and drive
    db_file = connect(join(file_path, '..', 'db.sqlite'))
    drive = join(file_path, '../..', 'disk_part.img')

    # Start filesystem
    fs = Filesystem(db_file, drive)
    fs.multithreaded = False
    fs.main()


if __name__ == '__main__':
    main()
