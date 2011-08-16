SELECT SUM(length+1) AS size
FROM chunks
WHERE file IS NULL

-- Maybe this is a bug and should not be here...
LIMIT 1