SELECT file, block, :ceil-block AS length
FROM chunks
WHERE file IS :file AND block+length > :ceil