SELECT size
FROM files
WHERE inode == :inode
LIMIT 1