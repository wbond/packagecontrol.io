UPDATE packages SET st_versions = ARRAY[2, 3, 4]::int[] WHERE st_versions = ARRAY[2, 3]::int[];
UPDATE packages SET st_versions = ARRAY[3, 4]::int[] WHERE st_versions = ARRAY[3]::int[];

CREATE FUNCTION array_unique(arr anyarray) RETURNS anyarray LANGUAGE sql AS $$
    SELECT array_agg(DISTINCT a)
    FROM (
        SELECT unnest(arr) a 
        ORDER BY a
    ) sq
$$;
