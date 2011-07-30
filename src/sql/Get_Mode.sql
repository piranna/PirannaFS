SELECT type
            FROM dir_entries
            WHERE inode == ?
            LIMIT 1