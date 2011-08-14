-- Get the smaller free space chunk that's equal or bigger than the required
-- number of sectors or if there's no one available get the bigger one that's
-- smaller than the required number of sectors

SELECT * FROM chunks
WHERE file IS NULL
--  AND block NOT IN (:blocks)
    AND length <= COALESCE
                  (
                      (
                          SELECT length FROM chunks
                          WHERE file IS NULL
--                            AND block NOT IN (:blocks)
                              AND length >= :sectors_required
                          ORDER BY length
                          LIMIT 1
                      ),
                      :sectors_required
                  )
ORDER BY length DESC
LIMIT 1