UPDATE files
SET size = :size
WHERE inode = :inode
  AND size < :size