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