SELECT SUM(length+1) AS size
            FROM chunks
            WHERE file IS NULL