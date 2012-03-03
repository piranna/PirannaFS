-- Free all the chunks from a file

UPDATE chunks
SET file = NULL, block = 0
WHERE file = :file