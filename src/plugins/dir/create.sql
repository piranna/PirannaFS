CREATE TABLE IF NOT EXISTS links
(
    id          INTEGER   PRIMARY KEY,

    child_entry INTEGER   NOT NULL,
    parent_dir  INTEGER   NOT NULL,
    name        TEXT      NOT NULL,
    creation    timestamp DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(child_entry) REFERENCES dir_entries(inode)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(parent_dir) REFERENCES dir_entries(inode)
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
    DELETE FROM dir_entries
    WHERE dir_entries.inode = OLD.child_entry;
END;

--

CREATE TRIGGER IF NOT EXISTS after_insert_on_links
-- Update the parent dir modification timestamp when a new direntry is inserted
    AFTER INSERT ON links
BEGIN
    UPDATE dir_entries
    SET modification = CURRENT_TIMESTAMP
    WHERE dir_entries.inode = NEW.parent_dir;
END;

CREATE TRIGGER IF NOT EXISTS after_update_on_links
-- Update the parent dir modification timestamp when a new direntry is updated
    AFTER UPDATE ON links
BEGIN
    UPDATE dir_entries
    SET modification = CURRENT_TIMESTAMP
    WHERE dir_entries.inode IN(OLD.parent_dir,NEW.parent_dir);
END;

CREATE TRIGGER IF NOT EXISTS after_delete_on_links
-- Update the parent dir modification timestamp when a new direntry is deleted
    AFTER DELETE ON links
BEGIN
    UPDATE dir_entries
    SET modification = CURRENT_TIMESTAMP
    WHERE dir_entries.inode = OLD.parent_dir;
END;


-- If links table is empty (table has just been created)
-- create initial row defining the root directory
INSERT INTO dir_entries(inode,type)
                 SELECT 0,   :type
                 WHERE NOT EXISTS(SELECT * FROM links LIMIT 1);

INSERT INTO links(id, child_entry, parent_dir, name)
           SELECT 0,  0,           0,          ''
           WHERE NOT EXISTS(SELECT * FROM links LIMIT 1);