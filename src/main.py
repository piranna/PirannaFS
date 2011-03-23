#!/usr/bin/python
'''
Created on 26/07/2010

@author: piranna
'''

import sys
sys.stderr = open('../test/error.log', 'w')

import sqlite3

from PirannaFS.pyfilesystem import FileSystem

import plugins


pm = plugins.Manager()
pm.Load_Dir("./plugins")

db = sqlite3.connect('../test/db.sqlite')

fs = FileSystem(db, '../test/disk_part.img', 512)
fs.multithreaded = False
fs.main()