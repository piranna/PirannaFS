CREATE TABLE IF NOT EXISTS files
(
    inode INTEGER PRIMARY KEY,

    size  INTEGER DEFAULT 0,

    FOREIGN KEY(inode) REFERENCES dir_entries(inode)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS chunks
(
    id     INTEGER PRIMARY KEY,

    file   INTEGER     NULL,    -- NULL file means free chunk
    block  INTEGER NOT NULL,
    length INTEGER NOT NULL,
    sector INTEGER NOT NULL,

    FOREIGN KEY(file) REFERENCES files(inode)
        ON DELETE SET NULL ON UPDATE CASCADE,

    UNIQUE(file,block),
    UNIQUE(file,sector)
);


-- If chunks table is empty (table has just been created)
-- create initial row defining all the partition as free

INSERT INTO chunks(file, block, length, sector)
            SELECT NULL, 0,    :length,:sector
            WHERE NOT EXISTS(SELECT * FROM chunks LIMIT 1);