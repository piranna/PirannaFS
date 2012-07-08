'''
Created on 29/03/2012

@author: piranna
'''

from os.path import abspath, dirname, join
from sqlite3 import connect

from plugins import Load_Dir
import testfs

from pirannafs.backends.fuse import FS


def main():
    file_path = dirname(abspath(__file__))

    # Load plugins
    Load_Dir(join(file_path, '../..', 'plugins'))

    # Set database and drive
    db_file = connect(join(file_path, '..', 'db.sqlite'))
    drive = join(file_path, '../..', 'disk_part.img')

    # Start filesystem
    fs = FS(db_file, drive)

    fs.parser.fetch_mp = False
    fs.parse(values=fs, errex=1)

    fs.multithreaded = False
    fs.fuse_args.mountpoint = '../test/mountpoint'
    fs.main()


if __name__ == '__main__':
    main()
