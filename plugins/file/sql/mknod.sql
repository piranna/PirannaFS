-- Make a new file


INCLUDE "_Make_Inode.sql";

INSERT INTO files(inode)
           VALUES(last_insert_rowid())
