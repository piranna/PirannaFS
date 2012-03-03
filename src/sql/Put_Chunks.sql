UPDATE chunks
SET inode = :inode, block = :block
WHERE sector=:sector
-- WHERE drive=:drive AND sector=:sector
