'''
Created on 29/03/2012

@author: piranna
'''

from unittest import main

import testfs

from PirannaFS import FileSystem
import plugins


if __name__ == '__main__':
    pm = plugins.Manager()
    pm.Load_Dir("./plugins")
    #pm.Load_Module('symlinks', './plugins')

    fs = FileSystem()

    fs.parser.fetch_mp = False
    fs.parse(values=fs, errex=1)

    fs.multithreaded = False
    fs.fuse_args.mountpoint = '../test/mountpoint'

    fs.main()

    main()