-- Make a new file

INSERT INTO dir_entries(type)
                VALUES(:type);
-- INCLUDE "Direntry.make.sql"

INSERT INTO files(inode)
           VALUES(last_insert_rowid())