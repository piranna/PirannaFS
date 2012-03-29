-- type: getter
-- return: size

-- Get the size of a file from a given file inode

SELECT size
FROM files
WHERE inode == :inode
LIMIT 1