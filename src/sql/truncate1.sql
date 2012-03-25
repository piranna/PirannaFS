-- Create new free chunks containing the tail sectors and
-- update the old chunks length to contain only the head sectors


INSERT INTO chunks(inode, block, length,                 sector)
            SELECT NULL,  0,     length-(:ceil-block)-1, sector+(:ceil-block)+1
            FROM chunks
            WHERE inode IS :inode
              AND block = length > :ceil-block ;

UPDATE chunks         SET length = :ceil-block
WHERE inode IS :inode AND length > :ceil-block ;

-- Set new file size
INCLUDE "_Set_Size.sql"