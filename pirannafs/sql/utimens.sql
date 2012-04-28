UPDATE inodes
SET access = :access, modification = :modification
WHERE id = :inode
