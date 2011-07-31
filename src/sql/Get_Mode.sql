SELECT type
FROM dir_entries
WHERE inode == :inode
LIMIT 1