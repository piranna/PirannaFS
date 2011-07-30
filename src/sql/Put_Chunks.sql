UPDATE chunks
            SET file  = :file,
                block = :block
            WHERE sector=:sector
--            WHERE drive=:drive AND sector=:sector