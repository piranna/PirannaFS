-- type: script

INSERT INTO chunks(file, block,              length,              sector)
SELECT             file, block+%(length)s+1, length-%(length)s-1, sector+%(length)s+1
    FROM chunks
    WHERE file IS %(file)s
      AND block = %(block)s;

UPDATE chunks SET length  = %(length)s
WHERE file IS %(file)s
  AND block = %(block)s;