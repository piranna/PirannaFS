UPDATE links
SET   parent_dir = :parent_new,    name = :name_new
WHERE parent_dir = :parent_old AND name = :name_old