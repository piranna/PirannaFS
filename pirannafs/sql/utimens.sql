UPDATE dir_entries
SET access = :access, modification = :modification
WHERE inode = :inode