#!/usr/bin/python
'''
Created on 26/07/2010

@author: piranna
'''

import sys
sys.stderr = open('../test/error.log', 'w')

from PirannaFS import FileSystem

import plugins


pm = plugins.Manager()
pm.Load_Dir("./plugins")

fs = FileSystem()
fs.multithreaded = False
fs.main()