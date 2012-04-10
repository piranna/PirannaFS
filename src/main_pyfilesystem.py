#!/usr/bin/python
'''
Created on 26/07/2010

@author: piranna
'''

from os.path import abspath, dirname, join
from sqlite3 import connect

from fs.expose.fuse import mount

from plugins import Manager

from pirannafs.backends.pyfilesystem import Filesystem


def main():
    '''Start a new instance of the filesystem using the PyFilesystem backend
    and export it using the FUSE expose subsystem
    '''

    file_path = dirname(abspath(__file__))

    # Load plugins
    Manager(join(file_path, '../..', 'plugins'))

    # Set database and drive
    db_file = connect(join(file_path, '..', 'db.sqlite'))
    drive = join(file_path, '../..', 'disk_part.img')

    # Start filesystem
    fs = Filesystem(db_file, drive)
    path = '/'
    mount(fs, path, True)


if __name__ == '__main__':
    main()
