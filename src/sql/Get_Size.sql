SELECT size
            FROM files
            WHERE inode == ?
            LIMIT 1