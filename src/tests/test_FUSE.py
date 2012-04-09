'''
Created on 29/03/2012

@author: piranna
'''

from unittest import main

import plugins
import testfs

from pirannafs.backends.fuse import Filesystem


if __name__ == '__main__':
    pm = plugins.Manager()
    pm.Load_Dir("./plugins")
    #pm.Load_Module('symlinks', './plugins')

    fs = Filesystem()

    fs.parser.fetch_mp = False
    fs.parse(values=fs, errex=1)

    fs.multithreaded = False
    fs.fuse_args.mountpoint = '../test/mountpoint'

    fs.main()

    main()