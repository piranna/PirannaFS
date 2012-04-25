SELECT
    0 AS st_dev,
    0 AS st_uid,
    0 AS st_gid,

    inodes.type         AS st_mode,
    inodes.inode        AS st_ino,
    COUNT(links.child_entry) AS st_nlink,

    links.creation           AS st_ctime,
    inodes.access       AS st_atime,
    inodes.modification AS st_mtime,
--    links.creation                                      AS st_ctime,
--    CAST(STRFTIME('%s',inodes.access)       AS INTEGER) AS st_atime,
--    CAST(STRFTIME('%s',inodes.modification) AS INTEGER) AS st_mtime,

    COALESCE(files.size,0) AS st_size, -- Python-FUSE
    COALESCE(files.size,0) AS size     -- PyFilesystem

FROM inodes
    LEFT JOIN files
        ON inodes.inode == files.inode
    LEFT JOIN links
        ON inodes.inode == links.child_entry

WHERE parent_dir == :parent_dir AND name == :name

GROUP BY inodes.inode
LIMIT 1