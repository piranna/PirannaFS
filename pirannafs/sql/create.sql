-- Create dir entries table (basic filesystem structure)

CREATE TABLE IF NOT EXISTS inodes
(
    id           INTEGER   PRIMARY KEY,

    type         INTEGER   NOT NULL,
    access       timestamp DEFAULT CURRENT_TIMESTAMP,
    modification timestamp DEFAULT CURRENT_TIMESTAMP
);




CREATE TABLE IF NOT EXISTS links
(
    id          INTEGER   PRIMARY KEY,

    child_entry INTEGER   NOT NULL,
    parent_dir  INTEGER   NOT NULL,
    name        TEXT      NOT NULL,
    creation    timestamp DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(child_entry) REFERENCES inodes(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(parent_dir) REFERENCES inodes(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    UNIQUE(parent_dir,name)
);


-- Triggers

CREATE TRIGGER IF NOT EXISTS remove_if_it_was_the_last_file_link
-- Delete the direntry when is removed it's last static link
    AFTER DELETE ON links
    WHEN NOT EXISTS
    (
        SELECT * FROM links
        WHERE child_entry = OLD.child_entry
        LIMIT 1
    )
BEGIN
    DELETE FROM inodes
    WHERE inodes.id = OLD.child_entry;
END;

--

CREATE TRIGGER IF NOT EXISTS after_insert_on_links
-- Update the parent dir modification timestamp when a new direntry is inserted
    AFTER INSERT ON links
BEGIN
    UPDATE inodes
    SET modification = CURRENT_TIMESTAMP
    WHERE inodes.id = NEW.parent_dir;
END;

CREATE TRIGGER IF NOT EXISTS after_update_on_links
-- Update the parent dir modification timestamp when a new direntry is updated
    AFTER UPDATE ON links
BEGIN
    UPDATE inodes
    SET modification = CURRENT_TIMESTAMP
    WHERE inodes.id IN(OLD.parent_dir,NEW.parent_dir);
END;

CREATE TRIGGER IF NOT EXISTS after_delete_on_links
-- Update the parent dir modification timestamp when a new direntry is deleted
    AFTER DELETE ON links
BEGIN
    UPDATE inodes
    SET modification = CURRENT_TIMESTAMP
    WHERE inodes.id = OLD.parent_dir;
END;


-- If links table is empty (table has just been created)
-- create initial row defining the root directory
INSERT INTO inodes(id, type)
            SELECT 0, :type
            WHERE NOT EXISTS(SELECT * FROM links LIMIT 1);

INSERT INTO links(id, child_entry, parent_dir, name)
           SELECT 0,  0,           0,          ''
           WHERE NOT EXISTS(SELECT * FROM links LIMIT 1);

           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
           
CREATE TABLE IF NOT EXISTS files
(
    inode INTEGER PRIMARY KEY,

    size  INTEGER DEFAULT 0,

    FOREIGN KEY(inode) REFERENCES inodes(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS chunks
(
    id     INTEGER PRIMARY KEY,

    inode  INTEGER     NULL,    -- NULL inode means free chunk
    block  INTEGER NOT NULL,
    length INTEGER NOT NULL,
    sector INTEGER NOT NULL,

    FOREIGN KEY(inode) REFERENCES files(inode)
        ON DELETE SET NULL ON UPDATE CASCADE,

    UNIQUE(inode,block),
    UNIQUE(inode,sector)
);


-- If chunks table is empty (table has just been created)
-- create initial row defining all the partition as free

INSERT INTO chunks(inode, block, length, sector)
            SELECT NULL,  0,    :length,:sector
            WHERE NOT EXISTS(SELECT * FROM chunks LIMIT 1);
