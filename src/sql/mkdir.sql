-- Make a new directory

INSERT INTO dir_entries(type)
               VALUES(%(type)s);
--INCLUDE "Direntry.make.sql"

INSERT INTO directories(inode)
                 VALUES(last_insert_rowid())