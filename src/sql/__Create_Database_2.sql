INSERT INTO dir_entries(inode, type)
                 VALUES(0,     %(type)s);

INSERT INTO directories(inode)
                 VALUES(0);

INSERT INTO links(id, child_entry, parent_dir, name)
           VALUES(0,  0,           0,          '');