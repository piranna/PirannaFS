-- Create dir entries table (basic filesystem structure)

CREATE TABLE IF NOT EXISTS inodes
(
    id           INTEGER   PRIMARY KEY,

    type         INTEGER   NOT NULL,
    access       timestamp DEFAULT CURRENT_TIMESTAMP,
    modification timestamp DEFAULT CURRENT_TIMESTAMP
)