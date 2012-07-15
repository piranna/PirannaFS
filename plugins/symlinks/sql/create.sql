-- Create the symlinks table in the database

CREATE TABLE IF NOT EXISTS symlinks
(
    inode  INTEGER PRIMARY KEY,

    target TEXT    NOT NULL,

    FOREIGN KEY(inode) REFERENCES inodes(inode)
        ON DELETE CASCADE ON UPDATE CASCADE
)