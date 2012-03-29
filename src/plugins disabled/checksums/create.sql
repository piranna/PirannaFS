CREATE TABLE IF NOT EXISTS checksums
(
    chunk    INTEGER PRIMARY KEY,

    checksum INTEGER NOT NULL,

    FOREIGN KEY(chunk) REFERENCES chunks(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Triggers

CREATE TRIGGER IF NOT EXISTS remove_if_chunk_have_been_freed
AFTER UPDATE ON chunks
WHEN NEW.file IS NULL
BEGIN
    DELETE FROM checksums
    WHERE checksums.chunk = OLD.id;
END;