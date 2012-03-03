-- Split the chunks in the database in two (old-head and new-tail)
-- based on it's defined length

-- Create new chunks containing the tail sectors and
-- update the old chunks length to contain only the head sectors

INSERT INTO chunks(inode, block,           length,           sector)
            SELECT inode, block+:length+1, length-:length-1, sector+:length+1
            FROM chunks
            WHERE inode IS :inode
              AND block = :block ;

UPDATE chunks SET length = :length
WHERE inode IS :inode
  AND block = :block;