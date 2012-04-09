#!/usr/bin/python
'''
Created on 26/07/2010

@author: piranna
'''

import sqlite3

import plugins

from pirannafs.backends.pyfilesystem import Filesystem


def main():
    'Start a new instance of the filesystem using the PyFilesystem backend'

    # Load plugins
    pm = plugins.Manager()
    pm.Load_Dir("./plugins")

    # Set database and drive
    db_file = sqlite3.connect('../db.sqlite')
    drive = '../disk_part.img'

    # Start filesystem
    Filesystem(db_file, drive)


if __name__ == '__main__':
    main()
