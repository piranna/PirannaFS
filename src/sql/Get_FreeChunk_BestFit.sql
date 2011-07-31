-- 

SELECT * FROM chunks
WHERE file IS NULL
--  AND block NOT IN (:blocks)
    AND length <= COALESCE
                  (
                      SELECT length FROM chunks
                      WHERE file IS NULL
--                        AND block NOT IN (:blocks)
                          AND length >= :sectors_required
                      ORDER BY length
                      LIMIT 1,
                      :sectors_required
                  )
ORDER BY length DESC
LIMIT 1