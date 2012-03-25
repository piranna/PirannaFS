-- Make a new file


INCLUDE "_Make_DirEntry.sql"

INSERT INTO files(inode)
           VALUES(last_insert_rowid())
