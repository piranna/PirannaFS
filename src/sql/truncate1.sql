-- Split the chunks in the database in two (old-head and new-tail)
-- based on it's defined length

-- Create new chunks containing the tail sectors and
-- update the old chunks length to contain only the head sectors

INSERT INTO chunks(file, block, length,           sector)
            SELECT NULL, 0,     length-:length-1, sector+:length+1
            FROM chunks
            WHERE file IS :file
              AND block = :block ;

UPDATE chunks SET length = :length
WHERE file IS :file
  AND block = :block;