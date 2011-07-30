SELECT file, block, ?-block AS length
            FROM chunks
            WHERE file IS ?
              AND block+length > ?