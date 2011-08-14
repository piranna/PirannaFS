-- type: getter
-- return: type

-- Get the mode of a file from a given file inode

SELECT type
FROM dir_entries
WHERE inode == :inode
LIMIT 1