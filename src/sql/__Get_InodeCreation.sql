SELECT
    child_entry                              AS inode,
    CAST(STRFTIME('%s',creation) AS INTEGER) AS creation
FROM links
WHERE parent_dir == ?
    AND name == ?
LIMIT 1