SELECT * FROM chunks
WHERE file = :file AND block BETWEEN :floor AND :ceil-length
GROUP BY file,block
ORDER BY block