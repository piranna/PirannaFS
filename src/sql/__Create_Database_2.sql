-- If directories table is empty (table has just been created)
-- create initial row defining the root directory

INSERT INTO dir_entries(inode, type)
                 VALUES(0,     %(type)s);

INSERT INTO directories(inode)
                 VALUES(0);

INSERT INTO links(id, child_entry, parent_dir, name)
           VALUES(0,  0,           0,          '');


--INSERT INTO dir_entries(inode, type)
--                 SELECT 0,   %(type)s
--                 WHERE NOT EXISTS(SELECT * FROM dir_entries LIMIT 1);
--
--INSERT INTO directories(inode)
--                 SELECT 0
--                 WHERE NOT EXISTS(SELECT * FROM dir_entries LIMIT 1);
--
--INSERT INTO links(id, child_entry, parent_dir, name)
--           SELECT 0,  0,           0,          ''
--           WHERE NOT EXISTS(SELECT * FROM dir_entries LIMIT 1);