-- type: script
-- return: integer

-- INCLUDE "Direntry.make.sql"

INSERT INTO files(inode)
           VALUES(last_insert_rowid())