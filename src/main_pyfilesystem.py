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
    db_file = sqlite3.connect('../db.sqlite')
    db_dirPath = '/home/piranna/Proyectos/FUSE/PirannaFS/src/sql'

    drive = '../disk_part.img'
    sector_size = 512

    # Start filesystem
    Filesystem(db_file, db_dirPath, drive, sector_size)