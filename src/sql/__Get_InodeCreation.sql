SELECT child_entry AS inode, creation
FROM links
WHERE parent_dir == :parent_dir AND name == :name
LIMIT 1