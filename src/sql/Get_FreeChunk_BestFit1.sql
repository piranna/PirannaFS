-- Get the smaller free space chunk that's equal or bigger than the required
-- number of sectors or if there's no one available get the bigger one that's
-- smaller than the required number of sectors

-- Smaller chunk equal or bigger than required space
SELECT NULL AS id, inode, :block AS block, length, sector FROM chunks
WHERE inode IS NULL
  AND length >= :sectors_required
ORDER BY length
LIMIT 1