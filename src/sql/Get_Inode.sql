SELECT child_entry AS inode
FROM links
WHERE parent_dir IS :parent_dir AND name == :name
LIMIT 1