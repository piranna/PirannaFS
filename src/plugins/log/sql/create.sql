CREATE TABLE IF NOT EXISTS log
(
    'who'   TEXT      NULL,                      --User
    'what'  TEXT      NOT NULL,                  --Action / Caller.Action?
    'where' TEXT      NOT NULL,                  --Caller / GPS?    # http://live.gnome.org/action/show/GnomeActivityJournal
    'when'  timestamp DEFAULT CURRENT_TIMESTAMP, --Timestamp
    'why'   TEXT      NULL,
    'how'   TEXT      NOT NULL,                  --Parameters
    'whom'  INTEGER   NULL,                      --Inode
    'for'   TEXT      NULL--,

--    FOREIGN KEY('whom') REFERENCES dir_entries(inode)
--        ON UPDATE CASCADE
)