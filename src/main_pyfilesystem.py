#!/usr/bin/python
'''
Created on 26/07/2010

@author: piranna
'''

import sqlite3

import plugins

from PirannaFS.pyfilesystem import Filesystem


if __name__ == '__main__':
    # Load plugins
    pm = plugins.Manager()
    pm.Load_Dir("./plugins")

    # Set database, drive and sector size
    db = sqlite3.connect('../test/db.sqlite')
    drive = '../test/disk_part.img'
    sector_size = 512

    # Start filesystem
    Filesystem(db, drive, sector_size)