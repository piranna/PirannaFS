SELECT * FROM chunks
            WHERE file = ?
              AND block BETWEEN ? AND ?-length
            GROUP BY file,block
            ORDER BY block