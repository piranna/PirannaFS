SELECT * FROM chunks
WHERE inode = :inode AND block BETWEEN :floor AND :ceil-length
GROUP BY inode,block
ORDER BY block
