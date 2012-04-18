-- Free all the chunks from a file

UPDATE chunks
SET inode = NULL, block = 0
WHERE inode = :inode ;

-- Set new file size
INCLUDE "_Set_Size.sql"