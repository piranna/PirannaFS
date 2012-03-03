UPDATE chunks
SET file = NULL, block = 0
WHERE file = :file