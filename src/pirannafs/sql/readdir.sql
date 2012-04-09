SELECT name
FROM links
WHERE parent_dir = :parent_dir
LIMIT :limit