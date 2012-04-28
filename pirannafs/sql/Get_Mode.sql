-- type: getter
-- return: type

-- Get the mode of a file from a given file inode

SELECT type
FROM inodes
WHERE id == :inode
LIMIT 1
