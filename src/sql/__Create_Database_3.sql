-- If chunks table is empty (table has just been created)
-- create initial row defining all the partition as free

--INSERT INTO chunks(file, block, length, sector)
--            VALUES(NULL, 0, :length, :sector);

INSERT INTO chunks(file, block, length, sector)
            SELECT NULL, 0, :length, :sector
            WHERE NOT EXISTS(SELECT * FROM chunks LIMIT 1);