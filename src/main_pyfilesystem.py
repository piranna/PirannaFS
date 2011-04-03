#!/usr/bin/python
'''
Created on 26/07/2010

@author: piranna
'''

import sqlite3

import plugins

from PirannaFS.pyfilesystem import Filesystem


if __name__ == '__main__':
    pm = plugins.Manager()
    pm.Load_Dir("./plugins")

    db = sqlite3.connect('../test/db.sqlite')
    drive = '../test/disk_part.img'
    sector_size = 512

    Filesystem(db, drive, sector_size)