SELECT child_entry AS inode
FROM links
WHERE parent_dir == :parent_dir AND name == :name
LIMIT 1